"""
Legal-Mind-AI Teams Bot Application
Enhanced Teams Bot with dual orchestrator support
"""

import os
import sys
import json
import time
import asyncio
from dotenv import load_dotenv
from aiohttp import web

from botbuilder.core import (
    BotFrameworkAdapterSettings,
    TurnContext,
    BotFrameworkAdapter,
    ConversationState,
    MemoryStorage,
    ActivityHandler,
    MessageFactory
)
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount

# Import our enhanced orchestrator
from agents.orchestrator import QueryContext
from agents.legal_orchestrator import legal_orchestrator

# Load environment variables
load_dotenv()

# === Teams / Bot Framework Setup ===
APP_ID = os.getenv("MICROSOFT_APP_ID", "")
APP_PASS = os.getenv("MICROSOFT_APP_PASSWORD", "")

# For development/testing, allow empty credentials 
if not APP_ID or not APP_PASS:
    print("⚠️  Bot Framework credentials not found. Running in development mode.")
    APP_ID = ""
    APP_PASS = ""

print(f"🔧 Bot Configuration:")
print(f"   App ID: {APP_ID if APP_ID else 'Development Mode (Empty)'}")
print(f"   App Password: {'*' * len(APP_PASS) if APP_PASS else 'Development Mode (Empty)'}")

settings = BotFrameworkAdapterSettings(APP_ID, APP_PASS)

# For development, allow unauthenticated requests
if not APP_ID and not APP_PASS:
    settings.app_id = ""
    settings.app_password = ""
adapter = BotFrameworkAdapter(settings)
memory = MemoryStorage()
conv_state = ConversationState(memory)

# === Enhanced Teams Bot Class ===
class LegalMindTeamsBot(ActivityHandler):
    """Legal-Mind-AI Teams Bot with multi-agent orchestration"""
    
    def __init__(self):
        super().__init__()
        
    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming messages"""
        user_id = turn_context.activity.from_property.id
        text = turn_context.activity.text.strip() if turn_context.activity.text else ""
        
        # Handle bot commands
        if text.lower().startswith('/'):
            return await self._handle_command(turn_context, text.lower())
        
        # Process regular queries
        await self._process_query(turn_context, text, user_id)
    
    async def on_welcome_activity(self, turn_context: TurnContext):
        """Send welcome message when bot is added to conversation"""
        welcome_text = """🤖 **Welcome to Legal-Mind-AI v2.0!**

I'm your AI-powered multi-agent assistant for AI policy, governance, and compliance guidance.

**What I can help with:**
• **Policy Analysis**: EU AI Act, NIST Framework, GDPR compliance
• **Latest News**: Real-time AI regulation updates
• **Document Analysis**: Legal document review and insights
• **Report Generation**: Compliance reports and summaries

**Specialized Agents:**
• 📋 **Policy Expert**: Regulatory guidance and compliance
• 📰 **News Monitor**: Latest AI policy developments  
• 📄 **Document Analyzer**: Legal document insights
• 📊 **Report Generator**: Compliance documentation

**Commands:**
• `/help` - Show this help message
• `/status` - Check system status

**Example queries:**
• "What are the key requirements of the EU AI Act?"
• "Latest news on AI regulation"
• "Generate a compliance report for high-risk AI systems"
• "Analyze this AI governance framework"

Ask me anything about AI governance and policy! 🚀"""

        await turn_context.send_activity(MessageFactory.text(welcome_text))
    
    async def _handle_command(self, turn_context: TurnContext, command: str):
        """Handle bot commands"""
        user_id = turn_context.activity.from_property.id
        
        if command == '/help':
            await self.on_welcome_activity(turn_context)
            
        elif command == '/status':
            status_message = f"""📊 **Legal-Mind-AI System Status**

**User:** `{user_id}`
**Orchestrator:** **Multi-Agent System**
**Status:** ✅ Active

**Available Agents:**
• 📋 Policy Expert - AI regulations and compliance
• 📰 News Monitor - Latest policy developments
• 📄 Document Analyzer - Legal document insights
• 📊 Report Generator - Compliance reports

**System Status:** 🟢 All agents operational
**Version:** 2.0 (Multi-Agent Architecture)"""

            await turn_context.send_activity(MessageFactory.text(status_message))
            
        else:
            await turn_context.send_activity(MessageFactory.text(
                f"❓ **Unknown command:** `{command}`\n\n"
                f"Use `/help` to see available commands."
            ))
    
    async def _process_query(self, turn_context: TurnContext, query: str, user_id: str):
        """Process user query with the new legal orchestrator"""
        if not query.strip():
            await turn_context.send_activity(MessageFactory.text(
                "💬 Please ask me a question about AI policy or governance!\n\n"
                "Use `/help` to see what I can help with."
            ))
            return
            
        try:
            # Show typing indicator
            await turn_context.send_activity(MessageFactory.text("🤔 Analyzing your query..."))
            
            # Create query context
            context = QueryContext(
                user_id=user_id,
                query=query,
                priority="normal",
                output_format="text"
            )
            
            # Process with the new legal orchestrator
            response = await legal_orchestrator.process_query(context)
            
            # Format response for Teams
            formatted_response = self._format_teams_response(response, "Legal-Mind Multi-Agent", query)
            
            # Send response (Teams has a message limit, so we might need to split)
            await self._send_long_message(turn_context, formatted_response)
            
        except Exception as e:
            error_message = f"""❌ **Error Processing Query**

{str(e)}

💡 **Troubleshooting:**
• Try rephrasing your question
• Use `/help` for guidance
• Ask about specific AI policies or regulations"""

            await turn_context.send_activity(MessageFactory.text(error_message))
    
    def _format_teams_response(self, response: str, orchestrator_name: str, query: str) -> str:
        """Format response for better Teams display"""
        # Clean up the response
        response = response.strip()
        
        # Add header with orchestrator info
        formatted = f"🤖 **Legal-Mind-AI** _{orchestrator_name}_\n\n"
        formatted += response
        
        # Add footer
        formatted += f"\n\n---\n_💡 Multi-agent system • More help: `/help` • Status: `/status`_"
        
        return formatted
    
    async def _send_long_message(self, turn_context: TurnContext, message: str, max_length: int = 28000):
        """Send long messages by splitting them if necessary"""
        if len(message) <= max_length:
            await turn_context.send_activity(MessageFactory.text(message))
            return
        
        # Split message into chunks
        chunks = []
        current_chunk = ""
        
        lines = message.split('\n')
        for line in lines:
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Send chunks
        for i, chunk in enumerate(chunks):
            if i == 0:
                await turn_context.send_activity(MessageFactory.text(chunk))
            else:
                await turn_context.send_activity(MessageFactory.text(f"**Continued...** _(Part {i+1})_\n\n{chunk}"))
    
    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        """Send welcome message when members are added"""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await self.on_welcome_activity(turn_context)

# Create bot instance
bot = LegalMindTeamsBot()

# Bot message handler
async def on_message(turn_context: TurnContext):
    """Message handler for Bot Framework"""
    await bot.on_message_activity(turn_context)

# Web server endpoints
async def messages(req: web.Request) -> web.Response:
    """Handle incoming Teams messages"""
    try:
        print(f"📩 Received request: {req.method} {req.path}")
        print(f"📋 Headers: {dict(req.headers)}")
        
        if "application/json" not in req.headers.get("content-type", ""):
            print("❌ Invalid content type")
            return web.Response(status=415, text="Unsupported Media Type")

        body = await req.json()
        print(f"📦 Body: {json.dumps(body, indent=2)}")
        
        activity = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")
        
        print(f"🔐 Auth header present: {bool(auth_header)}")
        print(f"🎯 Activity type: {activity.type}")
        print(f"💬 Activity text: {activity.text}")

        response = await adapter.process_activity(activity, auth_header, on_message)
        print(f"✅ Bot response: {response}")
        
        if response:
            return web.json_response(data=response.body, status=response.status)
        return web.Response(status=201)
        
    except Exception as e:
        print(f"❌ Error processing activity: {e}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        return web.Response(status=500, text=f"Internal Server Error: {str(e)}")

async def health_check(req: web.Request) -> web.Response:
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "Legal-Mind-AI Teams Bot",
        "version": "2.0",
        "timestamp": time.time(),
        "orchestrator": "multi-agent",
        "agents": list(legal_orchestrator.agents.keys()),
        "endpoints": {
            "messages": "/api/messages",
            "health": "/health"
        }
    })

async def bot_info(req: web.Request) -> web.Response:
    """Bot information endpoint"""
    return web.json_response({
        "name": "Legal-Mind-AI",
        "version": "2.0",
        "architecture": "Multi-Agent Orchestration",
        "description": "AI-powered multi-agent assistant for AI policy, governance, and compliance guidance",
        "features": [
            "Multi-agent orchestration system",
            "Specialized AI policy agents",
            "EU AI Act compliance guidance",
            "NIST AI Risk Management Framework",
            "Real-time AI regulation news",
            "Document analysis and insights",
            "Compliance report generation",
            "Intelligent query routing"
        ],
        "agents": [
            "Policy Expert - AI regulations and compliance",
            "News Monitor - Latest policy developments", 
            "Document Analyzer - Legal document insights",
            "Report Generator - Compliance reports"
        ],
        "commands": [
            "/help - Show help message",
            "/status - Check system status"
        ]
    })

# Create web application
app = web.Application()
app.router.add_post("/api/messages", messages)
app.router.add_get("/health", health_check)
app.router.add_get("/", bot_info)
app.router.add_get("/info", bot_info)

if __name__ == "__main__":
    try:
        port = int(os.getenv("APP_PORT", "3978"))
        print(f"\n🚀 Starting Legal-Mind-AI Teams Bot v2.0")
        print(f"=" * 50)
        print(f"📱 Port: {port}")
        print(f"🔑 Bot Framework App ID: {APP_ID}")
        print(f"🌐 Health check: http://localhost:{port}/health")
        print(f"💬 Teams endpoint: http://localhost:{port}/api/messages")
        print(f"📊 Bot info: http://localhost:{port}/info")
        
        print(f"\n🤖 Bot Features:")
        print(f"   • Multi-agent orchestration system")
        print(f"   • Specialized AI policy agents")
        print(f"   • Real-time news monitoring")
        print(f"   • Document analysis capabilities")
        print(f"   • Compliance report generation")
        
        print(f"\n💡 Teams Commands:")
        print(f"   /help - Show help message")
        print(f"   /status - Check system status")
        
        print(f"\n🔧 Environment:")
        print(f"   • Python: {sys.version}")
        print(f"   • Working directory: {os.getcwd()}")
        
        print(f"\n✅ Ready to serve Teams messages!")
        print(f"=" * 50)
        
        web.run_app(app, host="0.0.0.0", port=port)
        
    except KeyboardInterrupt:
        print("\n👋 Legal-Mind-AI Teams Bot stopped")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)
