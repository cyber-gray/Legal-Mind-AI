#!/usr/bin/env python3
"""
Tests for Agent Registry

Tests agent registration, configuration, and lifecycle management.
"""

import pytest
from unittest.mock import patch, Mock
from legal_mind.agents.registry import AgentRegistry, get_agent_registry

class TestAgentRegistry:
    """Test cases for AgentRegistry class"""
    
    def test_initialization(self):
        """Test registry initialization"""
        registry = AgentRegistry()
        assert isinstance(registry.agents, dict)
        assert len(registry.agents) > 0  # Should have default agents
    
    def test_default_agents_setup(self):
        """Test that default agents are properly configured"""
        registry = AgentRegistry()
        expected_agents = [
            "regulation_analysis",
            "risk_scoring", 
            "compliance_expert",
            "policy_translation",
            "comparative_regulatory"
        ]
        
        for agent_type in expected_agents:
            assert agent_type in registry.agents
            config = registry.agents[agent_type]
            assert "name" in config
            assert "description" in config
            assert "capabilities" in config
            assert "status" in config
            assert config["status"] == "active"
    
    def test_get_agent_config(self):
        """Test retrieving agent configuration"""
        registry = AgentRegistry()
        
        # Test valid agent
        config = registry.get_agent_config("regulation_analysis")
        assert config is not None
        assert config["name"] == "Regulation Analysis Agent"
        
        # Test invalid agent
        config = registry.get_agent_config("nonexistent_agent")
        assert config is None
    
    def test_list_available_agents(self):
        """Test listing available agents"""
        registry = AgentRegistry()
        agents = registry.list_available_agents()
        
        assert isinstance(agents, list)
        assert len(agents) > 0
        assert "regulation_analysis" in agents
        assert "risk_scoring" in agents
    
    def test_get_agent_capabilities(self):
        """Test retrieving agent capabilities"""
        registry = AgentRegistry()
        
        capabilities = registry.get_agent_capabilities("regulation_analysis")
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
        assert "EU AI Act analysis" in capabilities
    
    def test_get_agent_tools(self):
        """Test retrieving agent tools"""
        registry = AgentRegistry()
        
        tools = registry.get_agent_tools("risk_scoring")
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert "risk_calculator" in tools
    
    def test_session_management(self):
        """Test session registration and management"""
        registry = AgentRegistry()
        
        # Register a session
        session_id = "test-session-123"
        agent_type = "regulation_analysis"
        user_context = {"user_id": "test-user", "preferences": {}}
        
        registry.register_session(session_id, agent_type, user_context)
        
        # Retrieve session
        session = registry.get_session(session_id)
        assert session is not None
        assert session["agent_type"] == agent_type
        assert session["user_context"] == user_context
        assert "created_at" in session
        assert "last_activity" in session
    
    def test_session_activity_update(self):
        """Test updating session activity"""
        registry = AgentRegistry()
        
        session_id = "test-session-456"
        registry.register_session(session_id, "risk_scoring", {})
        
        original_activity = registry.get_session(session_id)["last_activity"]
        
        # Update activity (would normally have time difference)
        registry.update_session_activity(session_id)
        
        # Verify session still exists and can be updated
        assert registry.get_session(session_id) is not None
    
    def test_registry_stats(self):
        """Test registry statistics"""
        registry = AgentRegistry()
        stats = registry.get_registry_stats()
        
        assert isinstance(stats, dict)
        assert "total_agents" in stats
        assert "active_agents" in stats
        assert "active_sessions" in stats
        assert "agent_types" in stats
        assert "last_updated" in stats
        
        assert stats["total_agents"] >= 5  # At least 5 default agents
        assert isinstance(stats["agent_types"], list)
    
    def test_validate_agent_setup(self):
        """Test agent setup validation"""
        registry = AgentRegistry()
        validation_results = registry.validate_agent_setup()
        
        assert isinstance(validation_results, dict)
        
        for agent_type, is_valid in validation_results.items():
            assert isinstance(is_valid, bool)
            assert is_valid  # All default agents should be valid
    
    def test_global_registry_instance(self):
        """Test global registry singleton"""
        registry1 = get_agent_registry()
        registry2 = get_agent_registry()
        
        # Should return the same instance
        assert registry1 is registry2
        assert isinstance(registry1, AgentRegistry)

class TestAgentRegistryWithMockConfig:
    """Test agent registry with mock configuration"""
    
    @patch('legal_mind.agents.registry.Path.exists')
    @patch('builtins.open')
    def test_load_from_manifest(self, mock_open, mock_exists):
        """Test loading configuration from manifest file"""
        mock_exists.return_value = True
        mock_config = {
            "agents": {
                "test_agent": {
                    "name": "Test Agent",
                    "description": "Test description",
                    "capabilities": ["test"],
                    "status": "active"
                }
            }
        }
        
        mock_file = Mock()
        mock_file.__enter__.return_value = mock_file
        mock_file.read.return_value = '{"agents": {"test_agent": {"name": "Test Agent", "description": "Test description", "capabilities": ["test"], "status": "active"}}}'
        mock_open.return_value = mock_file
        
        with patch('json.load', return_value=mock_config):
            registry = AgentRegistry(config_path="test_manifest.json")
            assert "test_agent" in registry.agents
            assert registry.agents["test_agent"]["name"] == "Test Agent"
