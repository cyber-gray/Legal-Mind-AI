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

# Load .env
load_dotenv()

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

# === Azure AI Project & Agent Setup ===
project_endpoint = os.getenv("AZURE_PROJECT_ENDPOINT")
agent_id         = os.getenv("AZURE_AGENT_ID")
credential       = DefaultAzureCredential()
project          = AIProjectClient(endpoint=project_endpoint, credential=credential)

async def on_message(context: TurnContext):
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