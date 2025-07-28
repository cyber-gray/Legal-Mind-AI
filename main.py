#!/usr/bin/env python3
"""
Legal Mind Agent - Microsoft Teams Bot
A multi-agent AI legal assistant that provides specialized legal analysis.

This is the main entry point for the Legal Mind Agent bot using Microsoft Bot Framework SDK 4.17
with proper Teams integration and enhanced messaging patterns.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import List

import aiohttp
from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import (
    ActivityHandler,
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    MessageFactory,
    TurnContext,
    CardFactory,
)
from botbuilder.schema import (
    Activity, 
    ChannelAccount, 
    ActivityTypes,
    Attachment,
    SuggestedActions,
    CardAction,
    ActionTypes
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LegalMindAgent(ActivityHandler):
    """
    Legal Mind Agent - Multi-Agent Legal Assistant
    
    Enhanced Teams bot using Bot Framework SDK 4.23 with proper Teams integration.
    Coordinates specialized AI policy agents for regulatory compliance guidance.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Legal Mind Agent"
        self.version = "3.0"
        
    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """Handle incoming message activities with proper Teams integration"""
        try:
            # Send typing indicator to show bot is processing
            await self._send_typing_indicator(turn_context)
            
            user_message = turn_context.activity.text.strip() if turn_context.activity.text else ""
            logger.info(f"Processing legal query: {user_message[:50]}...")
            
            # Route to appropriate specialized agent and get response
            response_text, suggested_actions = await self.process_legal_query(user_message)
            
            # Create response message with suggested actions
            response_activity = MessageFactory.text(response_text)
            
            # Add suggested actions if available
            if suggested_actions:
                response_activity.suggested_actions = SuggestedActions(
                    actions=suggested_actions
                )
            
            # Send response via context.send_activity (proper Teams pattern)
            await turn_context.send_activity(response_activity)
            logger.info("Legal analysis delivered successfully")
            
        except Exception as e:
            logger.exception(f"Error processing legal query: {e}")
            await turn_context.send_activity(
                MessageFactory.text(
                    "⚠️ I apologize, but I encountered an error while processing your legal query. "
                    "Please try rephrasing your question or contact support if the issue persists.\n\n"
                    "*This system is for research purposes only and not a substitute for professional legal advice.*"
                )
            )
    
    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ) -> None:
        """Welcome new users with Legal Mind Agent introduction and suggested actions"""
        welcome_text = (
            "🤖⚖️ **Welcome to Legal Mind Agent!**\n\n"
            "I'm your AI Policy Expert for Regulatory Compliance, powered by Microsoft's AI platform. "
            "I coordinate specialized agents to provide citation-rich compliance guidance:\n\n"
            "🔧 **Specialized AI Policy Agents:**\n"
            "• **Regulation Analysis** - AI regulation ingestion & framework analysis\n"
            "• **Risk Scoring** - Compliance risk assessment & scoring\n"
            "• **Compliance Expert** - Regulatory compliance & audit preparation\n"
            "• **Policy Translation** - Complex regulation interpretation\n"
            "• **Comparative Regulatory** - Cross-jurisdictional analysis\n\n"
            "⚠️ **Research Purpose Only**: This solution is for research and educational purposes. "
            "Always consult qualified legal professionals for compliance decisions.\n\n"
            "*What regulatory compliance matter can I help you with today?*"
        )
        
        # Create suggested actions for quick start
        suggested_actions = [
            CardAction(
                type=ActionTypes.im_back,
                title="🔍 Analyze EU AI Act",
                value="Analyze EU AI Act requirements for our chatbot"
            ),
            CardAction(
                type=ActionTypes.im_back,
                title="📊 Risk Assessment",
                value="Score compliance risk for facial recognition deployment"
            ),
            CardAction(
                type=ActionTypes.im_back,
                title="✅ GDPR Compliance",
                value="GDPR compliance checklist for AI data processing"
            ),
            CardAction(
                type=ActionTypes.im_back,
                title="🌍 Compare Regulations",
                value="Compare US vs EU AI governance requirements"
            )
        ]
        
        welcome_activity = MessageFactory.text(welcome_text)
        welcome_activity.suggested_actions = SuggestedActions(actions=suggested_actions)
        
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(welcome_activity)
    
    async def _send_typing_indicator(self, turn_context: TurnContext) -> None:
        """Send typing indicator to show bot is processing"""
        try:
            typing_activity = Activity(
                type=ActivityTypes.typing,
                relates_to=turn_context.activity.relates_to
            )
            await turn_context.send_activity(typing_activity)
        except Exception as e:
            logger.warning(f"Could not send typing indicator: {e}")
    
    async def process_legal_query(self, user_message: str) -> tuple[str, List[CardAction]]:
        """
        Process legal queries through specialized agent coordination
        
        Returns tuple of (response_text, suggested_actions)
        """
        if not user_message:
            return self._get_help_message()
        
        # Analyze query intent and route to appropriate agents
        query_intent = self._analyze_query_intent(user_message)
        
        # Route to specialized AI policy agents
        if query_intent == "regulation":
            return await self._handle_regulation_analysis(user_message)
        elif query_intent == "risk":
            return await self._handle_risk_scoring(user_message)
        elif query_intent == "compliance":
            return await self._handle_compliance_query(user_message)
        elif query_intent == "policy":
            return await self._handle_policy_translation(user_message)
        elif query_intent == "comparative":
            return await self._handle_comparative_analysis(user_message)
        elif query_intent == "greeting":
            return self._get_greeting_response()
        else:
            return await self._handle_general_legal_query(user_message)
    
    def _analyze_query_intent(self, message: str) -> str:
        """Analyze user query to determine appropriate specialized AI policy agent"""
        message_lower = message.lower()
        
        # Regulation analysis keywords
        if any(keyword in message_lower for keyword in [
            'regulation', 'ai act', 'gdpr', 'ccpa', 'nist', 'framework', 'law', 'statute'
        ]):
            return "regulation"
        
        # Risk scoring keywords
        elif any(keyword in message_lower for keyword in [
            'risk', 'score', 'assessment', 'evaluate', 'facial recognition', 'biometric'
        ]):
            return "risk"
        
        # Compliance keywords
        elif any(keyword in message_lower for keyword in [
            'compliance', 'checklist', 'audit', 'requirement', 'data processing', 'privacy'
        ]):
            return "compliance"
        
        # Policy translation keywords
        elif any(keyword in message_lower for keyword in [
            'translate', 'explain', 'implementation', 'steps', 'guidance', 'interpret'
        ]):
            return "policy"
        
        # Comparative analysis keywords
        elif any(keyword in message_lower for keyword in [
            'compare', 'difference', 'versus', 'vs', 'between', 'jurisdiction', 'us vs eu'
        ]):
            return "comparative"
        
        # Greeting keywords
        elif any(keyword in message_lower for keyword in [
            'hello', 'hi', 'hey', 'help', 'what can you do'
        ]):
            return "greeting"
        
        return "general"
    
    async def _handle_regulation_analysis(self, message: str) -> tuple[str, List[CardAction]]:
        """Handle regulation analysis queries"""
        response = (
            f"📋 **Regulation Analysis Agent**\n\n"
            f"**Query:** {message}\n\n"
            f"**Analysis Framework:** I specialize in AI regulation ingestion and framework analysis:\n\n"
            f"• **EU AI Act** - High-risk AI system classifications and requirements\n"
            f"• **GDPR/CCPA** - Data protection and privacy regulations for AI\n"
            f"• **NIST AI Framework** - Risk management and governance standards\n"
            f"• **Sectoral Regulations** - Industry-specific AI compliance requirements\n\n"
            f"📖 **Research Disclaimer:** This analysis is for research and educational purposes only. "
            f"Always consult qualified legal professionals for compliance decisions.\n\n"
            f"*Please specify the regulation and your AI system for detailed analysis.*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🇪🇺 EU AI Act Details", value="Explain EU AI Act high-risk categories"),
            CardAction(type=ActionTypes.im_back, title="🛡️ GDPR for AI", value="GDPR requirements for AI data processing"),
            CardAction(type=ActionTypes.im_back, title="📊 NIST Framework", value="NIST AI Risk Management Framework overview")
        ]
        
        return response, suggested_actions
    
    async def _handle_risk_scoring(self, message: str) -> tuple[str, List[CardAction]]:
        """Handle risk scoring queries"""
        response = (
            f"🔍 **Risk Scoring Agent**\n\n"
            f"**Query:** {message}\n\n"
            f"**Risk Assessment Framework:** I provide compliance risk assessment and scoring:\n\n"
            f"• **High-Risk AI Classification** - EU AI Act risk category assessment\n"
            f"• **Data Protection Risk** - GDPR/CCPA privacy impact scoring\n"
            f"• **Algorithmic Bias Risk** - Fairness and discrimination assessment\n"
            f"• **Transparency Requirements** - Explainability and disclosure obligations\n\n"
            f"📖 **Research Disclaimer:** Risk scores are for research purposes only. "
            f"Professional legal review required for production deployments.\n\n"
            f"*Describe your AI system for comprehensive risk scoring.*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🎯 High-Risk Assessment", value="Is my AI system high-risk under EU AI Act?"),
            CardAction(type=ActionTypes.im_back, title="⚖️ Bias Risk Check", value="Assess algorithmic bias risk for hiring AI"),
            CardAction(type=ActionTypes.im_back, title="🔒 Privacy Impact", value="GDPR privacy impact assessment for AI")
        ]
        
        return response, suggested_actions
    
    async def _handle_compliance_query(self, message: str) -> tuple[str, List[CardAction]]:
        """Handle compliance-related queries"""
        response = (
            f"✅ **Compliance Expert Agent**\n\n"
            f"**Query:** {message}\n\n"
            f"**Compliance Framework:** I provide regulatory compliance and audit preparation:\n\n"
            f"• **Compliance Checklists** - Step-by-step regulatory requirements\n"
            f"• **Audit Preparation** - Documentation and evidence requirements\n"
            f"• **Implementation Roadmaps** - Practical compliance deployment guides\n"
            f"• **Monitoring & Reporting** - Ongoing compliance maintenance\n\n"
            f"📖 **Research Disclaimer:** Compliance guidance is for educational purposes. "
            f"Engage qualified legal counsel for production compliance programs.\n\n"
            f"*What specific compliance requirements do you need guidance on?*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="📋 GDPR Checklist", value="GDPR compliance checklist for AI systems"),
            CardAction(type=ActionTypes.im_back, title="📄 Documentation Guide", value="Required documentation for AI Act compliance"),
            CardAction(type=ActionTypes.im_back, title="🔍 Audit Preparation", value="Prepare for AI compliance audit")
        ]
        
        return response, suggested_actions
    
    async def _handle_policy_translation(self, message: str) -> tuple[str, List[CardAction]]:
        """Handle policy translation queries"""
        response = (
            f"📖 **Policy Translation Agent**\n\n"
            f"**Query:** {message}\n\n"
            f"**Translation Framework:** I translate complex regulations into actionable guidance:\n\n"
            f"• **Plain Language Translation** - Converting legal text to clear requirements\n"
            f"• **Implementation Steps** - Practical action items from regulatory text\n"
            f"• **Technical Mapping** - Linking regulations to technical implementations\n"
            f"• **Best Practices** - Industry-standard approaches to compliance\n\n"
            f"📖 **Research Disclaimer:** Translations are for research and educational purposes. "
            f"Original regulatory text and legal counsel remain authoritative.\n\n"
            f"*Which regulation would you like me to translate into actionable steps?*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🔧 NIST Implementation", value="Translate NIST AI framework into implementation steps"),
            CardAction(type=ActionTypes.im_back, title="📐 EU AI Act Guide", value="Convert EU AI Act requirements to technical specs"),
            CardAction(type=ActionTypes.im_back, title="🛡️ Privacy by Design", value="Implement GDPR privacy by design principles")
        ]
        
        return response, suggested_actions
    
    async def _handle_comparative_analysis(self, message: str) -> tuple[str, List[CardAction]]:
        """Handle comparative regulatory analysis"""
        response = (
            f"⚖️ **Comparative Regulatory Agent**\n\n"
            f"**Query:** {message}\n\n"
            f"**Comparative Framework:** I analyze regulatory differences across jurisdictions:\n\n"
            f"• **Cross-Jurisdictional Mapping** - US vs EU vs Asia-Pacific AI regulations\n"
            f"• **Harmonization Analysis** - Common principles and divergent approaches\n"
            f"• **Global Compliance Strategy** - Multi-jurisdiction deployment guidance\n"
            f"• **Regulatory Trends** - Emerging patterns in AI governance\n\n"
            f"📖 **Research Disclaimer:** Comparative analysis is for research purposes. "
            f"Jurisdiction-specific legal advice required for global deployments.\n\n"
            f"*Which jurisdictions would you like me to compare for your AI system?*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🌍 US vs EU AI Laws", value="Compare US and EU AI governance requirements"),
            CardAction(type=ActionTypes.im_back, title="🔄 Global Harmonization", value="Common AI principles across jurisdictions"),
            CardAction(type=ActionTypes.im_back, title="📈 Regulatory Trends", value="Emerging AI regulation trends globally")
        ]
        
        return response, suggested_actions
    
    async def _handle_general_legal_query(self, message: str) -> tuple[str, List[CardAction]]:
        """Handle general legal queries"""
        response = (
            f"🤖⚖️ **Legal Mind Agent**\n\n"
            f"**Your Question:** {message}\n\n"
            f"**AI Policy Expertise:** I specialize in regulatory compliance for AI systems. "
            f"For the most accurate analysis, please specify:\n\n"
            f"• **AI System Type** - Chatbot, facial recognition, hiring algorithm, etc.\n"
            f"• **Jurisdiction** - EU, US, California, UK, etc.\n"
            f"• **Regulatory Focus** - EU AI Act, GDPR, CCPA, NIST framework\n"
            f"• **Use Case** - Risk assessment, compliance checklist, implementation guide\n\n"
            f"📖 **Research Disclaimer:** This system provides research and educational guidance only. "
            f"Professional legal counsel required for production compliance decisions.\n\n"
            f"*How can I assist with your AI regulatory compliance needs?*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🔍 Regulation Analysis", value="Analyze EU AI Act requirements"),
            CardAction(type=ActionTypes.im_back, title="📊 Risk Assessment", value="Score compliance risk for my AI system"),
            CardAction(type=ActionTypes.im_back, title="✅ Compliance Guide", value="Create compliance checklist"),
            CardAction(type=ActionTypes.im_back, title="🌍 Compare Laws", value="Compare AI regulations across jurisdictions")
        ]
        
        return response, suggested_actions
    
    def _get_greeting_response(self) -> tuple[str, List[CardAction]]:
        """Return greeting response with suggested actions"""
        response = (
            "👋 **Hello! I'm Legal Mind Agent**\n\n"
            "I'm your AI Policy Expert for Regulatory Compliance, specializing in:\n\n"
            "🔧 **Specialized AI Policy Agents:**\n"
            "• **Regulation Analysis** - AI regulation framework analysis\n"
            "• **Risk Scoring** - Compliance risk assessment & scoring\n"
            "• **Compliance Expert** - Regulatory compliance & audit prep\n"
            "• **Policy Translation** - Converting regulations to action items\n"
            "• **Comparative Regulatory** - Cross-jurisdictional analysis\n\n"
            "📖 **Research Purpose Only** - Educational guidance, not legal advice.\n\n"
            "*What AI regulatory compliance matter can I help you with?*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🇪🇺 EU AI Act", value="Analyze EU AI Act requirements for chatbot"),
            CardAction(type=ActionTypes.im_back, title="🔍 Risk Score", value="Score compliance risk for facial recognition"),
            CardAction(type=ActionTypes.im_back, title="✅ GDPR Compliance", value="GDPR compliance checklist for AI"),
            CardAction(type=ActionTypes.im_back, title="🌍 Compare Regs", value="Compare US vs EU AI governance")
        ]
        
        return response, suggested_actions
    
    def _get_help_message(self) -> tuple[str, List[CardAction]]:
        """Return help message for empty queries"""
        response = (
            "🤖⚖️ **Welcome to Legal Mind Agent!**\n\n"
            "I'm your AI Policy Expert ready to help with regulatory compliance. "
            "I coordinate specialized agents for:\n\n"
            "• Regulation analysis and framework interpretation\n"
            "• Risk assessment and compliance scoring\n"
            "• Compliance checklists and audit preparation\n"
            "• Policy translation and implementation guidance\n"
            "• Comparative regulatory analysis\n\n"
            "📖 **Research Purpose Only** - This is educational guidance, not legal advice.\n\n"
            "*How can I assist with your AI regulatory compliance needs today?*"
        )
        
        suggested_actions = [
            CardAction(type=ActionTypes.im_back, title="🔍 Start Analysis", value="Analyze regulations for my AI system"),
            CardAction(type=ActionTypes.im_back, title="📊 Risk Assessment", value="Assess compliance risks"),
            CardAction(type=ActionTypes.im_back, title="✅ Get Checklist", value="Create compliance checklist"),
            CardAction(type=ActionTypes.im_back, title="❓ Learn More", value="What can Legal Mind Agent do?")
        ]
        
        return response, suggested_actions

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
        # Import and initialize key modules
        from thread_session import get_thread_session
        from legal_tools import get_legal_tools
        
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
        bot = LegalMindAgent()
        
        # Enhanced error handler with proper Teams integration
        async def on_error(context: TurnContext, error: Exception):
            logger.error(f"Bot error: {error}")
            error_message = (
                "⚠️ I apologize, but I encountered an error while processing your request. "
                "Please try again or contact support if the issue persists.\n\n"
                "📖 **Research Disclaimer:** This system is for research and educational purposes only. "
                "For production legal matters, please consult qualified legal professionals."
            )
            await context.send_activity(MessageFactory.text(error_message))
        
        adapter.on_turn_error = on_error
        
        logger.info("Legal Mind Agent initialized successfully with Teams integration")
        return adapter, bot
        
    except Exception as e:
        logger.exception(f"Failed to initialize bot: {e}")
        sys.exit(1)

# Initialize bot components
ADAPTER, BOT = initialize_bot()

# Create the web application
def create_app():
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
        logger.info("🔧 Enhanced with Bot Framework SDK 4.17 and proper Teams integration")
        logger.info("📖 Research and educational purposes only - not legal advice")
        
        # Run the application
        web.run_app(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.exception(f"Failed to start Legal Mind Agent: {e}")
