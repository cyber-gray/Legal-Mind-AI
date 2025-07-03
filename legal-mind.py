# legal-mind.py

import os
import sys
import time
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder, RunStatus  # import RunStatus

def main():
    load_dotenv()
    project_endpoint = os.getenv("AZURE_PROJECT_ENDPOINT")
    agent_id         = os.getenv("AZURE_AGENT_ID")

    if not project_endpoint or not agent_id:
        print("❌ Please set AZURE_PROJECT_ENDPOINT and AZURE_AGENT_ID in your .env")
        sys.exit(1)

    credential = DefaultAzureCredential()
    project    = AIProjectClient(endpoint=project_endpoint, credential=credential)

    agent = project.agents.get_agent(agent_id)
    print(f"✅ Connected to agent: {agent.id}")

    thread = project.agents.threads.create()
    print(f"🆕 Created thread: {thread.id}")

    user_question = "What does the EU AI Act say about biometric surveillance?"
    project.agents.messages.create(thread.id, role="user", content=user_question)
    print(f"📤 User: {user_question}")

    run = project.agents.runs.create_and_process(thread.id, agent_id=agent.id)

    # Poll until COMPLETED or FAILED
    while run.status not in (RunStatus.COMPLETED, RunStatus.FAILED):
        print(f"⏳ Run status: {run.status}... waiting")
        time.sleep(1)
        run = project.agents.runs.get(thread_id=thread.id, run_id=run.id)

    if run.status == RunStatus.FAILED:
        print(f"❌ Run failed: {run.last_error}")
        sys.exit(1)

    # At this point run.status == RunStatus.COMPLETED
    messages = project.agents.messages.list(
        thread_id=thread.id,
        order=ListSortOrder.ASCENDING
    )
    for m in messages:
        if m.role == "assistant" and m.text_messages:
            print("🤖 Assistant:", m.text_messages[-1].text.value)

if __name__ == "__main__":
    main()