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
    MemoryStorage
)
from botbuilder.schema import Activity

# Import our enhanced orchestrator
from agents.orchestrator import LegalMindOrchestrator, QueryContext

# Load .env with explicit path and override
load_dotenv(override=True, verbose=True)

# === Teams / Bot Framework Setup ===
APP_ID   = os.getenv("MICROSOFT_APP_ID")
APP_PASS = os.getenv("MICROSOFT_APP_PASSWORD")
if not APP_ID or not APP_PASS:
    print("❌ Please set MICROSOFT_APP_ID and MICROSOFT_APP_PASSWORD in your .env")
    sys.exit(1)

settings = BotFrameworkAdapterSettings(APP_ID, APP_PASS)
adapter  = BotFrameworkAdapter(settings)
memory   = MemoryStorage()
conv_st   = ConversationState(memory)

# === Initialize Enhanced Orchestrator ===
orchestrator = LegalMindOrchestrator()

# Check system status on startup
print("🚀 Starting Legal-Mind-AI with Enhanced Search Capabilities")
status = orchestrator.get_system_status()
print("📊 System Status:")
for category, services in status.items():
    print(f"  {category.title()}:")
    for service, enabled in services.items():
        icon = "✅" if enabled else "❌"
        print(f"    {icon} {service}")
print()

async def on_message(context: TurnContext):
    """Enhanced message handler using the orchestrator"""
    text = context.activity.text.strip()
    
    try:
        # Create query context
        query_context = QueryContext(
            user_id=context.activity.from_property.id,
            query=text,
            priority="normal",
            max_response_length=3800,
            enable_chunking=True
        )
        
        # Process using enhanced orchestrator
        response = await orchestrator.process_query(query_context)
        await context.send_activity(response)
        
    except Exception as e:
        error_msg = f"⚠️ Error processing your request: {str(e)}"
        print(f"Error in on_message: {e}")
        await context.send_activity(error_msg)

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
    print(f"Starting enhanced bot on http://localhost:{port}/api/messages")
    web.run_app(app, host="localhost", port=port)
