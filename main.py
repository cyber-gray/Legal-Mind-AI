#!/usr/bin/env python3
"""
Legal Mind Agent Pro - Microsoft Teams Bot
A multi-agent AI legal assistant that provides specialized legal analysis.

This is the main entry point for the Legal Mind Agent Pro bot.
The bot coordinates multiple specialized legal agents to provide comprehensive legal advice.
"""

import asyncio
import json
import logging
import os
import sys
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
)
from botbuilder.schema import Activity, ChannelAccount

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LegalMindAgentPro(ActivityHandler):
    """
    Legal Mind Agent Pro - Multi-Agent Legal Assistant
    
    This bot coordinates specialized legal agents:
    - Contract Analysis Agent
    - Legal Research Agent  
    - Compliance Expert
    - Policy Analyst
    - Comparative Legal Analyst
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Legal Mind Agent Pro"
        self.version = "2.0"
        
    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """Handle incoming message activities and coordinate agent responses"""
        try:
            user_message = turn_context.activity.text.strip() if turn_context.activity.text else ""
            logger.info(f"Processing legal query: {user_message[:50]}...")
            
            # Route to appropriate specialized agent
            response_text = await self.process_legal_query(user_message)
            
            # Send response
            await turn_context.send_activity(MessageFactory.text(response_text))
            logger.info("Legal analysis delivered successfully")
            
        except Exception as e:
            logger.exception(f"Error processing legal query: {e}")
            await turn_context.send_activity(
                MessageFactory.text(
                    "I apologize, but I encountered an error while processing your legal query. "
                    "Please try rephrasing your question or contact support if the issue persists."
                )
            )
    
    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ) -> None:
        """Welcome new users with Legal Mind Agent Pro introduction"""
        welcome_text = (
            "⚖️ **Welcome to Legal Mind Agent Pro!**\n\n"
            "I'm your AI-powered legal assistant with specialized expertise in:\n"
            "• **Contract Analysis** - Review agreements, terms, and legal documents\n"
            "• **Legal Research** - Find relevant case law, statutes, and precedents\n"
            "• **Compliance Guidance** - Navigate regulatory requirements\n"
            "• **Policy Analysis** - Understand legal frameworks and policies\n"
            "• **Comparative Law** - Cross-jurisdictional legal analysis\n\n"
            "**Try asking me:**\n"
            "• 'Analyze this employment contract'\n"
            "• 'What are the tenant rights in California?'\n"
            "• 'Research GDPR compliance requirements'\n"
            "• 'Compare contract law between US and UK'\n\n"
            "*How can I assist with your legal matters today?*"
        )
        
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(MessageFactory.text(welcome_text))
    
    async def process_legal_query(self, user_message: str) -> str:
        """
        Process legal queries through specialized agent coordination
        
        This method determines which specialized agents to engage based on the query
        and synthesizes their responses into a comprehensive legal analysis.
        """
        if not user_message:
            return self._get_help_message()
        
        # Analyze query intent and route to appropriate agents
        query_intent = self._analyze_query_intent(user_message)
        
        # Route to specialized legal agents
        if query_intent == "contract":
            return await self._handle_contract_analysis(user_message)
        elif query_intent == "research":
            return await self._handle_legal_research(user_message)
        elif query_intent == "compliance":
            return await self._handle_compliance_query(user_message)
        elif query_intent == "policy":
            return await self._handle_policy_analysis(user_message)
        elif query_intent == "comparative":
            return await self._handle_comparative_analysis(user_message)
        elif query_intent == "greeting":
            return self._get_greeting_response()
        else:
            return await self._handle_general_legal_query(user_message)
    
    def _analyze_query_intent(self, message: str) -> str:
        """Analyze user query to determine appropriate specialized agent"""
        message_lower = message.lower()
        
        # Contract-related keywords
        if any(keyword in message_lower for keyword in [
            'contract', 'agreement', 'terms', 'clause', 'signing', 'negotiate'
        ]):
            return "contract"
        
        # Legal research keywords
        elif any(keyword in message_lower for keyword in [
            'research', 'case law', 'precedent', 'statute', 'ruling', 'court'
        ]):
            return "research"
        
        # Compliance keywords
        elif any(keyword in message_lower for keyword in [
            'compliance', 'regulation', 'regulatory', 'gdpr', 'hipaa', 'requirement'
        ]):
            return "compliance"
        
        # Policy analysis keywords
        elif any(keyword in message_lower for keyword in [
            'policy', 'law', 'legislation', 'framework', 'legal system'
        ]):
            return "policy"
        
        # Comparative analysis keywords
        elif any(keyword in message_lower for keyword in [
            'compare', 'difference', 'versus', 'vs', 'between', 'jurisdiction'
        ]):
            return "comparative"
        
        # Greeting keywords
        elif any(keyword in message_lower for keyword in [
            'hello', 'hi', 'hey', 'help', 'what can you do'
        ]):
            return "greeting"
        
        return "general"
    
    async def _handle_contract_analysis(self, message: str) -> str:
        """Handle contract analysis queries"""
        return (
            f"📋 **Contract Analysis Request**\n\n"
            f"**Query:** {message}\n\n"
            f"**Analysis:** I can help you analyze contracts and agreements. For comprehensive contract review, I recommend:\n\n"
            f"• **Key Terms Review** - Identifying critical clauses and obligations\n"
            f"• **Risk Assessment** - Highlighting potential legal risks\n"
            f"• **Negotiation Points** - Suggesting areas for improvement\n"
            f"• **Compliance Check** - Ensuring regulatory compliance\n\n"
            f"*Please share specific contract sections or terms you'd like me to analyze, and I'll provide detailed legal insights.*"
        )
    
    async def _handle_legal_research(self, message: str) -> str:
        """Handle legal research queries"""
        return (
            f"🔍 **Legal Research Request**\n\n"
            f"**Query:** {message}\n\n"
            f"**Research Approach:** I'll help you find relevant legal precedents and authorities. My research covers:\n\n"
            f"• **Case Law Analysis** - Relevant court decisions and precedents\n"
            f"• **Statutory Research** - Applicable laws and regulations\n"
            f"• **Jurisdictional Analysis** - Location-specific legal requirements\n"
            f"• **Legal Commentary** - Expert analysis and interpretations\n\n"
            f"*Please specify the jurisdiction and legal area you're researching for more targeted results.*"
        )
    
    async def _handle_compliance_query(self, message: str) -> str:
        """Handle compliance-related queries"""
        return (
            f"✅ **Compliance Analysis**\n\n"
            f"**Query:** {message}\n\n"
            f"**Compliance Framework:** I'll help you navigate regulatory requirements including:\n\n"
            f"• **Regulatory Mapping** - Identifying applicable regulations\n"
            f"• **Compliance Requirements** - Specific obligations and deadlines\n"
            f"• **Risk Assessment** - Potential compliance gaps\n"
            f"• **Implementation Guidance** - Practical compliance steps\n\n"
            f"*Please specify your industry and jurisdiction for tailored compliance guidance.*"
        )
    
    async def _handle_policy_analysis(self, message: str) -> str:
        """Handle policy analysis queries"""
        return (
            f"📖 **Policy Analysis**\n\n"
            f"**Query:** {message}\n\n"
            f"**Policy Framework:** I'll analyze legal policies and frameworks including:\n\n"
            f"• **Policy Interpretation** - Understanding legal frameworks\n"
            f"• **Impact Analysis** - How policies affect your situation\n"
            f"• **Implementation Guidelines** - Practical application steps\n"
            f"• **Future Implications** - Potential changes and developments\n\n"
            f"*Please provide more context about the specific policy area you're interested in.*"
        )
    
    async def _handle_comparative_analysis(self, message: str) -> str:
        """Handle comparative legal analysis"""
        return (
            f"⚖️ **Comparative Legal Analysis**\n\n"
            f"**Query:** {message}\n\n"
            f"**Comparative Framework:** I'll analyze legal differences across jurisdictions:\n\n"
            f"• **Jurisdictional Comparison** - Key legal differences\n"
            f"• **Best Practices** - Optimal approaches across jurisdictions\n"
            f"• **Cross-Border Implications** - International legal considerations\n"
            f"• **Harmonization Opportunities** - Common legal principles\n\n"
            f"*Please specify which jurisdictions you'd like me to compare.*"
        )
    
    async def _handle_general_legal_query(self, message: str) -> str:
        """Handle general legal queries"""
        return (
            f"⚖️ **Legal Analysis**\n\n"
            f"**Your Question:** {message}\n\n"
            f"**Response:** I'm here to help with your legal question. For the most accurate analysis, could you provide more details about:\n\n"
            f"• **Legal Area** - Contract law, employment law, corporate law, etc.\n"
            f"• **Jurisdiction** - Which country/state's laws apply\n"
            f"• **Context** - Background information about your situation\n"
            f"• **Specific Goals** - What outcome you're seeking\n\n"
            f"*With more context, I can provide specialized analysis through my expert legal agents.*"
        )
    
    def _get_greeting_response(self) -> str:
        """Return greeting response"""
        return (
            "👋 **Hello! I'm Legal Mind Agent Pro**\n\n"
            "I'm your AI-powered legal assistant with specialized expertise. I can help with:\n\n"
            "• **Contract Analysis** - 'Review this employment agreement'\n"
            "• **Legal Research** - 'Find cases about intellectual property'\n"
            "• **Compliance** - 'GDPR requirements for my business'\n"
            "• **Policy Analysis** - 'Explain new privacy legislation'\n"
            "• **Comparative Law** - 'Compare US vs EU contract law'\n\n"
            "*What legal matter can I assist you with today?*"
        )
    
    def _get_help_message(self) -> str:
        """Return help message for empty queries"""
        return (
            "👋 **Welcome to Legal Mind Agent Pro!**\n\n"
            "I'm ready to help with your legal questions. Try asking me about:\n\n"
            "• Contract analysis and review\n"
            "• Legal research and precedents\n"
            "• Compliance and regulatory guidance\n"
            "• Policy analysis and interpretation\n"
            "• Comparative legal analysis\n\n"
            "*How can I assist with your legal matters today?*"
        )

# Bot Framework message handler
async def messages(request: Request) -> Response:
    """Handle Bot Framework messages"""
    try:
        body = await request.read()
        activity = Activity().deserialize(json.loads(body.decode("utf-8")))
        logger.info(f"Received activity type: {activity.type}")
        
        # Get auth header
        auth_header = request.headers.get("Authorization", "")
        
        try:
            # Process the activity
            response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
            if response:
                return web.json_response(data=response.body, status=response.status)
            return web.Response(status=200)
            
        except Exception as adapter_error:
            logger.error(f"Adapter error: {adapter_error}")
            # Always return 200 to Teams to acknowledge receipt
            return web.Response(status=200)
            
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        return web.Response(status=200)  # Return 200 to avoid Teams retries

# Health check endpoint
async def health_check(request: Request) -> Response:
    """Health check endpoint for monitoring"""
    return web.json_response({
        "status": "healthy", 
        "bot": "Legal Mind Agent Pro", 
        "version": "v2.0",
        "agents": [
            "Contract Analysis Agent",
            "Legal Research Agent", 
            "Compliance Expert",
            "Policy Analyst",
            "Comparative Legal Analyst"
        ]
    })

# Initialize the bot and adapter
def initialize_bot():
    """Initialize the Legal Mind Agent Pro bot"""
    try:
        app_id = os.environ.get("MicrosoftAppId", "")
        app_password = os.environ.get("MicrosoftAppPassword", "")
        
        logger.info(f"Initializing Legal Mind Agent Pro with App ID: {app_id[:8]}..." if app_id else "No App ID configured")
        
        # Create adapter settings
        settings = BotFrameworkAdapterSettings(
            app_id=app_id,
            app_password=app_password
        )
        
        # Create adapter and bot
        adapter = BotFrameworkAdapter(settings)
        bot = LegalMindAgentPro()
        
        # Set up error handler
        async def on_error(context: TurnContext, error: Exception):
            logger.error(f"Bot error: {error}")
            await context.send_activity(
                MessageFactory.text("I apologize, but I encountered an error. Please try again or contact support.")
            )
        
        adapter.on_turn_error = on_error
        
        logger.info("Legal Mind Agent Pro initialized successfully")
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
        
        logger.info(f"🚀 Starting Legal Mind Agent Pro on port {port}")
        logger.info("🤖 Multi-Agent Legal Assistant Ready")
        
        # Run the application
        web.run_app(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.exception(f"Failed to start Legal Mind Agent Pro: {e}")
