import os
import sys
import traceback
import json
from typing import Any, Dict, Optional
from dataclasses import asdict

from botbuilder.core import MemoryStorage, TurnContext
from state import AppTurnState
from teams import Application, ApplicationOptions, TeamsAdapter
from teams.ai import AIOptions
from teams.ai.actions import ActionTurnContext
from teams.ai.models import AzureOpenAIModelOptions, OpenAIModel, OpenAIModelOptions
from teams.ai.planners import ActionPlanner, ActionPlannerOptions
from teams.ai.prompts import PromptManager, PromptManagerOptions
from teams.state import TurnState
from teams.feedback_loop_data import FeedbackLoopData


from config import Config
config = Config()

# Create AI components
model = OpenAIModel(
    AzureOpenAIModelOptions(
        api_key=config.AZURE_OPENAI_API_KEY,
        default_model=config.AZURE_OPENAI_MODEL_DEPLOYMENT_NAME,
        endpoint=config.AZURE_OPENAI_ENDPOINT,
    )
)
prompts = PromptManager(PromptManagerOptions(prompts_folder=f"{os.getcwd()}/prompts"))
planner = ActionPlanner(
    ActionPlannerOptions(model=model, prompts=prompts, default_prompt="planner")
)
storage = MemoryStorage()
bot_app = Application[AppTurnState](
    ApplicationOptions(
        bot_app_id=config.APP_ID,
        storage=storage,
        adapter=TeamsAdapter(config),
        ai=AIOptions(planner=planner, enable_feedback_loop=True),
    )
)

# --- Multi-agent orchestration action (experimental logic) ---
import uuid
from typing import List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@bot_app.ai.action("processLegalQuery")
async def process_legal_query(context: ActionTurnContext[Dict[str, Any]], state: AppTurnState):
    """
    Multi-agent orchestration: selects agents, routes query, scores responses, and synthesizes final answer.
    """
    user_query = context.activity.text
    conversation_id = getattr(state.conversation, "conversation_id", None) or str(uuid.uuid4())
    setattr(state.conversation, "conversation_id", conversation_id)
    conversation_history = getattr(state.conversation, "history", [])
    conversation_history.append(f"User: {user_query}")

    # Example agent selection logic (expand as needed)
    agents = ["PolicyAnalyst", "ComplianceExpert", "ResearchAgent", "ComparativeAnalyst"]
    needed_agents = []
    q = user_query.lower()
    if any(k in q for k in ["policy", "regulation", "framework"]):
        needed_agents.append("PolicyAnalyst")
    if any(k in q for k in ["compliance", "violation", "audit"]):
        needed_agents.append("ComplianceExpert")
    if any(k in q for k in ["research", "case law", "statute"]):
        needed_agents.append("ResearchAgent")
    if any(k in q for k in ["compare", "jurisdiction", "difference"]):
        needed_agents.append("ComparativeAnalyst")
    if not needed_agents:
        needed_agents = ["PolicyAnalyst"]

    responses = []
    for agent in needed_agents:
        # Use planner to invoke agent prompt (modular prompt)
        agent_prompt = agent.lower()
        agent_response = await planner.model.complete(
            prompts.get_prompt(agent_prompt),
            input=user_query
        )
        responses.append({
            "agent": agent,
            "content": agent_response,
            "timestamp": datetime.utcnow().isoformat(),
            "conversation_id": conversation_id
        })
        conversation_history.append(f"{agent}: {agent_response}")

    # Synthesis by Coordinator
    synthesis_prompt = f"Based on the specialist analysis above, provide a comprehensive synthesis and final recommendations for: {user_query}"
    synthesis_response = await planner.model.complete(
        prompts.get_prompt("coordinator"),
        input=synthesis_prompt
    )
    conversation_history.append(f"Coordinator: {synthesis_response}")

    # Save history
    setattr(state.conversation, "history", conversation_history)

    # Return synthesized answer
    return synthesis_response

@bot_app.turn_state_factory
async def turn_state_factory(context: TurnContext):
    return await AppTurnState.load(context, storage)

@bot_app.ai.action("createTask")
async def create_task(context: ActionTurnContext[Dict[str, Any]], state: AppTurnState):
    if not state.conversation.tasks:
        state.conversation.tasks = {}
    parameters = state.conversation.planner_history[-1].content.action.parameters
    task = {"title": parameters["title"], "description": parameters["description"]}
    state.conversation.tasks[parameters["title"]] = task
    return f"task created, think about your next action"

@bot_app.ai.action("deleteTask")
async def delete_task(context: ActionTurnContext[Dict[str, Any]], state: AppTurnState):
    if not state.conversation.tasks:
        state.conversation.tasks = {}
    parameters = state.conversation.planner_history[-1].content.action.parameters
    if parameters["title"] not in state.conversation.tasks:
        return "task not found, think about your next action"
    del state.conversation.tasks[parameters["title"]]
    return f"task deleted, think about your next action"
    
@bot_app.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The agent encountered an error or bug.")

@bot_app.feedback_loop()
async def feedback_loop(_context: TurnContext, _state: TurnState, feedback_loop_data: FeedbackLoopData):
    # Add custom feedback process logic here.
    print(f"Your feedback is:\n{json.dumps(asdict(feedback_loop_data), indent=4)}")