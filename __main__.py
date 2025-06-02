#!/usr/bin/env python3
"""
Get Info Agent Main Entry Point
Uses the proper A2A protocol with tasks/send and tasks/sendSubscribe
Designed to dynamically gather information for any type of request
"""

import logging
import os

import click
import uvicorn
from dotenv import load_dotenv

# Import from A2A SDK
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    AgentProvider,
)

# Import your agent executor - FIXED: Use absolute import
from agents.get_info.agent_executor import GetInfoAgentExecutor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_agent_card(host: str, port: int) -> AgentCard:
    """Create the Agent Card for the Get Info Agent."""
    
    # Define the main skill - keeping it generic and adaptable
    get_info_skill = AgentSkill(
        id='dynamic_information_gathering',
        name='Dynamic Information Gathering',
        description='Intelligently analyzes any request to identify missing information and asks relevant questions to gather complete context. Adapts questioning strategy based on the specific needs of each unique situation.',
        tags=['information', 'context', 'analysis', 'clarification', 'understanding'],
        examples=[
            'Tell me more about what you need',
            'I need to understand your request better',
            'Let me gather some details about that',
            'Could you provide more context?',
            'I need to ask some questions first',
            'Help me understand your requirements'
        ],
        inputModes=['text', 'text/plain'],
        outputModes=['text', 'text/plain']
    )
    
    # Define provider information
    provider = AgentProvider(
        organization="Decision Flow Systems",
        url="https://github.com/decision-flow-agent"
    )
    
    # Define capabilities
    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True
    )
    
    # Create the agent card with generic, adaptable description
    agent_card = AgentCard(
        name='Get Info Agent',
        description='An intelligent information gathering agent that dynamically adapts to any type of request. Specializes in understanding context, identifying information gaps, and asking targeted questions to gather all necessary details. Can handle any subject matter or type of inquiry.',
        url=f'http://{host}:{port}/',
        provider=provider,
        version='1.0.0',
        documentationUrl='https://github.com/decision-flow-agent/README.md',
        capabilities=capabilities,
        defaultInputModes=['text', 'text/plain'],
        defaultOutputModes=['text', 'text/plain'],
        skills=[get_info_skill]
    )
    
    return agent_card


@click.command()
@click.option(
    '--host', 
    default=os.getenv('AGENT_HOST', 'localhost'), 
    help='Host to bind the server'
)
@click.option(
    '--port', 
    default=int(os.getenv('GET_INFO_AGENT_PORT', '10001')), 
    type=int,
    help='Port to bind the server'
)
def main(host: str, port: int):
    """Start the Get Info Agent server."""
    
    try:
        # Validate environment setup
        if not os.getenv('OPENAI_API_KEY'):
            logger.error("❌ Missing required environment variable: OPENAI_API_KEY")
            exit(1)
        
        # Create agent card
        agent_card = create_agent_card(host, port)
        logger.info(f"✓ Created agent card for {agent_card.name}")
        
        # Create request handler with task store and agent executor
        task_store = InMemoryTaskStore()
        agent_executor = GetInfoAgentExecutor()
        
        # Use A2A's DefaultRequestHandler - this handles the proper A2A protocol
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=task_store
        )
        
        # Create A2A server application - this implements the proper A2A endpoints
        server_app = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler
        )
        
        # Get the FastAPI app - only build it once
        app = server_app.build()
        
        logger.info(f"🚀 Starting Get Info Agent server on {host}:{port}")
        logger.info(f"📋 Agent Card available at: http://{host}:{port}/.well-known/agent.json")
        logger.info("🔗 Using proper A2A protocol with message/send endpoints")
        logger.info("🎯 Ready to gather information for any type of request!")
        
        # Start the server with increased worker timeout
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            timeout_keep_alive=30,
            timeout_graceful_shutdown=10,
            loop="asyncio"
        )
        
    except Exception as e:  # ← THIS WAS MISSING!
        logger.error(f"❌ Failed to start Get Info Agent server: {e}")
        exit(1)


if __name__ == '__main__':  # ← THIS WAS ALSO MISSING!
    main()