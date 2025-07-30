#!/usr/bin/env python3
"""
Legal Mind Prompts Package

Versioned prompt management system for specialized legal AI agents.
"""

from .version_manager import PromptVersionManager, get_prompt_manager

__all__ = ["PromptVersionManager", "get_prompt_manager"]
