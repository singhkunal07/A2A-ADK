#!/usr/bin/env python3
"""
Create Plan Agent Main Entry Point
Uses the proper A2A protocol with tasks/send and tasks/sendSubscribe
Designed to handle any type of planning scenario dynamically
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
from agents.create_plan.agent_executor import CreatePlanAgentExecutor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_agent_card(host: str, port: int) -> AgentCard:
    """Create the Agent Card for the Create Plan Agent."""
    
    # Define the main skill - keeping it generic and adaptable
    create_plan_skill = AgentSkill(
        id='dynamic_planning',
        name='Dynamic Planning',
        description='Creates detailed, actionable plans for any scenario by analyzing requirements, context, and objectives. Adapts to any type of planning need dynamically.',
        tags=['planning', 'strategy', 'organization', 'analysis', 'execution'],
        examples=[
            'Help me plan this task',
            'I need a plan for achieving my goal',
            'Create a strategy for my objective',
            'Help me organize this activity',
            'Make a plan for my idea',
            'How should I approach this?'
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
        name='Create Plan Agent',
        description='An intelligent planning agent that dynamically adapts to any scenario. Creates comprehensive, actionable plans by analyzing the specific context, requirements, and objectives of each unique situation. Can handle any type of planning need, from simple tasks to complex projects.',
        url=f'http://{host}:{port}/',
        provider=provider,
        version='1.0.0',
        documentationUrl='https://github.com/decision-flow-agent/README.md',
        capabilities=capabilities,
        defaultInputModes=['text', 'text/plain'],
        defaultOutputModes=['text', 'text/plain'],
        skills=[create_plan_skill]
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
    default=int(os.getenv('CREATE_PLAN_AGENT_PORT', '10002')), 
    type=int,
    help='Port to bind the server'
)
def main(host: str, port: int):
    """Start the Create Plan Agent server."""
    
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
        agent_executor = CreatePlanAgentExecutor()
        
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
        
        logger.info(f"🚀 Starting Create Plan Agent server on {host}:{port}")
        logger.info(f"📋 Agent Card available at: http://{host}:{port}/.well-known/agent.json")
        logger.info("🔗 Using proper A2A protocol with tasks/send and tasks/sendSubscribe endpoints")
        logger.info("🎯 Ready to create plans for any scenario!")
        
        # Start the server with the same app instance
        uvicorn.run(
            app,  # Use the same app instance
            host=host,
            port=port,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start Create Plan Agent server: {e}")
        exit(1)


if __name__ == '__main__':
    main()































# #!/usr/bin/env python3
# """
# Create Plan Agent Main Entry Point
# Specialized agent for generating comprehensive plans and strategies.
# """

# import logging
# import os

# import click
# import uvicorn
# from dotenv import load_dotenv

# from a2a.server.apps import A2AStarletteApplication
# from a2a.server.request_handlers import DefaultRequestHandler
# from a2a.server.tasks import InMemoryTaskStore
# from a2a.types import (
#     AgentCapabilities,
#     AgentCard,
#     AgentSkill,
#     AgentProvider,
# )

# from agent_executor import CreatePlanAgentExecutor

# # Load environment variables
# load_dotenv()

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# def create_agent_card(host: str, port: int) -> AgentCard:
#     """Create the Agent Card for the Create Plan Agent."""
    
#     # Define the main skill
#     create_plan_skill = AgentSkill(
#         id='comprehensive_planning',
#         name='Comprehensive Planning',
#         description='Specializes in creating detailed, structured plans and strategies for complex projects, events, trips, and other multi-step endeavors',
#         tags=['planning', 'strategy', 'organization', 'structure', 'timeline'],
#         examples=[
#             'Plan a trip to Paris from May 10 to May 15 with a $2000 budget',
#             'Create a weekly meal plan for a family of four with dietary restrictions',
#             'Organize a conference for 200 people with 5 speakers and 3 workshops',
#             'Develop a marketing strategy for a new product launch',
#             'Plan a wedding with 150 guests and a $15000 budget',
#             'Create a study plan for learning Python programming in 3 months'
#         ],
#         inputModes=['text', 'text/plain'],
#         outputModes=['text', 'text/plain', 'text/markdown']
#     )
    
#     # Define provider information
#     provider = AgentProvider(
#         organization="Decision Flow Systems",
#         url="https://github.com/decision-flow-agent"
#     )
    
#     # Define capabilities
#     capabilities = AgentCapabilities(
#         streaming=True,
#         pushNotifications=False,
#         stateTransitionHistory=True
#     )
    
#     # Create the agent card
#     agent_card = AgentCard(
#         name='Create Plan Agent',
#         description='Specialized agent that creates comprehensive, detailed plans and strategies. Excels at breaking down complex goals into actionable steps, creating timelines, organizing resources, and structuring approaches for maximum effectiveness.',
#         url=f'http://{host}:{port}/',
#         provider=provider,
#         version='1.0.0',
#         documentationUrl='https://github.com/decision-flow-agent/README.md',
#         capabilities=capabilities,
#         defaultInputModes=['text', 'text/plain'],
#         defaultOutputModes=['text', 'text/plain', 'text/markdown'],
#         skills=[create_plan_skill]
#     )
    
#     return agent_card


# @click.command()
# @click.option('--host', default=os.getenv('AGENT_HOST', 'localhost'), help='Host to bind the server')
# @click.option('--port', type=int, default=int(os.getenv('CREATE_PLAN_AGENT_PORT', '10002')), help='Port to bind the server')
# def main(host: str, port: int):
#     """Start the Create Plan Agent server."""
    
#     try:
#         # Create agent card
#         agent_card = create_agent_card(host, port)
#         logger.info(f"✓ Created agent card for {agent_card.name}")
        
#         # Create request handler with task store
#         task_store = InMemoryTaskStore()
#         agent_executor = CreatePlanAgentExecutor()
#         request_handler = DefaultRequestHandler(
#             agent_executor=agent_executor,
#             task_store=task_store
#         )
        
#         # Create A2A server application
#         server_app = A2AStarletteApplication(
#             agent_card=agent_card,
#             http_handler=request_handler
#         )
        
#         logger.info(f"🚀 Starting Create Plan Agent server on {host}:{port}")
#         logger.info(f"📋 Agent Card available at: http://{host}:{port}/.well-known/agent.json")
        
#         # Start the server
#         uvicorn.run(
#             server_app.build(),
#             host=host,
#             port=port,
#             log_level="info"
#         )
        
#     except Exception as e:
#         logger.error(f"❌ Failed to start Create Plan Agent server: {e}")
#         exit(1)


# if __name__ == '__main__':
#     main()