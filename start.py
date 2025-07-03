#!/usr/bin/env python3
"""
Legal-Mind-AI Startup Script
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from config import settings

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=getattr(logging, settings.app.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('legal_mind_ai.log') if not settings.app.debug else logging.NullHandler()
        ]
    )

def validate_environment():
    """Validate that all required environment variables are set"""
    missing_vars = settings.validate()
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        print("See .env.example for a template.")
        return False
    
    return True

def check_dependencies():
    """Check if all required dependencies are available"""
    required_packages = [
        ('aiohttp', 'aiohttp'),
        ('botbuilder.core', 'botbuilder-core'),
        ('azure.ai.projects', 'azure-ai-projects'),
        ('azure.identity', 'azure-identity')
    ]
    
    missing_packages = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nPlease install missing packages:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🤖 Starting Legal-Mind-AI...")
    
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    logger.info("✅ Environment validation passed")
    logger.info(f"🏢 Company: {settings.app.company_name}")
    logger.info(f"🌐 Port: {settings.teams.app_port}")
    logger.info(f"🔧 Debug mode: {settings.app.debug}")
    
    try:
        # Import and start the bot
        from legal_mind_bot import create_app
        from aiohttp import web
        
        app = create_app()
        
        print(f"✅ Legal-Mind-AI is starting on port {settings.teams.app_port}")
        print(f"🔗 Bot endpoint: http://localhost:{settings.teams.app_port}/api/messages")
        print(f"💊 Health check: http://localhost:{settings.teams.app_port}/health")
        print("\n🚀 Legal-Mind-AI is ready to help with AI policy questions!")
        
        web.run_app(app, host="0.0.0.0", port=settings.teams.app_port)
        
    except KeyboardInterrupt:
        print("\n👋 Legal-Mind-AI shutting down...")
        logger.info("Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to start Legal-Mind-AI: {str(e)}")
        logger.error(f"Startup error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
