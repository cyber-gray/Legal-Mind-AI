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

# Import ThreadSession for Azure AI Agents integration
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from thread_session import get_thread_session

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
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@bot_app.ai.action("processLegalQuery")
async def process_legal_query(context: ActionTurnContext[Dict[str, Any]], state: AppTurnState):
    """
    Enhanced multi-agent orchestration using Azure AI Agents Service
    Routes queries to specialized legal AI agents and synthesizes responses.
    """
    try:
        user_query = context.activity.text
        user_id = context.activity.from_property.id if context.activity.from_property else "unknown"
        
        logger.info(f"Processing query from user {user_id}: {user_query}")
        
        # Initialize conversation state
        conversation_id = getattr(state.conversation, "conversation_id", None) or str(uuid.uuid4())
        setattr(state.conversation, "conversation_id", conversation_id)
        conversation_history = getattr(state.conversation, "history", [])
        conversation_history.append(f"User: {user_query}")

        # Get ThreadSession instance
        thread_session = await get_thread_session()
        
        # Enhanced agent selection logic based on query content
        query_lower = user_query.lower()
        selected_agents = []
        
        # Map query patterns to agent types
        agent_patterns = {
            "regulation_analysis": ["regulation", "rule", "law", "statute", "ordinance", "framework", "legal requirement"],
            "risk_scoring": ["risk", "compliance risk", "violation", "penalty", "fine", "assessment", "evaluation"],
            "compliance_expert": ["compliance", "audit", "checklist", "requirement", "standard", "certification"],
            "policy_translation": ["policy", "translate", "explain", "simplify", "understand", "meaning", "interpretation"],
            "comparative_regulatory": ["compare", "comparison", "jurisdiction", "different", "versus", "cross-border", "international"]
        }
        
        for agent_name, patterns in agent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                selected_agents.append(agent_name)
        
        # Default to regulation analysis if no specific patterns match
        if not selected_agents:
            selected_agents = ["regulation_analysis"]
        
        logger.info(f"Selected Azure AI Agents: {selected_agents}")
        
        # Process query through selected agents
        agent_responses = []
        for agent_name in selected_agents:
            try:
                logger.info(f"Querying Azure AI Agent: {agent_name}")
                
                # Process message through Azure AI Agents Service
                response = await thread_session.process_message(
                    user_id=user_id,
                    agent_name=agent_name,
                    message=user_query
                )
                
                if response:
                    agent_responses.append({
                        "agent": agent_name,
                        "content": response,
                        "timestamp": datetime.utcnow().isoformat(),
                        "conversation_id": conversation_id
                    })
                    conversation_history.append(f"{agent_name}: {response}")
                    logger.info(f"Successfully received response from {agent_name}")
                else:
                    logger.warning(f"No response received from agent {agent_name}")
                    
            except Exception as agent_error:
                logger.error(f"Error querying agent {agent_name}: {str(agent_error)}")
                # Continue with other agents even if one fails
                continue
        
        # Synthesize responses if we have multiple agents
        if len(agent_responses) > 1:
            logger.info("Synthesizing multiple agent responses")
            
            # Prepare synthesis input
            agent_summaries = []
            for resp in agent_responses:
                agent_summaries.append(f"**{resp['agent'].replace('_', ' ').title()}:**\n{resp['content']}")
            
            synthesis_input = f"**User Query:** {user_query}\n\n**Specialist Analysis:**\n\n" + "\n\n".join(agent_summaries)
            
            # Use traditional planner for synthesis (fallback)
            try:
                synthesis_response = await planner.model.complete(
                    prompts.get_prompt("coordinator"),
                    input=synthesis_input
                )
                conversation_history.append(f"Coordinator: {synthesis_response}")
                final_response = f"## 🎯 Legal Analysis Summary\n\n{synthesis_response}"
            except Exception as synthesis_error:
                logger.error(f"Synthesis error: {str(synthesis_error)}")
                # Return individual responses if synthesis fails
                final_response = f"## 📋 Legal Analysis\n\n" + "\n\n---\n\n".join([resp['content'] for resp in agent_responses])
        
        elif len(agent_responses) == 1:
            # Single agent response
            final_response = f"## 📋 Legal Analysis\n\n{agent_responses[0]['content']}"
        
        else:
            # No agent responses - fallback to traditional processing
            logger.warning("No agent responses received, falling back to traditional processing")
            final_response = await _fallback_processing(user_query, planner, prompts)
        
        # Save conversation history
        setattr(state.conversation, "history", conversation_history)
        
        logger.info(f"Successfully processed query for user {user_id}")
        return final_response
        
    except Exception as e:
        logger.error(f"Error in process_legal_query: {str(e)}")
        traceback.print_exc()
        return "I'm sorry, I encountered an error while processing your legal query. Please try again or contact support if the issue persists."

async def _fallback_processing(user_query: str, planner, prompts) -> str:
    """Fallback processing when Azure AI Agents are not available"""
    try:
        logger.info("Using fallback processing")
        response = await planner.model.complete(
            prompts.get_prompt("planner"),
            input=user_query
        )
        return f"## 📋 Legal Analysis (Fallback)\n\n{response}\n\n*Note: Azure AI Agents Service unavailable - using fallback processing.*"
    except Exception as e:
        logger.error(f"Fallback processing error: {str(e)}")
        return "I'm sorry, I'm currently unable to process legal queries. Please try again later."

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
