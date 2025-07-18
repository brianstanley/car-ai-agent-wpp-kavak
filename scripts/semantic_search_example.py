#!/usr/bin/env python3
"""
Simple example of how to use semantic search for cars.
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.test_semantic_search import SemanticSearchTester

# Load environment variables
load_dotenv()

def example_semantic_search():
    """Example of basic semantic search."""
    print("🚗 Car Semantic Search Example")
    print("=" * 40)
    
    try:
        # Initialize the search tester
        tester = SemanticSearchTester()
        
        # Example 1: Basic semantic search
        print("\n1️⃣ Basic Semantic Search")
        query = "toyota corolla económico"
        results = tester.search_cars_semantic(query, limit=3)
        tester.print_results(query, results)
        
        # Example 2: Search with filters
        print("\n2️⃣ Hybrid Search with Filters")
        query = "auto confiable"
        filters = {
            "price_max": 300000,
            "year_min": 2019,
            "bluetooth": True
        }
        results = tester.search_cars_hybrid(query, filters, limit=3)
        tester.print_results(query, results, "Hybrid")
        
        # Example 3: Luxury car search
        print("\n3️⃣ Luxury Car Search")
        query = "bmw lujo deportivo"
        filters = {
            "price_min": 400000,
            "car_play": True
        }
        results = tester.search_cars_hybrid(query, filters, limit=3)
        tester.print_results(query, results, "Hybrid")
        
        print("\n✅ Examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in example: {e}")

def interactive_search():
    """Interactive semantic search demo."""
    print("\n🎯 Interactive Semantic Search")
    print("=" * 40)
    
    try:
        tester = SemanticSearchTester()
        
        while True:
            print("\nEnter your search query (or 'quit' to exit):")
            query = input("🔍 Query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                print("❌ Please enter a valid query")
                continue
            
            try:
                # Ask for filters
                print("\nAdd filters? (y/n):")
                use_filters = input().strip().lower() == 'y'
                
                filters = None
                if use_filters:
                    filters = {}
                    
                    print("Enter make (or press Enter to skip):")
                    make = input().strip()
                    if make:
                        filters['make'] = make
                    
                    print("Enter max price (or press Enter to skip):")
                    price_max = input().strip()
                    if price_max:
                        filters['price_max'] = float(price_max)
                    
                    print("Enter min year (or press Enter to skip):")
                    year_min = input().strip()
                    if year_min:
                        filters['year_min'] = int(year_min)
                    
                    print("Require Bluetooth? (y/n):")
                    bluetooth = input().strip().lower() == 'y'
                    filters['bluetooth'] = bluetooth
                    
                    print("Require CarPlay? (y/n):")
                    car_play = input().strip().lower() == 'y'
                    filters['car_play'] = car_play
                
                # Perform search
                if filters:
                    results = tester.search_cars_hybrid(query, filters, limit=5)
                    tester.print_results(query, results, "Hybrid")
                else:
                    results = tester.search_cars_semantic(query, limit=5)
                    tester.print_results(query, results)
                    
            except Exception as e:
                print(f"❌ Error performing search: {e}")
        
        print("👋 Goodbye!")
        
    except Exception as e:
        print(f"❌ Error in interactive search: {e}")

def main():
    """Main function."""
    print("🚗 Car Semantic Search Demo")
    print("=" * 40)
    
    print("Choose an option:")
    print("1. Run example searches")
    print("2. Interactive search")
    print("3. Both")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        example_semantic_search()
    elif choice == "2":
        interactive_search()
    elif choice == "3":
        example_semantic_search()
        interactive_search()
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 