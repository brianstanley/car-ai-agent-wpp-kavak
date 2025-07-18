#!/usr/bin/env python3
"""
Test script for KavakInfoSearchTool.
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.kavak_info_search_tool import KavakInfoSearchTool
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_kavak_info_search():
    """Test the KavakInfoSearchTool."""
    print("🔍 Testing KavakInfoSearchTool")
    print("=" * 50)
    
    try:
        # Initialize the tool
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        tool = KavakInfoSearchTool(openai_client=client)
        
        # Test queries
        test_queries = [
            "propuesta de valor",
            "sucursales",
            "documentación para comprar un auto",
            "período de prueba",
            "evaluación de vehículos"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Probando: '{query}'")
            print("-" * 30)
            
            try:
                result = tool.execute({"query": query, "max_results": 3})
                print(f"✅ Resultado:\n{result}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n✅ Pruebas completadas!")
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")

def test_tool_definition():
    """Test the tool definition."""
    print("\n🔧 Testing tool definition")
    print("=" * 30)
    
    try:
        tool = KavakInfoSearchTool()
        definition = tool.get_tool_definition()
        
        print("Tool definition:")
        print(f"Name: {definition['function']['name']}")
        print(f"Description: {definition['function']['description']}")
        print(f"Parameters: {definition['function']['parameters']}")
        
        print("\n✅ Tool definition looks good!")
        
    except Exception as e:
        print(f"❌ Error testing tool definition: {e}")

def main():
    """Main function."""
    print("🧪 KavakInfoSearchTool Test Suite")
    print("=" * 50)
    
    # Test tool definition
    test_tool_definition()
    
    # Test actual functionality
    test_kavak_info_search()

if __name__ == "__main__":
    main() 