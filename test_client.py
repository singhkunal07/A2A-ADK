#!/usr/bin/env python3
"""
Test client for Decision Flow Agent system using A2A protocol.
"""

import asyncio
import logging
from typing import Dict, Any
from uuid import uuid4

import click
import httpx
from dotenv import load_dotenv

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
    Message,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
    TextPart,
    Part,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DecisionFlowTestClient:
    """Test client for the Decision Flow Agent system."""
    
    def __init__(self, router_url: str = "http://localhost:10000"):
        self.router_url = router_url
        self.client = None
        self.agent_card = None
        
    async def initialize(self):
        """Initialize the A2A client."""
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            try:
                # Get agent card
                card_resolver = A2ACardResolver(http_client, self.router_url)
                self.agent_card = await card_resolver.get_agent_card()
                
                # Create A2A client
                self.client = A2AClient(http_client, agent_card=self.agent_card)
                
                logger.info(f"✅ Connected to {self.agent_card.name}")
                logger.info(f"📋 Description: {self.agent_card.description}")
                logger.info(f"🔧 Capabilities: Streaming={self.agent_card.capabilities.streaming}")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize client: {e}")
                return False
    
    async def send_message(self, message_text: str, use_streaming: bool = False) -> Dict[str, Any]:
        """Send a message to the router agent."""
        
        if not self.client:
            logger.error("Client not initialized")
            return {"error": "Client not initialized"}
        
        try:
            # Create message
            message = Message(
                role='user',
                parts=[Part(root=TextPart(text=message_text))],
                messageId=str(uuid4())
            )
            
            # Create request parameters
            params = MessageSendParams(
                id=str(uuid4()),
                message=message
            )
            
            if use_streaming and self.agent_card.capabilities.streaming:
                # Use streaming
                logger.info(f"📤 Sending (streaming): {message_text}")
                
                request = SendStreamingMessageRequest(params=params)
                response_stream = self.client.send_message_streaming(request)
                
                full_response = ""
                async for chunk in response_stream:
                    if hasattr(chunk.root, 'result') and chunk.root.result:
                        if hasattr(chunk.root.result, 'parts'):
                            for part in chunk.root.result.parts:
                                if hasattr(part.root, 'text'):
                                    chunk_text = part.root.text
                                    full_response += chunk_text
                                    logger.info(f"📥 Chunk: {chunk_text}")
                
                return {"response": full_response, "type": "streaming"}
                
            else:
                # Use regular send
                logger.info(f"📤 Sending: {message_text}")
                
                request = SendMessageRequest(params=params)
                response = await self.client.send_message(request)
                
                if hasattr(response.root, 'error') and response.root.error:
                    error_msg = response.root.error.message
                    logger.error(f"❌ Error: {error_msg}")
                    return {"error": error_msg}
                
                if hasattr(response.root, 'result') and response.root.result:
                    if hasattr(response.root.result, 'parts'):
                        response_text = ""
                        for part in response.root.result.parts:
                            if hasattr(part.root, 'text'):
                                response_text += part.root.text
                        
                        logger.info(f"📥 Response: {response_text}")
                        return {"response": response_text, "type": "direct"}
                
                return {"error": "No response received"}
                
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            return {"error": str(e)}
    
    async def run_test_scenarios(self):
        """Run predefined test scenarios to demonstrate the decision flow."""
        
        test_scenarios = [
            {
                "name": "Info Required Scenario",
                "message": "I want to plan my trip",
                "expected_route": "Get Info Agent",
                "description": "Should route to Get Info Agent to collect missing details"
            },
            {
                "name": "Planning Scenario", 
                "message": "Plan a trip to Paris from May 10 to May 15 with a $2000 budget",
                "expected_route": "Create Plan Agent",
                "description": "Should route to Create Plan Agent to generate comprehensive plan"
            },
            {
                "name": "Task Execution Scenario",
                "message": "Book a flight to New York for tomorrow at 9 AM", 
                "expected_route": "Task Executor Agent",
                "description": "Should route to Task Executor Agent to handle the booking"
            },
            {
                "name": "No Action Scenario",
                "message": "Hello",
                "expected_route": "No Action Agent", 
                "description": "Should route to No Action Agent for engagement"
            },
            {
                "name": "Calculation Task",
                "message": "Calculate the square root of 144",
                "expected_route": "Task Executor Agent",
                "description": "Should route to Task Executor Agent for calculation"
            },
            {
                "name": "Complex Planning",
                "message": "Create a weekly meal plan for a family of four with dietary restrictions",
                "expected_route": "Create Plan Agent",
                "description": "Should route to Create Plan Agent for detailed meal planning"
            }
        ]
        
        logger.info("🧪 Running Decision Flow Test Scenarios...")
        logger.info("=" * 60)
        
        for i, scenario in enumerate(test_scenarios, 1):
            logger.info(f"\n🧪 Test {i}: {scenario['name']}")
            logger.info(f"📝 Description: {scenario['description']}")  
            logger.info(f"🎯 Expected Route: {scenario['expected_route']}")
            logger.info(f"💬 Message: \"{scenario['message']}\"")
            logger.info("-" * 40)
            
            # Send message
            result = await self.send_message(scenario['message'])
            
            if "error" in result:
                logger.error(f"❌ Test failed: {result['error']}")
            else:
                response = result.get("response", "No response")
                logger.info(f"✅ Response received ({len(response)} chars)")
                
                # Show first 200 characters of response
                preview = response[:200] + "..." if len(response) > 200 else response  
                logger.info(f"📖 Preview: {preview}")
            
            logger.info("=" * 60)
            
            # Wait between tests
            await asyncio.sleep(1)
        
        logger.info("🏁 All test scenarios completed!")
    
    async def interactive_mode(self):
        """Run in interactive mode for manual testing."""
        logger.info("🎮 Starting Interactive Mode")
        logger.info("💡 Try these example messages:")
        logger.info("   • 'I want to plan my trip' (Info Required)")
        logger.info("   • 'Plan a trip to Paris May 10-15 with $2000 budget' (Planning)")
        logger.info("   • 'Book a flight to NYC tomorrow at 9 AM' (Task Execution)")
        logger.info("   • 'Hello' (No Action)")
        logger.info("   • Type 'quit' to exit")
        logger.info("-" * 50)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    logger.info("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Send message
                result = await self.send_message(user_input)
                
                if "error" in result:
                    logger.error(f"❌ Error: {result['error']}")
                else:
                    response = result.get("response", "No response")
                    print(f"🤖 Agent: {response}")
                    
            except KeyboardInterrupt:
                logger.info("\n👋 Goodbye!")
                break
            except EOFError:
                logger.info("\n👋 Goodbye!")
                break


@click.command()
@click.option('--router-url', default='http://localhost:10000', help='URL of the router agent')
@click.option('--test-scenarios', is_flag=True, help='Run predefined test scenarios')
@click.option('--interactive', is_flag=True, help='Run in interactive mode')
@click.option('--message', help='Send a single message and exit')
@click.option('--streaming', is_flag=True, help='Use streaming mode for responses')
def main(router_url: str, test_scenarios: bool, interactive: bool, message: str, streaming: bool):
    """Test client for Decision Flow Agent system."""
    
    async def run_client():
        client = DecisionFlowTestClient(router_url)
        
        # Initialize client
        if not await client.initialize():
            logger.error("❌ Failed to initialize client")
            return
        
        if message:
            # Send single message
            result = await client.send_message(message, use_streaming=streaming)
            if "error" in result:
                logger.error(f"❌ Error: {result['error']}")
            else:
                response = result.get("response", "No response")
                print(f"🤖 Response: {response}")
                
        elif test_scenarios:
            # Run test scenarios
            await client.run_test_scenarios()
            
        elif interactive:
            # Interactive mode
            await client.interactive_mode()
            
        else:
            # Default: show help and run a quick test
            logger.info("🤖 Decision Flow Agent Test Client")
            logger.info(f"🔗 Connected to: {router_url}")
            logger.info("📋 Use --help for options")
            
            # Quick test
            logger.info("\n🧪 Quick Test:")
            result = await client.send_message("Hello, how can you help me?")
            if "error" not in result:
                response = result.get("response", "No response")
                logger.info(f"✅ System is working! Response: {response[:100]}...")
            else:
                logger.error(f"❌ Quick test failed: {result['error']}")
    
    try:
        asyncio.run(run_client())
    except Exception as e:
        logger.error(f"❌ Client error: {e}")


if __name__ == '__main__':
    main()