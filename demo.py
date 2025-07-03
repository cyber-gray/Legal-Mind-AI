#!/usr/bin/env python3
"""
Quick demo of Legal-Mind-AI capabilities
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from agents.orchestrator import orchestrator, QueryContext

async def demo():
    """Demonstrate Legal-Mind-AI capabilities"""
    load_dotenv()
    
    print("🤖 Legal-Mind-AI Demo")
    print("=" * 60)
    
    demo_question = "What are the key compliance requirements for facial recognition technology under current AI regulations?"
    
    print(f"📝 Demo Question:")
    print(f"   {demo_question}")
    print("\n🤖 Legal-Mind-AI Response:")
    print("-" * 60)
    
    context = QueryContext(
        user_id="demo_user",
        query=demo_question,
        priority="normal",
        output_format="text"
    )
    
    try:
        response = await orchestrator.process_query(context)
        print(response)
        
        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("\n💡 Your Legal-Mind-AI system is ready for:")
        print("   • Microsoft Teams integration")
        print("   • Professional PDF report generation")
        print("   • Email delivery of analysis")
        print("   • Real-time AI policy news monitoring")
        print("   • Multi-agent specialized analysis")
        
    except Exception as e:
        print(f"❌ Demo error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(demo())
