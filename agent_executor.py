#!/usr/bin/env python3
"""
Create Plan Agent - Uses LLM to create intelligent, customized plans
"""

import json  # Add this import
import logging
import os
from typing import Optional, Dict, Any
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from agents.base_agent_executor import BaseOpenAIAgentExecutor
from uuid import uuid4

logger = logging.getLogger(__name__)

class CreatePlanAgentExecutor(BaseOpenAIAgentExecutor):
    """Create Plan Agent powered by OpenAI GPT-4."""
    
    def __init__(self):
        system_prompt = """You are an AI assistant that creates detailed, actionable plans based on user requests.
Your task is to:
1. Analyze the complete context provided
2. Create a comprehensive, step-by-step plan
3. Include timelines, resources needed, and potential challenges
4. Determine if the plan needs execution assistance

Respond in JSON format:
{
    "plan": {
        "overview": "brief summary of the plan",
        "steps": [
            {
                "step": "step description",
                "timeline": "estimated time",
                "resources": ["required", "resources"],
                "notes": "additional information"
            }
        ],
        "estimated_duration": "total time estimate",
        "estimated_cost": "cost estimate if applicable",
        "needs_execution": boolean,
        "execution_tasks": ["list", "of", "tasks", "if", "needs_execution"]
    }
}"""

        super().__init__(system_prompt)
        self.task_executor_url = "http://localhost:10003"
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the Create Plan agent's logic."""
        try:
            # Get user message
            user_message = context.get_user_input()
            
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Get plan from OpenAI - NO AWAIT HERE!
            response = self.get_llm_response(messages)
            plan_data = json.loads(response)
            
            # Format plan for user
            plan_text = f"""📋 **Plan Overview**
{plan_data['plan']['overview']}

⏱️ **Estimated Duration**: {plan_data['plan']['estimated_duration']}
💰 **Estimated Cost**: {plan_data['plan']['estimated_cost']}

📝 **Step-by-Step Plan**:
"""
            
            for i, step in enumerate(plan_data['plan']['steps'], 1):
                plan_text += f"""
{i}. {step['step']}
   ⏰ Timeline: {step['timeline']}
   🔧 Resources: {', '.join(step['resources'])}
   📌 Note: {step['notes']}
"""
            
            await event_queue.enqueue_event(new_agent_text_message(plan_text))
            
            if plan_data['plan']['needs_execution']:
                # Forward to Task Executor
                await event_queue.enqueue_event(new_agent_text_message(
                    "🔄 This plan requires execution assistance. Forwarding to Task Executor..."
                ))
                
                execution_context = {
                    "plan": plan_data['plan'],
                    "tasks": plan_data['plan']['execution_tasks']
                }
                
                executor_response = await self.call_agent(
                    self.task_executor_url,
                    json.dumps(execution_context)
                )
                
                if "result" in executor_response:
                    result = executor_response["result"]
                    if isinstance(result, dict) and "message" in result:
                        msg = result["message"]
                        if isinstance(msg, dict) and "parts" in msg:
                            text_parts = [part["text"] for part in msg["parts"] if "text" in part]
                            response_text = " ".join(text_parts)
                            await event_queue.enqueue_event(new_agent_text_message(response_text))
            else:
                await event_queue.enqueue_event(new_agent_text_message(
                    "✅ Plan is ready for your review. No automated execution is needed for this plan."
                ))
                
        except Exception as e:
            error_msg = f"Error creating plan: {str(e)}"
            logger.error(error_msg)
            await event_queue.enqueue_event(new_agent_text_message(error_msg))