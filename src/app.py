"""
Legal Mind Agent - Production Application with Enterprise Security

Features:
- Azure Key Vault integration for secure secrets management
- Content safety filtering and PII protection
- Regional compliance and data residency controls
- Comprehensive audit logging and compliance reporting
"""

from http import HTTPStatus
import os
import sys
import logging
import json
from datetime import datetime
from aiohttp import web
from aiohttp.web import middleware

# Add legal_mind package to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from legal_mind.security import (
        initialize_security_framework,
        get_secure_config,
        get_compliance_coordinator,
        get_regional_compliance_manager,
        validate_deployment_security,
        get_security_status,
        DataResidencyRegion
    )
    from legal_mind.bots.teams_bot import LegalMindTeamsBot
    SECURITY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Security framework not available: {e}")
    SECURITY_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

routes = web.RouteTableDef()

@middleware
async def security_middleware(request, handler):
    """Security middleware for compliance and audit logging"""
    start_time = datetime.utcnow()
    
    try:
        # Log request for compliance audit
        if SECURITY_AVAILABLE:
            regional = get_regional_compliance_manager()
            user_region = request.headers.get('X-User-Region')
            
            # Generate conversation ID for this request
            conversation_id = f"{request.remote}_{start_time.isoformat()}"
            regional.log_conversation_storage(conversation_id, user_region)
        
        # Process request through content safety if available
        if SECURITY_AVAILABLE and request.method == 'POST':
            compliance = get_compliance_coordinator()
            
            # Read and validate request body
            if request.can_read_body:
                body = await request.text()
                
                # Apply content safety filtering
                safety_result = await compliance.process_message_async(body)
                
                if not safety_result["safe"]:
                    logger.warning(f"Content safety violation: {safety_result['violations']}")
                    return web.Response(
                        text=json.dumps({
                            "error": "Content safety violation",
                            "message": "Your message contains content that violates our safety policies."
                        }),
                        content_type="application/json",
                        status=HTTPStatus.BAD_REQUEST
                    )
                
                # Replace request body with scrubbed version
                request._body = safety_result["processed_text"].encode('utf-8')
        
        # Process the request
        response = await handler(request)
        
        # Log response for audit
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Request processed: {request.method} {request.path} - {response.status} ({duration:.3f}s)")
        
        return response
        
    except Exception as e:
        logger.error(f"Security middleware error: {e}")
        return web.Response(
            text=json.dumps({"error": "Internal security error"}),
            content_type="application/json", 
            status=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@routes.get("/")
async def health_check(req: web.Request) -> web.Response:
    """Health check endpoint with security status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Legal Mind Agent",
        "version": "1.0.0"
    }
    
    if SECURITY_AVAILABLE:
        try:
            security_status = get_security_status()
            health_status["security"] = {
                "framework_initialized": security_status["framework_initialized"],
                "components_available": len([
                    c for c in security_status["components"].values() 
                    if c.get("available", False)
                ])
            }
        except Exception as e:
            health_status["security"] = {"error": str(e)}
    else:
        health_status["security"] = {"available": False}
    
    return web.Response(
        text=json.dumps(health_status, indent=2),
        content_type="application/json",
        status=HTTPStatus.OK
    )

@routes.get("/security/status")
async def security_status(req: web.Request) -> web.Response:
    """Detailed security framework status"""
    if not SECURITY_AVAILABLE:
        return web.Response(
            text=json.dumps({"error": "Security framework not available"}),
            content_type="application/json",
            status=HTTPStatus.SERVICE_UNAVAILABLE
        )
    
    try:
        status = get_security_status()
        return web.Response(
            text=json.dumps(status, indent=2),
            content_type="application/json",
            status=HTTPStatus.OK
        )
    except Exception as e:
        logger.error(f"Error getting security status: {e}")
        return web.Response(
            text=json.dumps({"error": str(e)}),
            content_type="application/json",
            status=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@routes.get("/compliance/report")
async def compliance_report(req: web.Request) -> web.Response:
    """Generate data residency compliance report"""
    if not SECURITY_AVAILABLE:
        return web.Response(
            text=json.dumps({"error": "Security framework not available"}),
            content_type="application/json",
            status=HTTPStatus.SERVICE_UNAVAILABLE
        )
    
    try:
        regional = get_regional_compliance_manager()
        report = regional.get_data_residency_report()
        
        return web.Response(
            text=json.dumps(report, indent=2),
            content_type="application/json",
            status=HTTPStatus.OK
        )
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        return web.Response(
            text=json.dumps({"error": str(e)}),
            content_type="application/json",
            status=HTTPStatus.INTERNAL_SERVER_ERROR
        )

@routes.post("/api/messages")
async def process_messages(req: web.Request) -> web.Response:
    """Process Teams messages with full security and compliance"""
    try:
        body = await req.text()
        logger.info(f"Received message request")
        
        if not body:
            return web.Response(
                text=json.dumps({"error": "Empty request body"}),
                content_type="application/json",
                status=HTTPStatus.BAD_REQUEST
            )
        
        # Parse request body
        try:
            message_data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request: {e}")
            return web.Response(
                text=json.dumps({"error": "Invalid JSON format"}),
                content_type="application/json",
                status=HTTPStatus.BAD_REQUEST
            )
        
        # Initialize Teams bot if available
        try:
            from legal_mind.bots.teams_bot import LegalMindTeamsBot
            
            # Get secure configuration
            if SECURITY_AVAILABLE:
                config = get_secure_config()
                bot_config = {
                    "app_id": await config.get_secret("MICROSOFT_APP_ID"),
                    "app_password": await config.get_secret("MICROSOFT_APP_PASSWORD"),
                    "openai_api_key": await config.get_secret("OPENAI_API_KEY"),
                    "azure_openai_endpoint": await config.get_secret("AZURE_OPENAI_ENDPOINT")
                }
            else:
                # Fallback to environment variables
                bot_config = {
                    "app_id": os.environ.get("MICROSOFT_APP_ID"),
                    "app_password": os.environ.get("MICROSOFT_APP_PASSWORD"), 
                    "openai_api_key": os.environ.get("OPENAI_API_KEY"),
                    "azure_openai_endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT")
                }
            
            # Create bot instance
            bot = LegalMindTeamsBot(bot_config)
            
            # Process the message
            response = await bot.process_message(message_data)
            
            return web.Response(
                text=json.dumps(response),
                content_type="application/json",
                status=HTTPStatus.OK
            )
            
        except ImportError:
            logger.warning("Teams bot not available, using simple response")
            
            # Simple response for testing
            return web.Response(
                text=json.dumps({
                    "type": "message",
                    "text": "Hello! Legal Mind Agent is running with enterprise security.",
                    "timestamp": datetime.utcnow().isoformat()
                }),
                content_type="application/json",
                status=HTTPStatus.OK
            )
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return web.Response(
            text=json.dumps({"error": "Internal server error"}),
            content_type="application/json",
            status=HTTPStatus.INTERNAL_SERVER_ERROR
        )

async def create_app() -> web.Application:
    """Create and configure the web application with security framework"""
    
    # Initialize security framework if available
    if SECURITY_AVAILABLE:
        logger.info("Initializing security framework...")
        try:
            # Determine primary region from environment
            region_str = os.environ.get("AZURE_REGION", "eastus2")
            primary_region = DataResidencyRegion.US_EAST_2  # Default
            
            for region in DataResidencyRegion:
                if region.value == region_str:
                    primary_region = region
                    break
            
            # Initialize security framework
            init_result = initialize_security_framework(
                primary_region=primary_region,
                enable_content_safety=True,
                enable_key_vault=True
            )
            
            if init_result["initialized"]:
                logger.info("Security framework initialized successfully")
                
                # Validate deployment security
                service_endpoints = {
                    "app_service": os.environ.get("WEBSITE_HOSTNAME", "localhost"),
                    "azure_openai": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
                    "key_vault": os.environ.get("AZURE_KEY_VAULT_URL", "")
                }
                
                validation = validate_deployment_security(service_endpoints)
                if not validation["overall_secure"]:
                    logger.warning(f"Security validation issues: {validation['critical_issues']}")
                    for rec in validation["recommendations"]:
                        logger.info(f"Security recommendation: {rec}")
                
            else:
                logger.error(f"Security framework initialization failed: {init_result['errors']}")
                
        except Exception as e:
            logger.error(f"Error initializing security framework: {e}")
    else:
        logger.warning("Security framework not available - running in basic mode")
    
    # Create application
    app = web.Application(middlewares=[security_middleware] if SECURITY_AVAILABLE else [])
    app.add_routes(routes)
    
    # Add startup and cleanup handlers
    async def startup_handler(app):
        logger.info("Legal Mind Agent starting up...")
        
    async def cleanup_handler(app):
        logger.info("Legal Mind Agent shutting down...")
        
        # Generate final compliance report if security is available
        if SECURITY_AVAILABLE:
            try:
                regional = get_regional_compliance_manager()
                final_report = regional.get_data_residency_report()
                logger.info(f"Final compliance report: {json.dumps(final_report, indent=2)}")
            except Exception as e:
                logger.error(f"Error generating final compliance report: {e}")
    
    app.on_startup.append(startup_handler)
    app.on_cleanup.append(cleanup_handler)
    
    return app

app = web.Application()
app.add_routes(routes)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting test server on port {port}")
    web.run_app(app, host="0.0.0.0", port=port)
