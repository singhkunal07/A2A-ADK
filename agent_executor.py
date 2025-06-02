#!/usr/bin/env python3
"""
Get Info Agent - Fixed version with proper task handling
"""

import logging
import os
import json
from typing import Optional, Dict, Any
from uuid import uuid4
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message, new_task
from a2a.types import (
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    Message,
    TextPart,
    Part
)

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GetInfoAgentExecutor(AgentExecutor):
    """Get Info Agent with proper A2A task handling."""
    
    def __init__(self):
        # Initialize OpenAI client
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Use SYNCHRONOUS OpenAI client
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("✅ GET_INFO: OpenAI sync client initialized")
        except ImportError:
            raise ValueError("openai package not installed. Install with: pip install openai")
        
        self.system_prompt = """You are an AI assistant that analyzes user requests to determine what clarifying questions to ask.

Your ONLY job is to:
1. Analyze the user's request to understand what they want
2. Identify what essential information is missing
3. Generate 3-5 specific, helpful questions to gather that missing information
4. Return the questions in a friendly, conversational format

IMPORTANT: You should NEVER attempt to fulfill the request yourself. Your role is ONLY to ask clarifying questions.

Examples:
User: "I want to plan a trip" 
→ Ask about: destination, dates, budget, number of travelers, interests

User: "Help me organize an event"
→ Ask about: event type, number of attendees, date/time, venue, budget

User: "I need to create a presentation" 
→ Ask about: topic, audience, duration, deadline, key messages

Always respond in a friendly, helpful tone and explain why you need the information."""
        
        self.model = "gpt-4"
        logger.info(f"✅ GET_INFO: Initialized with model: {self.model}")
    
    def get_llm_response(self, messages: list) -> str:
        """Get response from OpenAI API using SYNCHRONOUS call."""
        try:
            logger.info("🧠 GET_INFO: Calling OpenAI API...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                timeout=30.0
            )
            
            llm_response = response.choices[0].message.content
            logger.info("✅ GET_INFO: OpenAI API call successful")
            return llm_response
            
        except Exception as e:
            logger.error(f"❌ GET_INFO: OpenAI API error: {e}")
            raise
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute with proper A2A task and response handling."""
        try:
            logger.info("=" * 60)
            logger.info("🚀 GET_INFO: Starting execution")
            logger.info(f"🚀 GET_INFO: Task ID: {context.task_id}")
            logger.info(f"🚀 GET_INFO: Context ID: {context.context_id}")
            
            # Get or create the task
            current_task = context.current_task
            if not current_task:
                # Create a new task if one doesn't exist
                if context.message:
                    current_task = new_task(context.message)
                    context.current_task = current_task
                    event_queue.enqueue_event(current_task)
                    logger.info(f"📋 GET_INFO: Created new task: {current_task.id}")
                else:
                    logger.error("❌ GET_INFO: No message or task in context")
                    return
            
            # Update task status to working
            status_update = TaskStatusUpdateEvent(
                taskId=current_task.id,
                contextId=current_task.contextId,
                kind="status-update",
                status=TaskStatus(state=TaskState.working, timestamp=None),
                final=False,
                metadata={}
            )
            event_queue.enqueue_event(status_update)
            logger.info("📊 GET_INFO: Updated task status to 'working'")
            
            # Get user input
            user_input = context.get_user_input()
            logger.info(f"📥 GET_INFO: Received user input: '{user_input}'")
            
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"The user said: '{user_input}'\n\nWhat clarifying questions should I ask to better understand their needs? Respond with a helpful message that asks 3-5 specific questions."}
            ]
            
            # Get questions from OpenAI
            logger.info("📡 GET_INFO: Requesting clarifying questions from OpenAI...")
            response = self.get_llm_response(messages)
            
            # Format response
            formatted_response = f"""🤔 **Let me gather some details to help you better!**

{response}

Please share any of these details that are relevant to your request, and I'll make sure you get the best possible assistance!"""
            
            logger.info("📤 GET_INFO: Formatted response for user")
            
            # Create the response message
            response_message = Message(
                messageId=str(uuid4()),
                role="agent",
                parts=[Part(root=TextPart(
                    kind="text",
                    text=formatted_response,
                    metadata={}
                ))],
                kind="message",
                contextId=current_task.contextId,
                taskId=current_task.id,
                metadata={}
            )
            
            # Enqueue the response message
            event_queue.enqueue_event(response_message)
            logger.info("📡 GET_INFO: Enqueued response message")
            
            # Update task status to completed with the message
            final_status = TaskStatusUpdateEvent(
                taskId=current_task.id,
                contextId=current_task.contextId,
                kind="status-update",
                status=TaskStatus(
                    state=TaskState.completed,
                    message=response_message,
                    timestamp=None
                ),
                final=True,
                metadata={}
            )
            event_queue.enqueue_event(final_status)
            logger.info("📊 GET_INFO: Updated task status to 'completed'")
            
            logger.info("✅ GET_INFO: Execution completed successfully")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ GET_INFO: Error in execution: {e}")
            logger.error(f"❌ GET_INFO: Error type: {type(e)}")
            import traceback
            logger.error(f"❌ GET_INFO: Full traceback: {traceback.format_exc()}")
            
            # Handle error with proper task status
            if current_task:
                error_message = Message(
                    messageId=str(uuid4()),
                    role="agent",
                    parts=[Part(root=TextPart(
                        kind="text",
                        text=f"I encountered an error while processing your request. Please try again.",
                        metadata={}
                    ))],
                    kind="message",
                    contextId=current_task.contextId,
                    taskId=current_task.id,
                    metadata={}
                )
                event_queue.enqueue_event(error_message)
                
                error_status = TaskStatusUpdateEvent(
                    taskId=current_task.id,
                    contextId=current_task.contextId,
                    kind="status-update",
                    status=TaskStatus(
                        state=TaskState.failed,
                        message=error_message,
                        timestamp=None
                    ),
                    final=True,
                    metadata={}
                )
                event_queue.enqueue_event(error_status)
            
            logger.info("=" * 60)
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle task cancellation."""
        logger.info("🛑 GET_INFO: Task cancellation requested")
        logger.info(f"🛑 GET_INFO: Task ID: {context.task_id}")
        
        if context.current_task:
            cancel_message = Message(
                messageId=str(uuid4()),
                role="agent",
                parts=[Part(root=TextPart(
                    kind="text",
                    text="No problem! Feel free to ask if you need help clarifying any other requests.",
                    metadata={}
                ))],
                kind="message",
                contextId=context.current_task.contextId,
                taskId=context.current_task.id,
                metadata={}
            )
            event_queue.enqueue_event(cancel_message)
            
            cancel_status = TaskStatusUpdateEvent(
                taskId=context.current_task.id,
                contextId=context.current_task.contextId,
                kind="status-update",
                status=TaskStatus(
                    state=TaskState.canceled,
                    timestamp=None
                ),
                final=True,
                metadata={}
            )
            event_queue.enqueue_event(cancel_status)