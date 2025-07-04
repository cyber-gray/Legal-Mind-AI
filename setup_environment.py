#!/usr/bin/env python3
"""
Environment Setup and Validation Tool for Legal-Mind-AI
Helps set up environment variables and validate API keys
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
from dotenv import load_dotenv

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Settings
from services.news_service import NewsMonitorService
from services.search_service import SearchService

class EnvironmentSetup:
    """Environment setup and validation utility"""
    
    def __init__(self):
        self.settings = Settings()
        self.env_file = Path(".env")
        self.env_example = Path(".env.example")
        
    def create_env_file(self) -> bool:
        """Create .env file from .env.example if it doesn't exist"""
        if self.env_file.exists():
            print(f"✓ Environment file {self.env_file} already exists")
            return True
            
        if not self.env_example.exists():
            print(f"❌ Example file {self.env_example} not found")
            return False
            
        try:
            # Copy example file to .env
            content = self.env_example.read_text()
            self.env_file.write_text(content)
            print(f"✓ Created {self.env_file} from {self.env_example}")
            print(f"📝 Please edit {self.env_file} with your actual API keys and endpoints")
            return True
        except Exception as e:
            print(f"❌ Failed to create {self.env_file}: {e}")
            return False
    
    def load_environment(self) -> bool:
        """Load environment variables from .env file"""
        if not self.env_file.exists():
            print(f"❌ Environment file {self.env_file} not found")
            return False
            
        try:
            load_dotenv(self.env_file)
            print(f"✓ Loaded environment variables from {self.env_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to load environment: {e}")
            return False
    
    def validate_configuration(self) -> Tuple[List[str], List[str]]:
        """Validate configuration and return (missing, warnings)"""
        missing = self.settings.validate()
        warnings = []
        
        # Check for optional but recommended settings
        if not self.settings.news.news_api_key and not self.settings.news.bing_search_key:
            warnings.append("No news search API keys configured (NEWS_API_KEY or BING_SEARCH_KEY)")
            
        if not self.settings.email.sendgrid_api_key:
            warnings.append("SendGrid API key not configured (SENDGRID_API_KEY)")
            
        if not self.settings.azure.search_endpoint:
            warnings.append("Azure Search not configured (AZURE_SEARCH_ENDPOINT)")
            
        return missing, warnings
    
    async def test_services(self) -> Dict[str, bool]:
        """Test each service with current configuration"""
        results = {}
        
        # Test News Service
        print("\n🔍 Testing News Service...")
        try:
            news_service = NewsMonitorService()
            # Try a simple search
            news_items = await news_service.search_news("artificial intelligence", max_results=1)
            results['news_service'] = len(news_items) > 0
            if results['news_service']:
                print(f"✓ News Service working - found {len(news_items)} items")
            else:
                print("⚠️  News Service returned no results (API key may be missing)")
        except Exception as e:
            print(f"❌ News Service failed: {e}")
            results['news_service'] = False
        
        # Test Search Service
        print("\n🔍 Testing Search Service...")
        try:
            search_service = SearchService()
            # Try a simple search
            search_results = await search_service.search("AI policy", search_type="general")
            results['search_service'] = len(search_results) > 0
            if results['search_service']:
                print(f"✓ Search Service working - found {len(search_results)} results")
            else:
                print("⚠️  Search Service returned no results")
        except Exception as e:
            print(f"❌ Search Service failed: {e}")
            results['search_service'] = False
        
        return results
    
    def generate_sample_env(self) -> str:
        """Generate a sample .env file with placeholders"""
        sample_content = """# Legal-Mind-AI Environment Configuration
# Copy this file to .env and fill in your actual values

# Azure AI Project Settings (Required)
AZURE_PROJECT_ENDPOINT=https://your-resource.services.ai.azure.com/api/projects/your-project
AZURE_AGENT_ID=asst_your_agent_id_here

# Microsoft Teams Bot Framework (Required for Teams integration)
MICROSOFT_APP_ID=your_teams_app_id
MICROSOFT_APP_PASSWORD=your_teams_app_password

# Azure AI Search (Recommended for legal corpus search)
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your_search_key
AZURE_SEARCH_INDEX_NAME=legal-mind-corpus

# News Search APIs (At least one recommended)
NEWS_API_KEY=your_newsapi_key
BING_SEARCH_KEY=your_bing_search_key

# Email Service (Optional)
SENDGRID_API_KEY=your_sendgrid_key
FROM_EMAIL=legalmind@yourcompany.com

# Application Settings
APP_PORT=3978
DEBUG=True
LOG_LEVEL=INFO
COMPANY_NAME=Legal-Mind-AI
COMPANY_LOGO_PATH=assets/logo.png
"""
        return sample_content
    
    def interactive_setup(self):
        """Interactive setup wizard"""
        print("🚀 Legal-Mind-AI Environment Setup Wizard")
        print("=" * 50)
        
        # Step 1: Create .env file
        print("\n📋 Step 1: Environment File Setup")
        if not self.create_env_file():
            print("\n❌ Could not create environment file. Please create .env manually.")
            print("\nSample .env content:")
            print(self.generate_sample_env())
            return False
        
        # Step 2: Load environment
        print("\n📋 Step 2: Load Environment Variables")
        if not self.load_environment():
            return False
        
        # Step 3: Validate configuration
        print("\n📋 Step 3: Validate Configuration")
        missing, warnings = self.validate_configuration()
        
        if missing:
            print(f"\n❌ Missing required configuration:")
            for item in missing:
                print(f"   - {item}")
            print(f"\n📝 Please edit {self.env_file} and add the missing values")
        else:
            print("✓ All required configuration present")
        
        if warnings:
            print(f"\n⚠️  Optional configuration warnings:")
            for warning in warnings:
                print(f"   - {warning}")
        
        # Step 4: Test services (if config is complete)
        if not missing:
            print("\n📋 Step 4: Test Services")
            print("Testing services with current configuration...")
            
            try:
                results = asyncio.run(self.test_services())
                
                print(f"\n📊 Service Test Results:")
                for service, status in results.items():
                    status_icon = "✓" if status else "❌"
                    print(f"   {status_icon} {service}: {'Working' if status else 'Failed'}")
                
                working_services = sum(results.values())
                total_services = len(results)
                
                if working_services == total_services:
                    print(f"\n🎉 All services are working! You're ready to go.")
                elif working_services > 0:
                    print(f"\n⚠️  {working_services}/{total_services} services working. Check API keys for failed services.")
                else:
                    print(f"\n❌ No services working. Please check your API keys and configuration.")
                    
            except Exception as e:
                print(f"\n❌ Error testing services: {e}")
        
        print("\n" + "=" * 50)
        print("Setup complete! Next steps:")
        print("1. Edit .env with your actual API keys")
        print("2. Run 'python console_test.py' to test the system")
        print("3. Run 'python test_semantic_kernel.py' to test Semantic Kernel integration")
        
        return not bool(missing)

def main():
    """Main setup function"""
    setup = EnvironmentSetup()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "validate":
            # Load environment and validate
            setup.load_environment()
            missing, warnings = setup.validate_configuration()
            
            if missing:
                print("❌ Missing required configuration:")
                for item in missing:
                    print(f"   - {item}")
                sys.exit(1)
            else:
                print("✓ Configuration is valid")
                
        elif command == "test":
            # Load environment and test services
            setup.load_environment()
            results = asyncio.run(setup.test_services())
            
            failed_services = [service for service, status in results.items() if not status]
            if failed_services:
                print(f"❌ Failed services: {', '.join(failed_services)}")
                sys.exit(1)
            else:
                print("✓ All services working")
                
        elif command == "create-env":
            # Just create the .env file
            setup.create_env_file()
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: validate, test, create-env")
            sys.exit(1)
    else:
        # Interactive setup
        setup.interactive_setup()

if __name__ == "__main__":
    main()
