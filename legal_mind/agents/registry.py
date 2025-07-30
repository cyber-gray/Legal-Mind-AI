#!/usr/bin/env python3
"""
Agent Registry for Legal Mind Agent

Manages the registration, configuration, and lifecycle of specialized
legal AI agents for regulatory compliance analysis.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Registry for managing specialized legal AI agents
    
    Coordinates between different agent types:
    - Regulation Analysis Agent
    - Risk Scoring Agent  
    - Compliance Expert Agent
    - Policy Translation Agent
    - Comparative Regulatory Agent
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the agent registry
        
        Args:
            config_path: Optional path to agent configuration file
        """
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.active_sessions: Dict[str, Any] = {}
        
        # Load agent configurations
        self._load_agent_configurations(config_path)
        
        logger.info(f"Agent Registry initialized with {len(self.agents)} agent types")
    
    def _load_agent_configurations(self, config_path: Optional[str] = None) -> None:
        """Load agent configurations from manifest or default setup"""
        try:
            # Try to load from agents_manifest.json if it exists
            manifest_path = Path(config_path or "agents_manifest.json")
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    config = json.load(f)
                    self.agents = config.get("agents", {})
                    logger.info(f"Loaded {len(self.agents)} agent configurations from manifest")
            else:
                # Use default configuration
                self._setup_default_agents()
                
        except Exception as e:
            logger.warning(f"Failed to load agent configurations: {e}")
            self._setup_default_agents()
    
    def _setup_default_agents(self) -> None:
        """Setup default agent configurations"""
        self.agents = {
            "regulation_analysis": {
                "name": "Regulation Analysis Agent",
                "description": "AI regulation ingestion and framework analysis",
                "capabilities": [
                    "EU AI Act analysis",
                    "GDPR/CCPA interpretation", 
                    "NIST framework mapping",
                    "Sectoral regulation review"
                ],
                "tools": ["vector_search", "document_analysis", "citation_generator"],
                "prompt_version": "v1",
                "status": "active"
            },
            "risk_scoring": {
                "name": "Risk Scoring Agent",
                "description": "Compliance risk assessment and scoring",
                "capabilities": [
                    "High-risk AI classification",
                    "Data protection risk scoring",
                    "Algorithmic bias assessment",
                    "Transparency requirements analysis"
                ],
                "tools": ["risk_calculator", "compliance_checker", "bias_detector"],
                "prompt_version": "v1", 
                "status": "active"
            },
            "compliance_expert": {
                "name": "Compliance Expert Agent",
                "description": "Regulatory compliance and audit preparation",
                "capabilities": [
                    "Compliance checklist generation",
                    "Audit preparation guidance",
                    "Implementation roadmaps",
                    "Monitoring and reporting"
                ],
                "tools": ["checklist_generator", "audit_tracker", "compliance_monitor"],
                "prompt_version": "v1",
                "status": "active"  
            },
            "policy_translation": {
                "name": "Policy Translation Agent",
                "description": "Complex regulation interpretation and translation",
                "capabilities": [
                    "Plain language translation",
                    "Implementation step generation",
                    "Technical mapping",
                    "Best practices recommendation"
                ],
                "tools": ["language_processor", "implementation_mapper", "best_practices_db"],
                "prompt_version": "v1",
                "status": "active"
            },
            "comparative_regulatory": {
                "name": "Comparative Regulatory Agent", 
                "description": "Cross-jurisdictional regulatory analysis",
                "capabilities": [
                    "Cross-jurisdictional mapping",
                    "Harmonization analysis",
                    "Global compliance strategy",
                    "Regulatory trend analysis"
                ],
                "tools": ["jurisdiction_mapper", "trend_analyzer", "compliance_strategist"],
                "prompt_version": "v1",
                "status": "active"
            }
        }
    
    def get_agent_config(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific agent type
        
        Args:
            agent_type: Type of agent (e.g., 'regulation_analysis')
            
        Returns:
            Agent configuration dictionary or None if not found
        """
        return self.agents.get(agent_type)
    
    def list_available_agents(self) -> List[str]:
        """
        List all available agent types
        
        Returns:
            List of agent type identifiers
        """
        return [agent_type for agent_type, config in self.agents.items() 
                if config.get("status") == "active"]
    
    def get_agent_capabilities(self, agent_type: str) -> List[str]:
        """
        Get capabilities for a specific agent
        
        Args:
            agent_type: Type of agent
            
        Returns:
            List of agent capabilities
        """
        config = self.get_agent_config(agent_type)
        return config.get("capabilities", []) if config else []
    
    def get_agent_tools(self, agent_type: str) -> List[str]:
        """
        Get tools available to a specific agent
        
        Args:
            agent_type: Type of agent
            
        Returns:
            List of tool identifiers
        """
        config = self.get_agent_config(agent_type)
        return config.get("tools", []) if config else []
    
    def register_session(self, session_id: str, agent_type: str, user_context: Dict[str, Any]) -> None:
        """
        Register an active agent session
        
        Args:
            session_id: Unique session identifier
            agent_type: Type of agent being used
            user_context: User context and preferences
        """
        self.active_sessions[session_id] = {
            "agent_type": agent_type,
            "user_context": user_context,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        logger.debug(f"Registered session {session_id} for agent {agent_type}")
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get active session information
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session information or None if not found
        """
        return self.active_sessions.get(session_id)
    
    def update_session_activity(self, session_id: str) -> None:
        """
        Update last activity timestamp for a session
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
    
    def cleanup_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old inactive sessions
        
        Args:
            max_age_hours: Maximum age for sessions in hours
            
        Returns:
            Number of sessions cleaned up
        """
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        old_sessions = []
        
        for session_id, session_info in self.active_sessions.items():
            try:
                last_activity = datetime.fromisoformat(session_info["last_activity"])
                if last_activity < cutoff_time:
                    old_sessions.append(session_id)
            except Exception as e:
                logger.warning(f"Error checking session age for {session_id}: {e}")
                old_sessions.append(session_id)  # Remove problematic sessions
        
        # Remove old sessions
        for session_id in old_sessions:
            del self.active_sessions[session_id]
        
        if old_sessions:
            logger.info(f"Cleaned up {len(old_sessions)} old agent sessions")
        
        return len(old_sessions)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics
        
        Returns:
            Dictionary with registry statistics
        """
        active_agents = [agent for agent, config in self.agents.items() 
                        if config.get("status") == "active"]
        
        return {
            "total_agents": len(self.agents),
            "active_agents": len(active_agents),
            "active_sessions": len(self.active_sessions),
            "agent_types": active_agents,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def validate_agent_setup(self) -> Dict[str, bool]:
        """
        Validate that all agents are properly configured
        
        Returns:
            Dictionary mapping agent types to validation status
        """
        validation_results = {}
        
        for agent_type, config in self.agents.items():
            # Basic validation checks
            has_name = bool(config.get("name"))
            has_description = bool(config.get("description")) 
            has_capabilities = bool(config.get("capabilities"))
            has_status = config.get("status") == "active"
            
            validation_results[agent_type] = all([
                has_name, has_description, has_capabilities, has_status
            ])
        
        return validation_results

# Global registry instance
_registry_instance: Optional[AgentRegistry] = None

def get_agent_registry() -> AgentRegistry:
    """
    Get the global agent registry instance
    
    Returns:
        Global AgentRegistry instance
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = AgentRegistry()
    return _registry_instance
