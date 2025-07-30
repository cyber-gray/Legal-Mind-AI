#!/usr/bin/env python3
"""
Prompt Version Management System

Manages versioned prompts with audit trail and hash verification for
specialized legal AI agents.
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class PromptVersionManager:
    """
    Manages versioned prompts for legal AI agents
    
    Features:
    - Version tracking with semantic versioning
    - Content hashing for integrity verification
    - Audit trail for prompt changes
    - Rollback capabilities
    """
    
    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize prompt version manager
        
        Args:
            prompts_dir: Directory containing versioned prompt files
        """
        self.prompts_dir = Path(prompts_dir)
        self.version_registry = {}
        self._load_version_registry()
        
    def _load_version_registry(self) -> None:
        """Load the version registry from disk"""
        registry_path = self.prompts_dir / "version_registry.json"
        
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    self.version_registry = json.load(f)
                logger.info(f"Loaded version registry with {len(self.version_registry)} agents")
            except Exception as e:
                logger.error(f"Failed to load version registry: {e}")
                self.version_registry = {}
        else:
            # Initialize registry for first time
            self._discover_prompts()
            
    def _discover_prompts(self) -> None:
        """Discover and register existing prompt files"""
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory {self.prompts_dir} does not exist")
            return
            
        for prompt_file in self.prompts_dir.glob("*.v*.md"):
            try:
                # Parse filename: agent_name.v1.md -> (agent_name, v1)
                name_parts = prompt_file.stem.split('.')
                if len(name_parts) >= 2:
                    agent_name = name_parts[0]
                    version = name_parts[1]
                    
                    if agent_name not in self.version_registry:
                        self.version_registry[agent_name] = {}
                    
                    # Calculate content hash
                    content_hash = self._calculate_file_hash(prompt_file)
                    
                    self.version_registry[agent_name][version] = {
                        "filename": prompt_file.name,
                        "content_hash": content_hash,
                        "created_at": datetime.utcnow().isoformat(),
                        "discovered": True
                    }
                    
            except Exception as e:
                logger.error(f"Error processing prompt file {prompt_file}: {e}")
        
        # Save the discovered registry
        self._save_version_registry()
        logger.info(f"Discovered {len(self.version_registry)} agent prompt versions")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file contents"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                hasher.update(f.read())
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return "unknown"
    
    def _save_version_registry(self) -> None:
        """Save version registry to disk"""
        registry_path = self.prompts_dir / "version_registry.json"
        
        try:
            self.prompts_dir.mkdir(exist_ok=True)
            with open(registry_path, 'w') as f:
                json.dump(self.version_registry, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save version registry: {e}")
    
    def get_prompt(self, agent_name: str, version: str = "latest") -> Optional[str]:
        """
        Get prompt content for an agent
        
        Args:
            agent_name: Name of the agent
            version: Version to retrieve (default: "latest")
            
        Returns:
            Prompt content or None if not found
        """
        if agent_name not in self.version_registry:
            logger.warning(f"Agent {agent_name} not found in registry")
            return None
        
        agent_versions = self.version_registry[agent_name]
        
        # Handle "latest" version
        if version == "latest":
            if not agent_versions:
                return None
            # Get the highest version number
            version_nums = [v for v in agent_versions.keys() if v.startswith('v')]
            if version_nums:
                version = max(version_nums, key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
        
        if version not in agent_versions:
            logger.warning(f"Version {version} not found for agent {agent_name}")
            return None
        
        version_info = agent_versions[version]
        prompt_file = self.prompts_dir / version_info["filename"]
        
        try:
            with open(prompt_file, 'r') as f:
                content = f.read()
            
            # Verify content hash for integrity
            current_hash = hashlib.sha256(content.encode()).hexdigest()
            expected_hash = version_info["content_hash"]
            
            if current_hash != expected_hash:
                logger.warning(f"Hash mismatch for {agent_name} {version} - content may have changed")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to read prompt file {prompt_file}: {e}")
            return None
    
    def list_agents(self) -> List[str]:
        """Get list of available agents"""
        return list(self.version_registry.keys())
    
    def list_versions(self, agent_name: str) -> List[str]:
        """
        Get list of available versions for an agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of version identifiers
        """
        if agent_name not in self.version_registry:
            return []
        
        return list(self.version_registry[agent_name].keys())
    
    def get_agent_info(self, agent_name: str) -> Dict[str, any]:
        """
        Get information about an agent and its versions
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary with agent information
        """
        if agent_name not in self.version_registry:
            return {}
        
        versions = self.version_registry[agent_name]
        latest_version = self.get_latest_version(agent_name)
        
        return {
            "agent_name": agent_name,
            "total_versions": len(versions),
            "latest_version": latest_version,
            "versions": versions,
            "available_versions": list(versions.keys())
        }
    
    def get_latest_version(self, agent_name: str) -> Optional[str]:
        """
        Get the latest version identifier for an agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Latest version identifier or None
        """
        if agent_name not in self.version_registry:
            return None
        
        versions = self.version_registry[agent_name]
        if not versions:
            return None
        
        # Find highest version number
        version_nums = [v for v in versions.keys() if v.startswith('v')]
        if version_nums:
            return max(version_nums, key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
        
        return list(versions.keys())[0]  # Fallback to first version
    
    def verify_integrity(self) -> Dict[str, bool]:
        """
        Verify integrity of all prompt files
        
        Returns:
            Dictionary mapping agent.version to verification status
        """
        results = {}
        
        for agent_name, versions in self.version_registry.items():
            for version, version_info in versions.items():
                prompt_file = self.prompts_dir / version_info["filename"]
                key = f"{agent_name}.{version}"
                
                try:
                    if not prompt_file.exists():
                        results[key] = False
                        continue
                    
                    current_hash = self._calculate_file_hash(prompt_file)
                    expected_hash = version_info["content_hash"]
                    results[key] = (current_hash == expected_hash)
                    
                except Exception as e:
                    logger.error(f"Error verifying {key}: {e}")
                    results[key] = False
        
        return results
    
    def get_registry_stats(self) -> Dict[str, any]:
        """Get statistics about the prompt registry"""
        total_agents = len(self.version_registry)
        total_versions = sum(len(versions) for versions in self.version_registry.values())
        
        return {
            "total_agents": total_agents,
            "total_versions": total_versions,
            "agents": list(self.version_registry.keys()),
            "last_updated": datetime.utcnow().isoformat()
        }

# Global instance
_prompt_manager: Optional[PromptVersionManager] = None

def get_prompt_manager() -> PromptVersionManager:
    """Get the global prompt version manager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptVersionManager()
    return _prompt_manager
