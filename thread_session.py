#!/usr/bin/env python3
"""
Azure AI Agents Thread Management for Legal Mind Agent

This module provides thread lifecycle management for Azure AI Agents Service,
including thread creation, message handling, and run processing.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from azure.ai.agents import AgentsClient
    from azure.ai.agents.models import Agent, AgentThread, ThreadMessage, ThreadRun
    from azure.identity import DefaultAzureCredential
    from azure.core.exceptions import HttpResponseError as AzureError
    AZURE_AGENTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Azure AI Agents SDK not available: {e}")
    AZURE_AGENTS_AVAILABLE = False
    # Mock classes for development
    class AgentsClient: pass
    class Agent: pass
    class AgentThread: pass
    class ThreadMessage: pass
    class ThreadRun: pass
    class DefaultAzureCredential: pass
    class AzureError(Exception): pass

logger = logging.getLogger(__name__)

class ThreadSession:
    """
    Azure AI Agents Thread Session Management
    
    Handles the complete lifecycle of agent interactions:
    1. Create/reuse agent threads
    2. Append user messages
    3. Create and process runs
    4. Retrieve assistant responses
    """
    
    def __init__(self, endpoint: Optional[str] = None, credential: Optional[Any] = None):
        """
        Initialize ThreadSession with Azure AI Agents client
        
        Args:
            endpoint: Azure AI Agents service endpoint
            credential: Azure credential for authentication
        """
        self.endpoint = endpoint or os.getenv("AZURE_AI_AGENTS_ENDPOINT")
        self.credential = credential or DefaultAzureCredential()
        
        if not AZURE_AGENTS_AVAILABLE:
            logger.warning("Azure AI Agents SDK not available - using mock responses")
            self.client = None
        elif not self.endpoint:
            logger.warning("Azure AI Agents endpoint not configured - using mock responses")
            self.client = None
        else:
            # Initialize the Azure AI Agents client
            self.client = AgentsClient(
                endpoint=self.endpoint,
                credential=self.credential
            )
        
        # Agent and thread caches
        self._agents_cache: Dict[str, str] = {}  # agent_name -> agent_id
        self._threads_cache: Dict[str, str] = {}  # user_agent_key -> thread_id
        self._manifest_path = Path(__file__).parent / "agents_manifest.json"
        
        # Initialize legal research tools (lazy loading to avoid circular imports)
        self.legal_tools = None
        
        logger.info(f"ThreadSession initialized with endpoint: {self.endpoint}")
    
    def _get_legal_tools(self):
        """Get legal tools instance (lazy loading)"""
        if self.legal_tools is None:
            try:
                from legal_tools import get_legal_tools
                self.legal_tools = get_legal_tools()
            except ImportError:
                logger.warning("Legal tools not available")
                self.legal_tools = None
        return self.legal_tools
    
    async def process_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a tool call from an agent
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result or None if failed
        """
        try:
            legal_tools = self._get_legal_tools()
            if not legal_tools:
                return {"error": "Legal tools not available"}
            
            if tool_name == "vector_search":
                return await legal_tools.vector_search(**arguments)
            elif tool_name == "deep_research":
                return await legal_tools.deep_research(**arguments)
            elif tool_name == "compliance_checker":
                return await legal_tools.compliance_checker(**arguments)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Tool call error ({tool_name}): {str(e)}")
            return {"error": str(e)}
    
    async def initialize_agents(self) -> Dict[str, str]:
        """
        Initialize all agents from the manifest file
        
        Returns:
            Dict mapping agent names to their IDs
        """
        try:
            if not AZURE_AGENTS_AVAILABLE or not self.client:
                logger.warning("Azure AI Agents not available - returning mock agent IDs")
                return {
                    "regulation_analysis": "mock-reg-agent-id",
                    "risk_scoring": "mock-risk-agent-id", 
                    "compliance_expert": "mock-compliance-agent-id",
                    "policy_translation": "mock-policy-agent-id",
                    "comparative_regulatory": "mock-comparative-agent-id"
                }
            
            # Load agents manifest
            manifest = self._load_agents_manifest()
            agent_ids = {}
            
            for agent_name, agent_config in manifest["agents"].items():
                # Check if agent already exists
                if agent_config.get("id"):
                    logger.info(f"Agent {agent_name} already exists: {agent_config['id']}")
                    agent_ids[agent_name] = agent_config["id"]
                    self._agents_cache[agent_name] = agent_config["id"]
                    continue
                
                # Create new agent
                logger.info(f"Creating agent: {agent_name}")
                agent_id = await self._create_agent(agent_name, agent_config)
                
                if agent_id:
                    agent_ids[agent_name] = agent_id
                    self._agents_cache[agent_name] = agent_id
                    
                    # Update manifest with agent ID
                    agent_config["id"] = agent_id
                    agent_config["created_at"] = datetime.utcnow().isoformat()
                    
                    logger.info(f"Successfully created agent {agent_name}: {agent_id}")
                else:
                    logger.error(f"Failed to create agent: {agent_name}")
            
            # Save updated manifest
            if agent_ids:
                manifest["metadata"]["updated_at"] = datetime.utcnow().isoformat()
                self._save_agents_manifest(manifest)
            
            logger.info(f"Initialized {len(agent_ids)} agents: {list(agent_ids.keys())}")
            return agent_ids
            
        except Exception as e:
            logger.exception(f"Error initializing agents: {e}")
            return {}
    
    async def create_thread_session(self, user_id: str, agent_name: str) -> Optional[str]:
        """
        Create a new thread session for a user and agent
        
        Args:
            user_id: Unique identifier for the user
            agent_name: Name of the agent to interact with
            
        Returns:
            Thread ID if successful, None otherwise
        """
        try:
            if not AZURE_AGENTS_AVAILABLE or not self.client:
                # Return mock thread ID
                thread_id = f"mock-thread-{user_id}-{agent_name}"
                thread_key = f"{user_id}_{agent_name}"
                self._threads_cache[thread_key] = thread_id
                return thread_id
            
            # Get agent ID
            agent_id = await self._get_agent_id(agent_name)
            if not agent_id:
                logger.error(f"Agent not found: {agent_name}")
                return None
            
            # Create thread using the actual SDK method
            # Note: Actual implementation would depend on the SDK's API
            thread = self.client.create_thread()
            
            # Cache thread with composite key
            thread_key = f"{user_id}_{agent_name}"
            self._threads_cache[thread_key] = thread.id
            
            logger.info(f"Created thread session: {thread.id} for user {user_id} with agent {agent_name}")
            return thread.id
            
        except AzureError as e:
            logger.error(f"Azure error creating thread session: {e}")
            return None
        except Exception as e:
            logger.exception(f"Error creating thread session: {e}")
            return None
    
    async def process_message(self, user_id: str, agent_name: str, message: str, thread_id: Optional[str] = None) -> Optional[str]:
        """
        Process a user message through an agent
        
        Args:
            user_id: User identifier
            agent_name: Agent to process the message
            message: User message content
            thread_id: Existing thread ID (optional)
            
        Returns:
            Agent response if successful, None otherwise
        """
        try:
            if not AZURE_AGENTS_AVAILABLE or not self.client:
                # Return mock response based on agent type
                return await self._get_mock_response(agent_name, message)
            
            # Get or create thread
            if not thread_id:
                thread_id = await self.create_thread_session(user_id, agent_name)
                if not thread_id:
                    return None
            
            # Get agent ID
            agent_id = await self._get_agent_id(agent_name)
            if not agent_id:
                logger.error(f"Agent not found: {agent_name}")
                return None
            
            # Add user message to thread
            self.client.create_message(
                thread_id=thread_id,
                role="user",
                content=message
            )
            
            # Create and process run
            run = self.client.create_run(
                thread_id=thread_id,
                assistant_id=agent_id
            )
            
            # Wait for run completion
            completed_run = await self._wait_for_run_completion(thread_id, run.id)
            if not completed_run:
                logger.error("Run did not complete successfully")
                return None
            
            # Retrieve assistant response
            response = await self._get_latest_assistant_message(thread_id)
            
            logger.info(f"Successfully processed message for user {user_id} with agent {agent_name}")
            return response
            
        except AzureError as e:
            logger.error(f"Azure error processing message: {e}")
            return None
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            return None
    
    async def _create_agent(self, agent_name: str, agent_config: Dict[str, Any]) -> Optional[str]:
        """Create an agent with the specified configuration"""
        try:
            if not AZURE_AGENTS_AVAILABLE or not self.client:
                return f"mock-{agent_name}-id"
            
            # Create agent using actual SDK
            # Note: Actual implementation would depend on the SDK's API
            agent = self.client.create_agent(
                model=agent_config.get("model", "gpt-4"),
                name=agent_config["name"],
                description=agent_config["description"],
                instructions=agent_config["instructions"],
                tools=agent_config.get("tools", [])
            )
            
            return agent.id
            
        except AzureError as e:
            logger.error(f"Azure error creating agent {agent_name}: {e}")
            return None
        except Exception as e:
            logger.exception(f"Error creating agent {agent_name}: {e}")
            return None
    
    async def _get_agent_id(self, agent_name: str) -> Optional[str]:
        """Get agent ID from cache or manifest"""
        try:
            # Check cache first
            if agent_name in self._agents_cache:
                return self._agents_cache[agent_name]
            
            # Load from manifest
            manifest = self._load_agents_manifest()
            agent_config = manifest["agents"].get(agent_name)
            if agent_config and agent_config.get("id"):
                self._agents_cache[agent_name] = agent_config["id"]
                return agent_config["id"]
            
            logger.warning(f"Agent ID not found for: {agent_name}")
            return None
            
        except Exception as e:
            logger.exception(f"Error getting agent ID for {agent_name}: {e}")
            return None
    
    async def _wait_for_run_completion(self, thread_id: str, run_id: str, timeout: int = 60) -> Optional[Any]:
        """Wait for a run to complete with timeout"""
        try:
            if not AZURE_AGENTS_AVAILABLE:
                await asyncio.sleep(1)  # Simulate processing time
                return {"status": "completed"}
            
            start_time = asyncio.get_event_loop().time()
            
            while True:
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.error(f"Run {run_id} timed out after {timeout} seconds")
                    return None
                
                # Get run status
                run = self.client.get_run(thread_id=thread_id, run_id=run_id)
                
                if run.status == "completed":
                    return run
                elif run.status in ["failed", "cancelled", "expired"]:
                    logger.error(f"Run {run_id} ended with status: {run.status}")
                    return None
                
                # Wait before checking again
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.exception(f"Error waiting for run completion: {e}")
            return None
    
    async def _get_latest_assistant_message(self, thread_id: str) -> Optional[str]:
        """Retrieve the latest assistant message from a thread"""
        try:
            if not AZURE_AGENTS_AVAILABLE:
                return "Mock assistant response from Azure AI Agents Service."
            
            messages = self.client.list_messages(thread_id=thread_id)
            
            # Find the most recent assistant message
            for message in messages.data:
                if message.role == "assistant":
                    # Extract text content
                    if message.content and len(message.content) > 0:
                        content = message.content[0]
                        if hasattr(content, 'text') and hasattr(content.text, 'value'):
                            return content.text.value
            
            logger.warning(f"No assistant message found in thread {thread_id}")
            return None
            
        except Exception as e:
            logger.exception(f"Error getting latest assistant message: {e}")
            return None
    
    async def _get_mock_response(self, agent_name: str, message: str) -> str:
        """Generate mock response for development/testing"""
        responses = {
            "regulation_analysis": f"📋 **Regulation Analysis Agent (Mock)**\n\n**Query:** {message}\n\n**Mock Analysis:** This is a simulated response for regulation analysis. In production, this would be powered by Azure AI Agents Service with real regulatory expertise.\n\n*Configure AZURE_AI_AGENTS_ENDPOINT to enable real agent responses.*",
            "risk_scoring": f"🔍 **Risk Scoring Agent (Mock)**\n\n**Query:** {message}\n\n**Mock Risk Assessment:** This is a simulated risk scoring response. Production version would provide real compliance risk analysis.\n\n*Configure Azure AI Agents Service for actual risk scoring.*",
            "compliance_expert": f"✅ **Compliance Expert Agent (Mock)**\n\n**Query:** {message}\n\n**Mock Compliance Guidance:** This is a simulated compliance response. Real implementation would provide detailed compliance checklists and guidance.\n\n*Enable Azure AI Agents Service for production compliance expertise.*",
            "policy_translation": f"📖 **Policy Translation Agent (Mock)**\n\n**Query:** {message}\n\n**Mock Translation:** This is a simulated policy translation. Production version would convert complex regulations into actionable guidance.\n\n*Configure Azure AI Agents for real policy translation.*",
            "comparative_regulatory": f"⚖️ **Comparative Regulatory Agent (Mock)**\n\n**Query:** {message}\n\n**Mock Comparison:** This is a simulated regulatory comparison. Real implementation would provide cross-jurisdictional analysis.\n\n*Enable Azure AI Agents Service for actual comparative analysis.*"
        }
        
        return responses.get(agent_name, f"**Mock Agent Response**\n\n{message}\n\n*Configure Azure AI Agents Service for production responses.*")
    
    def _load_agents_manifest(self) -> Dict[str, Any]:
        """Load agents configuration from manifest file"""
        try:
            if not self._manifest_path.exists():
                raise FileNotFoundError(f"Agents manifest not found: {self._manifest_path}")
            
            with open(self._manifest_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.exception(f"Error loading agents manifest: {e}")
            raise
    
    def _save_agents_manifest(self, manifest: Dict[str, Any]) -> None:
        """Save agents configuration to manifest file"""
        try:
            with open(self._manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
                
        except Exception as e:
            logger.exception(f"Error saving agents manifest: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            # Clear caches
            self._agents_cache.clear()
            self._threads_cache.clear()
            
            logger.info("ThreadSession cleanup completed")
            
        except Exception as e:
            logger.exception(f"Error during cleanup: {e}")

# Global thread session instance
_thread_session: Optional[ThreadSession] = None

async def get_thread_session() -> ThreadSession:
    """Get or create the global ThreadSession instance"""
    global _thread_session
    
    if _thread_session is None:
        _thread_session = ThreadSession()
        # Initialize agents on first use
        await _thread_session.initialize_agents()
    
    return _thread_session
