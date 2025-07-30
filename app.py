#!/usr/bin/env python3
"""
Legal Mind Agent - Production Entry Point

Streamlined entry point using modular package structure for maintainability.
Enhanced Teams integration with proper Bot Framework patterns.
"""

import json
import logging
import os
import sys
from datetime import datetime
from aiohttp import web, Request, Response
from aiohttp.web import Application

# Bot Framework imports
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, MessageFactory
from botbuilder.schema import Activity

# Legal Mind package imports
from legal_mind import LegalMindTeamsBot
from legal_mind.tools import get_legal_tools
from legal_mind.orchestrator import get_thread_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot Framework message handler with enhanced Teams integration
async def messages(request: Request) -> Response:
    """
    Handle Bot Framework messages with proper Teams integration patterns
    
    Uses BotFrameworkAdapter.process_activity for automatic JWT validation,
    mandatory 200 OK response, and proper Connector API integration.
    """
    try:
        # Read request body
        body = await request.read()
        activity = Activity().deserialize(json.loads(body.decode("utf-8")))
        
        logger.info(f"Received activity type: {activity.type} from channel: {activity.channel_id}")
        
        # Get authorization header for JWT validation
        auth_header = request.headers.get("Authorization", "")
        
        try:
            # Process activity through Bot Framework adapter
            # This automatically:
            # - Validates JWT tokens from Teams/Bot Framework
            # - Returns mandatory 200 OK to Teams
            # - Handles Connector API authentication for replies
            response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
            
            # Bot Framework adapter handles the response
            if response:
                return web.json_response(data=response.body, status=response.status)
            
            # Always return 200 OK to Teams (Bot Framework requirement)
            return web.Response(status=200)
            
        except Exception as adapter_error:
            logger.error(f"Bot Framework adapter error: {adapter_error}")
            # Always return 200 to Teams to acknowledge receipt and prevent retries
            return web.Response(status=200)
            
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        # Return 200 to avoid Teams retry loops
        return web.Response(status=200)

# Health check endpoint - Enhanced for Azure App Service stability
async def health_check(request: Request) -> Response:
    """
    Health check endpoint for monitoring with enhanced Teams integration status
    Designed for Azure App Service Always-On and Application Insights availability tests
    """
    try:
        # Pre-warm critical components to prevent cold starts
        await _warm_up_components()
        
        health_status = {
            "status": "healthy", 
            "timestamp": datetime.utcnow().isoformat(),
            "bot": "Legal Mind Agent", 
            "version": "v3.0",
            "architecture": "Modular package structure",
            "framework": "Bot Framework SDK 4.17",
            "teams_integration": "Enhanced with proper messaging patterns",
            "azure_agents": "Integrated with ThreadSession management",
            "tools": ["Vector Search", "Deep Research", "Compliance Checker"],
            "agents": [
                "Regulation Analysis Agent",
                "Risk Scoring Agent", 
                "Compliance Expert",
                "Policy Translation Agent",
                "Comparative Regulatory Agent"
            ],
            "environment": {
                "python_version": "3.11",
                "port": os.getenv("PORT", "80"),
                "azure_agents_configured": bool(os.getenv("AZURE_AI_AGENTS_ENDPOINT")),
                "app_service_ready": True
            },
            "performance": {
                "startup_optimized": True,
                "always_on_recommended": True,
                "cold_start_mitigation": "Active"
            },
            "disclaimer": "Research and educational purposes only - not legal advice"
        }
        
        return web.json_response(health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return web.json_response({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, status=500)

async def _warm_up_components():
    """Pre-warm critical components to prevent cold start delays"""
    try:
        # Pre-warm ThreadSession (this initializes agents)
        thread_session = await get_thread_session()
        
        # Pre-warm legal tools
        legal_tools = get_legal_tools()
        
        logger.debug("Components pre-warmed successfully")
        
    except Exception as e:
        logger.warning(f"Component warm-up failed (non-critical): {e}")

# Initialize the bot and adapter
def initialize_bot():
    """Initialize the Legal Mind Agent bot with enhanced Teams integration"""
    try:
        app_id = os.environ.get("MicrosoftAppId", "")
        app_password = os.environ.get("MicrosoftAppPassword", "")
        
        logger.info(f"Initializing Legal Mind Agent with App ID: {app_id[:8]}..." if app_id else "No App ID configured")
        
        # Create adapter settings with enhanced configuration
        settings = BotFrameworkAdapterSettings(
            app_id=app_id,
            app_password=app_password
        )
        
        # Create adapter and bot with improved error handling
        adapter = BotFrameworkAdapter(settings)
        bot = LegalMindTeamsBot()  # Using the new modular bot class
        
        # Enhanced error handler with proper Teams integration
        async def on_error(context, error):
            logger.error(f"Bot error: {error}")
            error_message = (
                "⚠️ I apologize, but I encountered an error while processing your request. "
                "Please try again or contact support if the issue persists.\\n\\n"
                "📖 **Research Disclaimer:** This system is for research and educational purposes only. "
                "For production legal matters, please consult qualified legal professionals."
            )
            await context.send_activity(MessageFactory.text(error_message))
        
        adapter.on_turn_error = on_error
        
        logger.info("Legal Mind Agent initialized successfully with modular architecture")
        return adapter, bot
        
    except Exception as e:
        logger.exception(f"Failed to initialize bot: {e}")
        sys.exit(1)

# Initialize bot components
ADAPTER, BOT = initialize_bot()

# Create the web application
def create_app() -> Application:
    """Create the web application"""
    app = web.Application()
    
    # Bot Framework endpoint
    app.router.add_post("/api/messages", messages)
    
    # Health check endpoints
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)
    
    return app

if __name__ == "__main__":
    try:
        # Get port from environment or default to 80
        port = int(os.getenv("PORT", 80))
        
        # Create application
        app = create_app()
        
        logger.info(f"🚀 Starting Legal Mind Agent v3.0 on port {port}")
        logger.info("🤖⚖️ AI Policy Expert for Regulatory Compliance")
        logger.info("🏗️ Modular architecture with specialized agent packages")
        logger.info("🔧 Enhanced with Bot Framework SDK 4.17 and proper Teams integration")
        logger.info("📖 Research and educational purposes only - not legal advice")
        
        # Run the application
        web.run_app(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.exception(f"Failed to start Legal Mind Agent: {e}")
        sys.exit(1)
