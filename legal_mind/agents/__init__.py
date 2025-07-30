#!/usr/bin/env python3
"""
Legal Mind Agents Package

Agent registry and management for specialized legal AI agents.
"""

from .registry import AgentRegistry, get_agent_registry

__all__ = ["AgentRegistry", "get_agent_registry"]
