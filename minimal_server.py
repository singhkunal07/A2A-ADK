#!/usr/bin/env python3
"""
Minimal server for testing A2A communication
"""

import logging
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill, AgentProvider

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MinimalAgentExecutor:
    """Absolute minimal agent executor."""
    
    async def execute(self, context, event_queue):
        """Execute with immediate response."""
        from a2a.utils import new_agent_text_message
        
        try:
            user_input = context.get_user_input()
            logger.info(f"🚀 MINIMAL: Processing: '{user_input}'")
            
            response = f"✅ Received: {user_input}"
            logger.info(f"🚀 MINIMAL: Responding with: {response}")
            
            event_queue.enqueue_event(new_agent_text_message(response))
            logger.info("🚀 MINIMAL: Response sent successfully")
            
        except Exception as e:
            logger.error(f"🚀 MINIMAL: Error: {e}")
            import traceback
            traceback.print_exc()
    
    async def cancel(self, context, event_queue):
        """Handle cancellation."""
        pass

def create_minimal_agent_card():
    """Create minimal agent card."""
    return AgentCard(
        name='Minimal Test Agent',
        description='Minimal agent for testing communication',
        url='http://localhost:10001/',
        provider=AgentProvider(organization="Test", url="http://localhost"),
        version='1.0.0',
        capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        skills=[AgentSkill(
            id='minimal_test',
            name='Minimal Test',
            description='Minimal test skill',
            tags=['test'],
            examples=['hello'],
            inputModes=['text'],
            outputModes=['text']
        )]
    )

def main():
    """Start minimal server."""
    try:
        logger.info("🚀 Starting minimal test server...")
        
        # Create components
        agent_card = create_minimal_agent_card()
        task_store = InMemoryTaskStore()
        agent_executor = MinimalAgentExecutor()
        
        # Create request handler
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=task_store
        )
        
        # Create server
        server_app = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler
        )
        
        logger.info("🚀 Starting server on localhost:10001")
        
        # Start with very verbose logging
        uvicorn.run(
            server_app.build(),
            host="localhost",
            port=10001,
            log_level="debug",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Server failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()