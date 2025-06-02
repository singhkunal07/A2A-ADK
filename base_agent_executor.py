#!/usr/bin/env python3
"""
Base Agent Executor with SYNCHRONOUS OpenAI support for A2A compatibility
"""

from typing import Optional, Dict, Any
import os
import logging
from a2a.types import (
    Message,
    TextPart,
    Part,
    Task,
    TaskState
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
import httpx
from uuid import uuid4

logger = logging.getLogger(__name__)

class BaseOpenAIAgentExecutor(AgentExecutor):
    """Base class for OpenAI-powered agent executors with A2A support."""
    
    def __init__(self, system_prompt: str):
        """Initialize the agent with SYNCHRONOUS OpenAI client."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found - agents will use fallback responses")
            self.client = None
        else:
            try:
                # Use SYNCHRONOUS OpenAI client (not AsyncOpenAI)
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)  # ← Changed to sync client
                logger.info("✓ OpenAI sync client initialized")
            except ImportError:
                logger.warning("OpenAI package not installed - using fallback responses")
                self.client = None
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        
        self.system_prompt = system_prompt
        self.model = "gpt-4"
        
    def get_llm_response(self, messages: list) -> str:  # ← Removed async
        """Get response from OpenAI API using synchronous client."""
        if not self.client:
            return "I'm currently unable to access the language model. Using fallback response."
            
        try:
            response = self.client.chat.completions.create(  # ← Removed await
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                timeout=30.0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return "I encountered an error accessing the language model. Please try again."
            
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the agent's logic. To be implemented by subclasses."""
        raise NotImplementedError
        
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel the agent's execution."""
        logger.info(f"Cancelling execution for task {context.task_id}")
        cancel_message = new_agent_text_message("Task has been cancelled.")
        event_queue.enqueue_event(cancel_message)#!/usr/bin/env python3
"""
Base Agent Executor with SYNCHRONOUS OpenAI support for A2A compatibility
"""

from typing import Optional, Dict, Any
import os
import logging
from a2a.types import (
    Message,
    TextPart,
    Part,
    Task,
    TaskState
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
import httpx
from uuid import uuid4

logger = logging.getLogger(__name__)

class BaseOpenAIAgentExecutor(AgentExecutor):
    """Base class for OpenAI-powered agent executors with A2A support."""
    
    def __init__(self, system_prompt: str):
        """Initialize the agent with SYNCHRONOUS OpenAI client."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found - agents will use fallback responses")
            self.client = None
        else:
            try:
                # Use SYNCHRONOUS OpenAI client (not AsyncOpenAI)
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)  # ← Changed to sync client
                logger.info("✓ OpenAI sync client initialized")
            except ImportError:
                logger.warning("OpenAI package not installed - using fallback responses")
                self.client = None
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        
        self.system_prompt = system_prompt
        self.model = "gpt-4"
        
    def get_llm_response(self, messages: list) -> str:  # ← Removed async
        """Get response from OpenAI API using synchronous client."""
        if not self.client:
            return "I'm currently unable to access the language model. Using fallback response."
            
        try:
            response = self.client.chat.completions.create(  # ← Removed await
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                timeout=30.0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return "I encountered an error accessing the language model. Please try again."
            
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the agent's logic. To be implemented by subclasses."""
        raise NotImplementedError
        
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel the agent's execution."""
        logger.info(f"Cancelling execution for task {context.task_id}")
        cancel_message = new_agent_text_message("Task has been cancelled.")
        event_queue.enqueue_event(cancel_message)