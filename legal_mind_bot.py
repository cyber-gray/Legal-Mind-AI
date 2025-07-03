"""
Legal-Mind-AI Teams Bot
Enhanced Teams integration with multi-agent orchestration
"""

import os
import sys
import json
import asyncio
import logging
from typing import Optional
from io import BytesIO

from dotenv import load_dotenv
from aiohttp import web
from aiohttp.web import Request, Response

from botbuilder.core import (
    BotFrameworkAdapterSettings,
    TurnContext,
    BotFrameworkAdapter,
    ConversationState,
    MemoryStorage,
    MessageFactory
)
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount

# Import our services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agents.orchestrator import orchestrator, QueryContext
from services.news_service import news_service
from services.email_service import email_service
from services.pdf_generator import report_generator
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class LegalMindBot:
    """
    Legal-Mind-AI Teams Bot with multi-agent orchestration
    """
    
    def __init__(self):
        self.orchestrator = orchestrator
        
    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """
        Handle incoming message from Teams with enhanced complex query support
        """
        user_message = turn_context.activity.text.strip()
        user_id = turn_context.activity.from_property.id
        
        logger.info(f"Received message from {user_id}: {user_message[:100]}...")
        
        try:
            # Show typing indicator for longer processing
            await self._send_typing_indicator(turn_context)
            
            # Analyze message complexity to adjust processing approach
            word_count = len(user_message.split())
            is_complex = word_count > 100 or user_message.count('?') > 2
            
            # Show extended typing for complex queries
            if is_complex:
                await self._send_extended_typing_indicator(turn_context)
            
            # Create query context with appropriate settings for complexity
            context = QueryContext(
                user_id=user_id,
                query=user_message,
                priority="high" if is_complex else "normal",
                output_format="text",
                max_response_length=3800,  # Teams message limit
                enable_chunking=True
            )
            
            # Check for special commands
            if user_message.lower().startswith('/help'):
                response = await self._get_help_message()
            elif user_message.lower().startswith('/news'):
                query = user_message[5:].strip() or "latest AI policy news"
                response = await self._handle_news_request(query)
            elif user_message.lower().startswith('/report'):
                query = user_message[7:].strip()
                response = await self._handle_report_request(turn_context, query, user_id)
            elif user_message.lower().startswith('/email'):
                response = await self._handle_email_request(user_message, user_id)
            else:
                # Process query through enhanced orchestrator
                response = await self.orchestrator.process_query(context)
            
            # Send response back to Teams
            await self._send_response(turn_context, response)
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Generate contextual error message
            error_response = await self._generate_contextual_error_message(str(e), user_message)
            await turn_context.send_activity(MessageFactory.text(error_response))
    
    async def _send_extended_typing_indicator(self, turn_context: TurnContext) -> None:
        """Send extended typing indicator for complex queries"""
        typing_activity = Activity(
            type=ActivityTypes.typing,
            from_property=turn_context.activity.recipient,
            recipient=turn_context.activity.from_property,
            conversation=turn_context.activity.conversation
        )
        
        # Send multiple typing indicators to show extended processing
        for _ in range(3):
            await turn_context.send_activity(typing_activity)
            await asyncio.sleep(2)
    
    async def _generate_contextual_error_message(self, error: str, user_message: str) -> str:
        """Generate contextual error messages based on the error type and user query"""
        word_count = len(user_message.split())
        is_complex = word_count > 100 or user_message.count('?') > 2
        
        if "rate_limit" in error.lower():
            if is_complex:
                return """
🚧 **High Demand for Complex Analysis**

Your comprehensive query requires significant processing power, and I'm currently experiencing high demand. 

**For complex multi-part questions like yours:**
• Try breaking it into 2-3 separate, focused questions
• Ask one main topic at a time for faster responses
• I'll provide more detailed analysis for focused queries

Please wait 30 seconds and try with a more focused question. I'm here to help! 🚀
                """
            else:
                return """
🚧 **System Temporarily Busy**

I'm experiencing high demand right now. Please wait 30 seconds and try again.

Your question looks straightforward, so it should process quickly once the load decreases! ⏱️
                """
        
        elif "timeout" in error.lower():
            return """
⏱️ **Complex Query Processing**

Your query is quite comprehensive and requires extended analysis time.

**To get faster results:**
• Break multi-part questions into focused queries
• Ask about specific regulations or frameworks one at a time
• I can provide more detailed responses to targeted questions

Try asking about one specific aspect first! 🎯
            """
        
        else:
            return f"""
❌ **Processing Error**

I encountered an unexpected issue while analyzing your query.

**Please try:**
• Rephrasing your question slightly
• Asking about one topic at a time if it's a complex question
• Contacting support if the issue continues

I'm ready to help with your AI governance questions! 💪
            """
    
    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ) -> None:
        """
        Welcome new members to the conversation
        """
        welcome_text = """
🤖 **Welcome to Legal-Mind-AI!**

I'm your AI assistant specializing in AI policy and governance. I can help you with:

• **Policy Analysis** - EU AI Act, NIST frameworks, ISO standards, AIDA, and more
• **Latest News** - Recent developments in AI policy and regulation
• **Document Review** - Analyze and compare policy documents
• **Reports** - Generate comprehensive policy reports

**Quick Commands:**
- `/help` - Show detailed help and examples
- `/news [topic]` - Get latest AI policy news
- `/report [topic]` - Generate a detailed PDF report

Just ask me any question about AI policy, governance, or compliance!
        """
        
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(MessageFactory.text(welcome_text))
    
    async def _send_typing_indicator(self, turn_context: TurnContext) -> None:
        """
        Send typing indicator to show the bot is processing
        """
        typing_activity = Activity(
            type=ActivityTypes.typing,
            from_property=turn_context.activity.recipient,
            recipient=turn_context.activity.from_property,
            conversation=turn_context.activity.conversation
        )
        await turn_context.send_activity(typing_activity)
    
    async def _send_response(self, turn_context: TurnContext, response: str) -> None:
        """
        Send formatted response to Teams
        """
        # Format response for better readability in Teams
        formatted_response = self._format_teams_message(response)
        await turn_context.send_activity(MessageFactory.text(formatted_response))
    
    def _format_teams_message(self, text: str) -> str:
        """
        Format message for optimal display in Teams
        """
        # Add some basic formatting for Teams
        # Replace **bold** with Teams-friendly formatting
        formatted = text.replace("**", "**")
        
        # Add Legal-Mind-AI branding
        if not formatted.startswith("🤖"):
            formatted = f"🤖 **Legal-Mind-AI Response:**\n\n{formatted}"
        
        return formatted
    
    async def _get_help_message(self) -> str:
        """
        Generate comprehensive help message
        """
        return """
🤖 **Legal-Mind-AI Help Guide**

**What I Can Help With:**
• AI policy analysis and interpretation
• Compliance requirements and recommendations
• Latest news and developments in AI governance
• Document analysis and comparison
• Comprehensive policy reports
• Email delivery of analysis and reports

**Example Questions:**
• "What are the key requirements of the EU AI Act for high-risk AI systems?"
• "What's the latest news on AI regulation in the US?"
• "Compare NIST AI Risk Management Framework with ISO/IEC 23053"
• "How do I ensure compliance with biometric surveillance regulations?"

**Special Commands:**
• `/help` - Show this help message
• `/news [topic]` - Get latest AI policy news
  Example: `/news EU AI Act` or just `/news` for general updates
• `/report [topic]` - Generate detailed analysis report
  Example: `/report facial recognition compliance requirements`
• `/email your@email.com [topic]` - Send analysis via email
  Example: `/email john@company.com GDPR AI compliance checklist`

**Tips for Better Results:**
• Be specific in your questions for more targeted responses
• Mention specific frameworks, laws, or standards you're interested in
• Ask follow-up questions to dive deeper into topics
• Use `/news` regularly to stay updated on policy changes
• Request reports for comprehensive analysis suitable for stakeholders

**Coverage Areas:**
• EU AI Act and implementation guidelines
• NIST AI Risk Management Framework
• ISO/IEC AI standards (23053, 23894, etc.)
• Canada's AIDA (Artificial Intelligence and Data Act)
• US AI governance and FTC guidance
• GDPR implications for AI systems
• Sector-specific AI regulations (healthcare, finance, etc.)

I'm here to help you navigate the complex world of AI policy and governance! 🚀

*Note: This is a demo version. Some features like PDF file sharing and advanced email templates will be fully implemented in the production release.*
        """
    
    async def _handle_news_request(self, query: str) -> str:
        """
        Handle news request using the news service
        """
        try:
            news_items = await news_service.get_latest_news(query, hours_back=24, max_items=5)
            
            if not news_items:
                return "I couldn't find any recent news matching your request. Please try a different query or check back later."
            
            response = "📰 **Latest AI Policy News:**\n\n"
            
            for i, item in enumerate(news_items, 1):
                response += f"**{i}. {item.title}**\n"
                response += f"*Source: {item.source}*\n"
                response += f"{item.summary[:200]}...\n"
                response += f"🔗 [Read more]({item.url})\n\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling news request: {str(e)}")
            return "I encountered an error while fetching the latest news. Please try again later."
    
    async def _handle_report_request(self, turn_context: TurnContext, query: str, user_id: str) -> str:
        """
        Handle report generation request
        """
        try:
            if not query.strip():
                return "Please specify what you'd like me to analyze for the report. For example: `/report EU AI Act compliance requirements`"
            
            # Generate report content using orchestrator
            context = QueryContext(
                user_id=user_id,
                query=query,
                priority="normal",
                output_format="pdf"
            )
            
            report_content = await self.orchestrator.process_query(context)
            
            # Generate PDF
            pdf_buffer = report_generator.generate_report(
                title=f"Legal-Mind-AI Analysis: {query}",
                content=report_content,
                user_query=query,
                metadata={
                    "generated_at": "datetime.now().isoformat()",
                    "user_id": user_id,
                    "sources": ["EU AI Act", "NIST Framework", "Legal-Mind-AI Analysis"]
                }
            )
            
            # For now, return text response with note about PDF
            # TODO: Implement file upload to Teams
            response = f"📄 **Report Generated: {query}**\n\n"
            response += report_content
            response += "\n\n*Note: PDF report generation is complete. File sharing will be implemented in the next phase.*"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return "I encountered an error while generating the report. Please try again or simplify your request."
    
    async def _handle_email_request(self, message: str, user_id: str) -> str:
        """
        Handle email-related requests
        """
        try:
            # Parse email command: /email user@example.com topic
            parts = message.split(" ", 2)
            if len(parts) < 3:
                return "Please use the format: `/email your@email.com your question or topic`"
            
            email_address = parts[1]
            query = parts[2]
            
            # Validate email format (basic)
            if "@" not in email_address or "." not in email_address:
                return "Please provide a valid email address."
            
            # Generate response using orchestrator
            context = QueryContext(
                user_id=user_id,
                query=query,
                priority="normal",
                output_format="email",
                email_address=email_address
            )
            
            report_content = await self.orchestrator.process_query(context)
            
            # Send email
            success = await email_service.send_report(
                to_email=email_address,
                subject=f"Legal-Mind-AI Analysis: {query}",
                report_content=report_content
            )
            
            if success:
                return f"✅ I've sent the analysis to {email_address}. Please check your inbox!"
            else:
                return f"❌ I couldn't send the email to {email_address}. Please verify the address or try again later."
                
        except Exception as e:
            logger.error(f"Error handling email request: {str(e)}")
            return "I encountered an error while sending the email. Please try again."

# Bot Framework setup
def create_app() -> web.Application:
    """
    Create and configure the web application
    """
    # Bot Framework settings
    app_id = os.getenv("MICROSOFT_APP_ID")
    app_password = os.getenv("MICROSOFT_APP_PASSWORD")
    
    if not app_id or not app_password:
        logger.error("MICROSOFT_APP_ID and MICROSOFT_APP_PASSWORD must be set")
        sys.exit(1)
    
    settings = BotFrameworkAdapterSettings(app_id, app_password)
    adapter = BotFrameworkAdapter(settings)
    
    # Create bot
    bot = LegalMindBot()
    
    # Error handler
    async def on_error(context: TurnContext, error: Exception):
        logger.error(f"Bot error: {error}")
        await context.send_activity(
            MessageFactory.text("Sorry, an error occurred. Please try again.")
        )
    
    adapter.on_turn_error = on_error
    
    # Message handler
    async def messages(req: Request) -> Response:
        if "application/json" in req.headers["Content-Type"]:
            body = await req.json()
        else:
            return Response(status=415)
        
        activity = Activity().deserialize(body)
        auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""
        
        try:
            response = await adapter.process_activity(activity, auth_header, bot.on_message_activity)
            if response:
                return web.json_response(data=response.body, status=response.status)
            return Response(status=201)
        except Exception as e:
            logger.error(f"Error processing activity: {e}")
            return Response(status=500)
    
    # Create web app
    app = web.Application()
    app.router.add_post("/api/messages", messages)
    
    # Health check endpoint
    async def health(request: Request) -> Response:
        return web.json_response({"status": "healthy", "service": "Legal-Mind-AI"})
    
    app.router.add_get("/health", health)
    
    return app

if __name__ == "__main__":
    try:
        app = create_app()
        port = int(os.getenv("APP_PORT", 3978))
        
        logger.info(f"Starting Legal-Mind-AI bot on port {port}")
        web.run_app(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)
