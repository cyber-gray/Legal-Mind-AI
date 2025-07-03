"""
Configuration settings for Legal-Mind-AI
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class AzureConfig:
    """Azure AI Project configuration"""
    project_endpoint: str
    agent_id: str
    search_endpoint: Optional[str] = None
    search_key: Optional[str] = None
    search_index: str = "legal-mind-corpus"

@dataclass
class TeamsConfig:
    """Microsoft Teams Bot configuration"""
    app_id: str
    app_password: str
    app_port: int = 3978

@dataclass
class EmailConfig:
    """Email service configuration"""
    sendgrid_api_key: Optional[str] = None
    from_email: str = "legalmind@yourcompany.com"
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

@dataclass
class NewsConfig:
    """News monitoring configuration"""
    news_api_key: Optional[str] = None
    bing_search_key: Optional[str] = None
    update_interval_hours: int = 6

@dataclass
class AppConfig:
    """Main application configuration"""
    debug: bool = False
    log_level: str = "INFO"
    company_name: str = "Legal-Mind-AI"
    company_logo_path: Optional[str] = None

class Settings:
    """
    Global settings manager for Legal-Mind-AI
    """
    
    def __init__(self):
        self.azure = AzureConfig(
            project_endpoint=os.getenv("AZURE_PROJECT_ENDPOINT", ""),
            agent_id=os.getenv("AZURE_AGENT_ID", ""),
            search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            search_key=os.getenv("AZURE_SEARCH_KEY"),
            search_index=os.getenv("AZURE_SEARCH_INDEX_NAME", "legal-mind-corpus")
        )
        
        self.teams = TeamsConfig(
            app_id=os.getenv("MICROSOFT_APP_ID", ""),
            app_password=os.getenv("MICROSOFT_APP_PASSWORD", ""),
            app_port=int(os.getenv("APP_PORT", "3978"))
        )
        
        self.email = EmailConfig(
            sendgrid_api_key=os.getenv("SENDGRID_API_KEY"),
            from_email=os.getenv("FROM_EMAIL", "legalmind@yourcompany.com"),
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME"),
            smtp_password=os.getenv("SMTP_PASSWORD")
        )
        
        self.news = NewsConfig(
            news_api_key=os.getenv("NEWS_API_KEY"),
            bing_search_key=os.getenv("BING_SEARCH_KEY"),
            update_interval_hours=int(os.getenv("NEWS_UPDATE_INTERVAL", "6"))
        )
        
        self.app = AppConfig(
            debug=os.getenv("DEBUG", "False").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            company_name=os.getenv("COMPANY_NAME", "Legal-Mind-AI"),
            company_logo_path=os.getenv("COMPANY_LOGO_PATH")
        )
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of missing required settings
        """
        missing = []
        
        if not self.azure.project_endpoint:
            missing.append("AZURE_PROJECT_ENDPOINT")
        
        if not self.azure.agent_id:
            missing.append("AZURE_AGENT_ID")
        
        if not self.teams.app_id:
            missing.append("MICROSOFT_APP_ID")
        
        if not self.teams.app_password:
            missing.append("MICROSOFT_APP_PASSWORD")
        
        return missing
    
    def get_agent_configs(self) -> Dict[str, str]:
        """Get agent configuration mapping"""
        return {
            "policy_expert": os.getenv("POLICY_EXPERT_AGENT_ID", self.azure.agent_id),
            "news_monitor": os.getenv("NEWS_MONITOR_AGENT_ID", self.azure.agent_id),
            "document_analyzer": os.getenv("DOCUMENT_ANALYZER_AGENT_ID", self.azure.agent_id),
            "report_generator": os.getenv("REPORT_GENERATOR_AGENT_ID", self.azure.agent_id)
        }

# Global settings instance
settings = Settings()
