#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Legal Mind Agent Package

Modular package structure for Legal Mind Agent with specialized components:
- bots: Teams bot implementations
- agents: Agent registry and management  
- orchestrator: Thread session management
- tools: Legal research tools
- prompts: Versioned prompt system
"""

__version__ = "3.0.0"

# Import main components
from .bots import LegalMindTeamsBot
from .agents import AgentRegistry, get_agent_registry
from .orchestrator import ThreadSession, get_thread_session
from .tools import LegalResearchTools, get_legal_tools
from .prompts import PromptVersionManager, get_prompt_manager

# Export public API
__all__ = [
    "LegalMindTeamsBot", 
    "AgentRegistry", 
    "get_agent_registry",
    "ThreadSession", 
    "get_thread_session",
    "LegalResearchTools",
    "get_legal_tools",
    "PromptVersionManager",
    "get_prompt_manager"
]

# Import main components with correct names
from .bots import LegalMindTeamsBot
from .agents import AgentRegistry, get_agent_registry
from .orchestrator import ThreadSession, get_thread_session
from .tools import LegalResearchTools, get_legal_tools

__all__ = [
    "LegalMindTeamsBot",
    "AgentRegistry", 
    "get_agent_registry",
    "ThreadSession",
    "get_thread_session",
    "LegalResearchTools",
    "get_legal_tools"
]
