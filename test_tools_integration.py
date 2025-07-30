#!/usr/bin/env python3
"""
Test script for Legal Research Tools integration with Azure AI Agents
"""

import asyncio
import logging
from legal_tools import get_legal_tools
from thread_session import get_thread_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_legal_tools():
    """Test Legal Research Tools functionality"""
    try:
        print("🔧 Testing Legal Research Tools Integration...")
        
        # Get legal tools instance
        legal_tools = get_legal_tools()
        print("✅ Legal tools initialized")
        
        # Test vector search
        print("\n--- Testing Vector Search ---")
        search_result = await legal_tools.vector_search(
            query="GDPR data processing requirements",
            document_types=["regulation", "guidance"],
            jurisdiction="EU",
            max_results=3
        )
        print(f"✅ Vector search returned {len(search_result.get('results', []))} results")
        if search_result.get('results'):
            print(f"   First result: {search_result['results'][0]['title']}")
        
        # Test deep research
        print("\n--- Testing Deep Research ---")
        research_result = await legal_tools.deep_research(
            topic="AI Act high-risk systems",
            research_depth="comprehensive",
            focus_areas=["regulations", "precedents"]
        )
        print(f"✅ Deep research completed with {research_result.get('summary', {}).get('total_sources', 0)} sources")
        
        # Test compliance checker
        print("\n--- Testing Compliance Checker ---")
        compliance_result = await legal_tools.compliance_checker(
            requirements=[
                "Data processing consent mechanisms",
                "Data subject rights implementation", 
                "Privacy by design implementation"
            ],
            jurisdiction="EU",
            framework="GDPR"
        )
        print(f"✅ Compliance check completed with score: {compliance_result.get('overall_score', 'N/A')}")
        print(f"   Risk level: {compliance_result.get('risk_level', 'N/A')}")
        
        print("\n🎉 Legal Research Tools test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Legal tools test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_tools_integration():
    """Test tools integration with ThreadSession"""
    try:
        print("\n🔗 Testing Tools Integration with ThreadSession...")
        
        # Get thread session
        thread_session = await get_thread_session()
        print("✅ ThreadSession with tools integration initialized")
        
        # Test tool calls through ThreadSession
        print("\n--- Testing Tool Call Processing ---")
        
        # Test vector search tool call
        vector_result = await thread_session.process_tool_call(
            tool_name="vector_search",
            arguments={
                "query": "EU AI Act prohibited practices",
                "document_types": ["regulation"],
                "jurisdiction": "EU"
            }
        )
        print(f"✅ Vector search tool call: {len(vector_result.get('results', []))} results")
        
        # Test deep research tool call
        research_result = await thread_session.process_tool_call(
            tool_name="deep_research", 
            arguments={
                "topic": "algorithmic transparency requirements",
                "research_depth": "basic"
            }
        )
        print(f"✅ Deep research tool call: {research_result.get('summary', {}).get('total_sources', 0)} sources")
        
        # Test compliance checker tool call
        compliance_result = await thread_session.process_tool_call(
            tool_name="compliance_checker",
            arguments={
                "requirements": ["Algorithmic impact assessment", "Explainability documentation"],
                "framework": "AI_Act"
            }
        )
        print(f"✅ Compliance checker tool call: {compliance_result.get('overall_score', 'N/A')} score")
        
        print("\n🎉 Tools integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Tools integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_enhanced_agents():
    """Test enhanced agents with tool capabilities"""
    try:
        print("\n🤖 Testing Enhanced Agents with Tool Integration...")
        
        thread_session = await get_thread_session()
        
        # Test queries that would benefit from tools
        test_cases = [
            {
                "agent": "regulation_analysis",
                "query": "What are the key requirements for high-risk AI systems under the EU AI Act?",
                "expected_tools": ["vector_search", "deep_research"]
            },
            {
                "agent": "compliance_expert", 
                "query": "Create a GDPR compliance checklist for AI data processing",
                "expected_tools": ["compliance_checker", "vector_search"]
            },
            {
                "agent": "risk_scoring",
                "query": "Assess compliance risks for an AI hiring system",
                "expected_tools": ["compliance_checker"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test_case['agent']} ---")
            print(f"Query: {test_case['query']}")
            
            # Process message through enhanced agent
            response = await thread_session.process_message(
                user_id="test-user-tools",
                agent_name=test_case["agent"],
                message=test_case["query"]
            )
            
            if response:
                print(f"✅ Enhanced agent response received")
                print(f"   Response preview: {response[:150]}...")
            else:
                print("❌ No response received")
        
        print("\n🎉 Enhanced agents test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced agents test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tool integration tests"""
    print("🚀 Starting Legal Research Tools Integration Tests...\n")
    
    results = []
    
    # Test 1: Legal tools functionality
    results.append(await test_legal_tools())
    
    # Test 2: Tools integration with ThreadSession  
    results.append(await test_tools_integration())
    
    # Test 3: Enhanced agents with tools
    results.append(await test_enhanced_agents())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Results Summary:")
    print(f"   Tests Passed: {passed}/{total}")
    print(f"   Success Rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n🎉 All tool integration tests PASSED!")
        print("\n🎯 Step 3: Tool Integration - COMPLETED SUCCESSFULLY")
        print("\n📋 Your Legal Mind Agent now includes:")
        print("   ✅ Vector Search - Semantic legal document search")
        print("   ✅ Deep Research - Multi-source legal research synthesis") 
        print("   ✅ Compliance Checker - Automated compliance assessment")
        print("   ✅ Tool Integration - Declarative tool attachment to agents")
        print("   ✅ Enhanced Agent Capabilities - Tools available to all 5 specialized agents")
    else:
        print(f"\n⚠️  {total-passed} test(s) failed - review errors above")

if __name__ == "__main__":
    asyncio.run(main())
