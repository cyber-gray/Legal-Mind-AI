import os
import sys
import json
import time
import asyncio
from dotenv import load_dotenv
from aiohttp import web

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder, RunStatus
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

# Import our enhanced orchestrators
from agents.orchestrator import orchestrator, QueryContext
from agents.semantic_orchestrator import semantic_orchestrator

# Load .env
load_dotenv()

# === Teams / Bot Framework Setup ===
APP_ID   = os.getenv("MICROSOFT_APP_ID")
APP_PASS = os.getenv("MICROSOFT_APP_PASSWORD")
if not APP_ID or not APP_PASS:
    print("❌ Please set MICROSOFT_APP_ID and MICROSOFT_APP_PASSWORD in your .env")
    print("💡 For testing, you can use placeholder values to test locally")
    # Use placeholder values for local testing
    APP_ID = "test-app-id"
    APP_PASS = "test-app-password"

settings = BotFrameworkAdapterSettings(APP_ID, APP_PASS)
adapter  = BotFrameworkAdapter(settings)
memory   = MemoryStorage()
conv_st   = ConversationState(memory)

# === Enhanced Teams Bot Class ===
class LegalMindTeamsBot(ActivityHandler):
    """Enhanced Legal-Mind-AI Teams Bot with dual orchestrator support"""
    
    def __init__(self):
        self.user_preferences = {}  # Store user preferences
        
    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming messages"""
        user_id = turn_context.activity.from_property.id
        text = turn_context.activity.text.strip()
        
        # Handle bot commands
        if text.lower().startswith('/'):
            return await self._handle_command(turn_context, text.lower())
        
        # Process regular queries
        await self._process_query(turn_context, text, user_id)
    
    async def on_welcome_activity(self, turn_context: TurnContext):
        """Send welcome message when bot is added to conversation"""
        welcome_text = """
🤖 **Welcome to Legal-Mind-AI v2.0!**

I'm your AI-powered assistant for AI policy, governance, and compliance guidance.

**What I can help with:**
• EU AI Act compliance requirements
• NIST AI Risk Management Framework
• Latest AI regulation news
• Policy analysis and recommendations
• Compliance report generation

**Commands:**
• `/help` - Show this help message
• `/semantic` - Switch to Semantic Kernel orchestrator
• `/original` - Switch to original orchestrator
• `/status` - Check current settings

**Example queries:**
• "What are the key requirements of the EU AI Act?"
• "Latest news on AI regulation"
• "Generate a compliance report for high-risk AI systems"

Ask me anything about AI governance and policy! 🚀
"""
        await turn_context.send_activity(MessageFactory.text(welcome_text))
    
    async def _handle_command(self, turn_context: TurnContext, command: str):
        """Handle bot commands"""
        user_id = turn_context.activity.from_property.id
        
        if command == '/help':
            await self.on_welcome_activity(turn_context)
            
        elif command == '/semantic':
            self.user_preferences[user_id] = {'orchestrator': 'semantic'}
            await turn_context.send_activity(MessageFactory.text(
                "✅ Switched to **Semantic Kernel orchestrator**\n"
                "Enhanced plugin-based routing and intelligent query planning enabled!"
            ))
            
        elif command == '/original':
            self.user_preferences[user_id] = {'orchestrator': 'original'}
            await turn_context.send_activity(MessageFactory.text(
                "✅ Switched to **Original orchestrator**\n"
                "Classic multi-agent system enabled!"
            ))
            
        elif command == '/status':
            prefs = self.user_preferences.get(user_id, {'orchestrator': 'original'})
            orchestrator_type = prefs['orchestrator']
            await turn_context.send_activity(MessageFactory.text(
                f"📊 **Current Settings:**\n"
                f"• Orchestrator: **{orchestrator_type.title()}**\n"
                f"• User ID: `{user_id}`\n\n"
                f"Use `/semantic` or `/original` to switch orchestrators."
            ))
            
        else:
            await turn_context.send_activity(MessageFactory.text(
                f"❓ Unknown command: `{command}`\n"
                f"Use `/help` to see available commands."
            ))
    
    async def _process_query(self, turn_context: TurnContext, query: str, user_id: str):
        """Process user query with selected orchestrator"""
        try:
            # Show typing indicator
            await turn_context.send_activity(MessageFactory.text("🤔 Analyzing your query..."))
            
            # Get user's orchestrator preference
            prefs = self.user_preferences.get(user_id, {'orchestrator': 'original'})
            use_semantic = prefs['orchestrator'] == 'semantic'
            
            # Create query context
            context = QueryContext(
                user_id=user_id,
                query=query,
                priority="normal",
                output_format="text"
            )
            
            # Select orchestrator
            if use_semantic:
                orchestrator_name = "Semantic Kernel"
                selected_orchestrator = semantic_orchestrator
            else:
                orchestrator_name = "Original"
                selected_orchestrator = orchestrator
            
            # Process query
            response = await selected_orchestrator.process_query(context)
            
            # Format response for Teams
            formatted_response = self._format_teams_response(response, orchestrator_name)
            
            # Send response
            await turn_context.send_activity(MessageFactory.text(formatted_response))
            
        except Exception as e:
            error_message = f"❌ **Error Processing Query**\n\n{str(e)}\n\nPlease try rephrasing your question or use `/help` for guidance."
            await turn_context.send_activity(MessageFactory.text(error_message))
    
    def _format_teams_response(self, response: str, orchestrator_name: str) -> str:
        """Format response for better Teams display"""
        # Add header with orchestrator info
        formatted = f"🤖 **Legal-Mind-AI** _{orchestrator_name} Orchestrator_\n\n"
        formatted += response
        
        # Add footer
        formatted += f"\n\n---\n_💡 Use `/semantic` or `/original` to switch orchestrators • `/help` for commands_"
        
        return formatted
    
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