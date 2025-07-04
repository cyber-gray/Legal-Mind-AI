"""
Plugin Manager for Legal-Mind-AI Semantic Kernel
Manages plugin registration, discovery, and lifecycle
"""

import os
import json
import asyncio
import importlib
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class PluginMetadata:
    """Metadata for a Legal-Mind-AI plugin"""
    name: str
    version: str
    description: str
    author: str
    capabilities: List[str]
    dependencies: List[str] = None
    config_required: List[str] = None
    enabled: bool = True

class BaseLegalMindPlugin(ABC):
    """Base class for Legal-Mind-AI plugins"""
    
    def __init__(self):
        self.metadata: Optional[PluginMetadata] = None
        self.config: Dict[str, Any] = {}
        self.initialized = False
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration"""
        pass
    
    @abstractmethod
    async def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plugin's main functionality"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass
    
    async def cleanup(self):
        """Cleanup plugin resources"""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate plugin configuration, return list of missing items"""
        missing = []
        if self.metadata and self.metadata.config_required:
            for key in self.metadata.config_required:
                if key not in config:
                    missing.append(key)
        return missing

class PluginManager:
    """Manages plugin lifecycle and execution"""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, BaseLegalMindPlugin] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.config = {}
        
        # Create plugin directory if it doesn't exist
        self.plugin_dir.mkdir(exist_ok=True)
        
        # Load core plugins
        self._register_core_plugins()
    
    def _register_core_plugins(self):
        """Register core built-in plugins"""
        from agents.semantic_orchestrator import (
            LegalSearchPlugin, NewsMonitorPlugin, 
            PolicyExpertPlugin, ReportGeneratorPlugin
        )
        from services.search_service import SearchService
        from services.news_service import NewsMonitorService
        from services.pdf_generator import LegalMindReportGenerator
        from services.email_service import EmailService
        
        # Wrap existing plugins in the new interface
        core_plugins = [
            EnhancedLegalSearchPlugin(SearchService()),
            EnhancedNewsMonitorPlugin(NewsMonitorService()),
            EnhancedPolicyExpertPlugin(),
            EnhancedReportGeneratorPlugin(LegalMindReportGenerator(), EmailService())
        ]
        
        for plugin in core_plugins:
            self.register_plugin(plugin)
    
    def register_plugin(self, plugin: BaseLegalMindPlugin):
        """Register a plugin with the manager"""
        try:
            metadata = plugin.get_metadata()
            
            # Validate dependencies
            if metadata.dependencies:
                missing_deps = self._check_dependencies(metadata.dependencies)
                if missing_deps:
                    logger.warning("Plugin has missing dependencies", 
                                 plugin=metadata.name, 
                                 missing=missing_deps)
                    return False
            
            self.plugins[metadata.name] = plugin
            self.plugin_metadata[metadata.name] = metadata
            
            logger.info("Plugin registered", plugin=metadata.name, version=metadata.version)
            return True
            
        except Exception as e:
            logger.error("Failed to register plugin", error=str(e))
            return False
    
    async def initialize_plugin(self, plugin_name: str, config: Dict[str, Any] = None) -> bool:
        """Initialize a specific plugin"""
        if plugin_name not in self.plugins:
            logger.error("Plugin not found", plugin=plugin_name)
            return False
        
        plugin = self.plugins[plugin_name]
        plugin_config = config or self.config.get(plugin_name, {})
        
        try:
            # Validate configuration
            missing = plugin.validate_config(plugin_config)
            if missing:
                logger.warning("Plugin missing configuration", 
                             plugin=plugin_name, 
                             missing=missing)
            
            # Initialize plugin
            success = await plugin.initialize(plugin_config)
            if success:
                plugin.initialized = True
                logger.info("Plugin initialized", plugin=plugin_name)
            else:
                logger.error("Plugin initialization failed", plugin=plugin_name)
            
            return success
            
        except Exception as e:
            logger.error("Plugin initialization error", plugin=plugin_name, error=str(e))
            return False
    
    async def initialize_all_plugins(self):
        """Initialize all registered plugins"""
        for plugin_name in self.plugins:
            await self.initialize_plugin(plugin_name)
    
    async def execute_plugin(self, plugin_name: str, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a specific plugin"""
        if plugin_name not in self.plugins:
            return {"error": f"Plugin {plugin_name} not found"}
        
        plugin = self.plugins[plugin_name]
        
        if not plugin.initialized:
            success = await self.initialize_plugin(plugin_name)
            if not success:
                return {"error": f"Failed to initialize plugin {plugin_name}"}
        
        try:
            result = await plugin.execute(query, context or {})
            return result
            
        except Exception as e:
            logger.error("Plugin execution failed", plugin=plugin_name, error=str(e))
            return {"error": f"Plugin execution failed: {str(e)}"}
    
    def get_available_plugins(self) -> List[PluginMetadata]:
        """Get list of available plugins"""
        return list(self.plugin_metadata.values())
    
    def get_plugin_capabilities(self, plugin_name: str) -> List[str]:
        """Get capabilities of a specific plugin"""
        if plugin_name in self.plugin_metadata:
            return self.plugin_metadata[plugin_name].capabilities
        return []
    
    def find_plugins_by_capability(self, capability: str) -> List[str]:
        """Find plugins that have a specific capability"""
        matching_plugins = []
        for name, metadata in self.plugin_metadata.items():
            if capability in metadata.capabilities:
                matching_plugins.append(name)
        return matching_plugins
    
    def _check_dependencies(self, dependencies: List[str]) -> List[str]:
        """Check for missing dependencies"""
        missing = []
        for dep in dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing.append(dep)
        return missing
    
    def save_config(self, config_path: str = "plugin_config.json"):
        """Save plugin configuration to file"""
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Plugin configuration saved", path=config_path)
        except Exception as e:
            logger.error("Failed to save plugin config", error=str(e))
    
    def load_config(self, config_path: str = "plugin_config.json"):
        """Load plugin configuration from file"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info("Plugin configuration loaded", path=config_path)
        except Exception as e:
            logger.error("Failed to load plugin config", error=str(e))


# Enhanced core plugins implementing the new interface

class EnhancedLegalSearchPlugin(BaseLegalMindPlugin):
    """Enhanced legal search plugin"""
    
    def __init__(self, search_service):
        super().__init__()
        self.search_service = search_service
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="LegalSearch",
            version="2.0.0",
            description="Search legal documents, policies, and regulations",
            author="Legal-Mind-AI Team",
            capabilities=["legal_search", "document_retrieval", "policy_lookup"],
            dependencies=["azure-search-documents"],
            config_required=["search_endpoint", "search_key"]
        )
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        self.config = config
        return True
    
    async def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from services.search_service import SearchType
            
            search_type = context.get("search_type", SearchType.WEB_SEARCH)
            max_results = context.get("max_results", 5)
            
            response = await self.search_service.search(query, search_type, max_results)
            
            return {
                "success": True,
                "results": [
                    {
                        "title": result.title,
                        "content": result.content,
                        "source": result.source,
                        "url": getattr(result, 'url', None),
                        "relevance": getattr(result, 'relevance_score', 0.0)
                    }
                    for result in (response.results if response else [])
                ],
                "query": query,
                "total_results": len(response.results) if response else 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

class EnhancedNewsMonitorPlugin(BaseLegalMindPlugin):
    """Enhanced news monitoring plugin"""
    
    def __init__(self, news_service):
        super().__init__()
        self.news_service = news_service
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="NewsMonitor",
            version="2.0.0",
            description="Monitor AI policy and regulation news",
            author="Legal-Mind-AI Team",
            capabilities=["news_search", "real_time_updates", "ai_policy_tracking"],
            dependencies=["newsapi-python", "feedparser"],
            config_required=["news_api_key"]
        )
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        self.config = config
        return True
    
    async def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            max_results = context.get("max_results", 5)
            hours_back = context.get("hours_back", 24)
            
            news_items = await self.news_service.get_latest_news(
                query=query,
                hours_back=hours_back,
                max_items=max_results
            )
            
            return {
                "success": True,
                "news_items": [
                    {
                        "title": item.title,
                        "summary": item.summary,
                        "url": item.url,
                        "source": item.source,
                        "published_date": item.published_date.isoformat(),
                        "relevance_score": item.relevance_score,
                        "keywords": item.keywords
                    }
                    for item in news_items
                ],
                "query": query,
                "total_items": len(news_items)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

class EnhancedPolicyExpertPlugin(BaseLegalMindPlugin):
    """Enhanced policy expert plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="PolicyExpert",
            version="2.0.0",
            description="AI policy and regulation expert analysis",
            author="Legal-Mind-AI Team",
            capabilities=["policy_analysis", "compliance_guidance", "regulatory_interpretation"],
            dependencies=[],
            config_required=[]
        )
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        self.config = config
        return True
    
    async def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # For now, return structured policy guidance
            # In a full implementation, this would use AI services
            
            policy_areas = {
                "eu ai act": {
                    "summary": "Comprehensive EU regulation for AI systems",
                    "key_points": [
                        "Risk-based approach to AI regulation",
                        "Prohibited AI practices",
                        "High-risk AI system requirements",
                        "Transparency obligations"
                    ],
                    "compliance_deadline": "2025-08-02"
                },
                "gdpr": {
                    "summary": "General Data Protection Regulation",
                    "key_points": [
                        "Data subject rights",
                        "Lawful basis for processing",
                        "Data protection by design",
                        "Breach notification requirements"
                    ],
                    "compliance_deadline": "2018-05-25"
                },
                "nist ai rmf": {
                    "summary": "NIST AI Risk Management Framework",
                    "key_points": [
                        "Identify AI risks",
                        "Govern AI systems",
                        "Map AI impacts",
                        "Measure AI performance"
                    ],
                    "compliance_deadline": "Voluntary framework"
                }
            }
            
            query_lower = query.lower()
            relevant_policies = []
            
            for policy, details in policy_areas.items():
                if any(keyword in query_lower for keyword in policy.split()):
                    relevant_policies.append({
                        "policy": policy,
                        **details
                    })
            
            if not relevant_policies:
                # Provide general guidance
                relevant_policies = [{
                    "policy": "General AI Governance",
                    "summary": "General principles for AI governance and compliance",
                    "key_points": [
                        "Establish AI governance framework",
                        "Implement risk assessment processes",
                        "Ensure transparency and accountability",
                        "Monitor and audit AI systems"
                    ],
                    "compliance_deadline": "Ongoing"
                }]
            
            return {
                "success": True,
                "analysis": {
                    "query": query,
                    "relevant_policies": relevant_policies,
                    "recommendations": [
                        "Conduct regular compliance assessments",
                        "Implement proper documentation",
                        "Establish monitoring procedures",
                        "Train relevant personnel"
                    ]
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

class EnhancedReportGeneratorPlugin(BaseLegalMindPlugin):
    """Enhanced report generator plugin"""
    
    def __init__(self, pdf_generator, email_service):
        super().__init__()
        self.pdf_generator = pdf_generator
        self.email_service = email_service
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="ReportGenerator",
            version="2.0.0",
            description="Generate and deliver comprehensive reports",
            author="Legal-Mind-AI Team",
            capabilities=["pdf_generation", "email_delivery", "report_formatting"],
            dependencies=["reportlab", "sendgrid"],
            config_required=["sendgrid_api_key"]
        )
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        self.config = config
        return True
    
    async def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            content = context.get("content", "")
            format_type = context.get("format", "text")
            email_address = context.get("email_address")
            
            if format_type == "pdf":
                pdf_path = await self.pdf_generator.generate_policy_report(
                    title=f"Legal-Mind-AI Report: {query[:50]}",
                    content=content,
                    user_id=context.get("user_id", "system")
                )
                
                result = {
                    "success": True,
                    "report_type": "pdf",
                    "file_path": pdf_path
                }
                
                if email_address:
                    await self.email_service.send_report_email(
                        email_address,
                        f"Legal-Mind-AI Report: {query[:30]}",
                        content,
                        pdf_path
                    )
                    result["email_sent"] = True
                    result["email_address"] = email_address
                
                return result
            else:
                return {
                    "success": True,
                    "report_type": "text",
                    "content": content
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global plugin manager instance
plugin_manager = PluginManager()
