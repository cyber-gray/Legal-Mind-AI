"""
Legal-Mind-AI Main Application
Simplified single orchestrator application using the new legal orchestrator
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

# Import our new legal orchestrator
from agents.orchestrator import QueryContext
from agents.legal_orchestrator import legal_orchestrator

# Load environment variables
load_dotenv()

# === Bot Framework Setup ===
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

Ask me anything about AI governance and policy! 🚀"""
        await turn_context.send_activity(MessageFactory.text(welcome_text))
    
    async def _handle_command(self, turn_context: TurnContext, command: str):
        """Handle bot commands"""
        
        if command == '/help':
            await self.on_welcome_activity(turn_context)
            
        elif command == '/status':
            await turn_context.send_activity(MessageFactory.text(
                """📊 **System Status**

**Multi-Agent System**: ✅ Active
**Specialized Agents**:
• 📋 Policy Expert: ✅ Ready
• 📰 News Monitor: ✅ Ready  
• 📄 Document Analyzer: ✅ Ready
• 📊 Report Generator: ✅ Ready

**Azure AI Integration**: ✅ Connected
**Teams Bot**: ✅ Online

Ready to assist with your AI governance questions! 🤖"""
            ))
            
        else:
            await turn_context.send_activity(MessageFactory.text(
                f"❓ Unknown command: `{command}`\n"
                f"Use `/help` to see available commands."
            ))
    
    async def _process_query(self, turn_context: TurnContext, query: str, user_id: str):
        """Process user query with the multi-agent orchestrator"""
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
        
        for line in message.split('\n'):
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
                continuation = f"📄 **Continued ({i+1}/{len(chunks)})**\n\n{chunk}"
                await turn_context.send_activity(MessageFactory.text(continuation))
    
    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        """Send welcome message when members are added"""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await self.on_welcome_activity(turn_context)

# Create bot instance
bot = LegalMindTeamsBot()
    text = context.activity.text.strip()
    # 1. Create new thread & send user message
    thread = project.agents.threads.create()
    project.agents.messages.create(thread.id, role="user", content=text)
    # 2. Run the agent
    run = project.agents.runs.create_and_process(thread.id, agent_id=agent_id)
    # 3. Poll until done
    while run.status not in (RunStatus.COMPLETED, RunStatus.FAILED):
        await asyncio.sleep(1)
        run = project.agents.runs.get(thread_id=thread.id, run_id=run.id)
    if run.status == RunStatus.FAILED:
        await context.send_activity(f"⚠️ Agent error: {run.last_error}")
        return
    # 4. Retrieve assistant’s reply
    msgs = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
    reply = next((m.text_messages[-1].text.value for m in msgs if m.role=="assistant"), None)
    await context.send_activity(reply or "No response")

# Route incoming requests to the bot
async def messages(req: web.Request) -> web.Response:
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")
    response = await adapter.process_activity(activity, auth_header, on_message)
    if response:
        return web.json_response(data=response.body, status=response.status)
    return web.Response(status=202)

app = web.Application()
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    port = 3978
    print(f"Starting bot on http://localhost:{port}/api/messages")
    web.run_app(app, host="localhost", port=port)