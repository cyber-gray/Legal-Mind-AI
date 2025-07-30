#!/usr/bin/env python3
"""
Test script for Azure AI Agents integration
"""

import asyncio
import logging
from thread_session import get_thread_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_agents():
    """Test Azure AI Agents integration"""
    try:
        print("🚀 Testing Azure AI Agents Integration...")
        
        # Get thread session
        thread_session = await get_thread_session()
        print("✅ ThreadSession initialized successfully")
        
        # Test queries for different agents
        test_queries = [
            ("regulation_analysis", "What are the key requirements for GDPR compliance?"),
            ("risk_scoring", "What compliance risks should I consider for data processing?"),
            ("compliance_expert", "Can you provide a GDPR compliance checklist?"),
            ("policy_translation", "Please explain GDPR Article 6 in simple terms"),
            ("comparative_regulatory", "How does GDPR compare to CCPA?")
        ]
        
        user_id = "test-user-123"
        
        print(f"\n📋 Testing {len(test_queries)} agent queries...")
        
        for i, (agent_name, query) in enumerate(test_queries, 1):
            print(f"\n--- Test {i}/{len(test_queries)}: {agent_name} ---")
            print(f"Query: {query}")
            
            try:
                response = await thread_session.process_message(
                    user_id=user_id,
                    agent_name=agent_name,
                    message=query
                )
                
                if response:
                    print(f"✅ Response received:")
                    print(f"{response[:200]}..." if len(response) > 200 else response)
                else:
                    print("❌ No response received")
                    
            except Exception as e:
                print(f"❌ Error testing {agent_name}: {str(e)}")
        
        print(f"\n🎉 Azure AI Agents integration test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agents())
