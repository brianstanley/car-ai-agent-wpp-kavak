#!/usr/bin/env python3
"""
Test script for semantic search using SQLAlchemy and vector similarity.
"""

import os
import sys
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal
from db.config import Config

# Load environment variables
load_dotenv()

class SemanticSearchTester:
    """Test class for semantic search functionality."""
    
    def __init__(self):
        """Initialize the semantic search tester."""
        # Validate environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.embedding_model = "text-embedding-3-small"
        
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for the given text using OpenAI API.
        
        Args:
            text: Text to embed
            
        Returns:
            List[float]: Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            raise
    
    def search_cars_semantic(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search cars using semantic similarity.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of car results with similarity scores
        """
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            # Convert embedding to PostgreSQL vector format
            embedding_str = f"[{','.join(map(str, query_embedding))}]"
            
            # Perform semantic search using SQLAlchemy
            session = SessionLocal()
            
            try:
                # SQL query with vector similarity
                sql_query = text("""
                    SELECT 
                        stock_id,
                        make,
                        model,
                        year,
                        price,
                        km,
                        bluetooth,
                        car_play,
                        descripcion,
                        embedding <-> :embedding as similarity_score
                    FROM cars
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <-> :embedding
                    LIMIT :limit
                """)
                
                result = session.execute(sql_query, {
                    'embedding': embedding_str,
                    'limit': limit
                })
                
                # Convert results to list of dictionaries
                cars = []
                for row in result:
                    car = {
                        'stock_id': row.stock_id,
                        'make': row.make,
                        'model': row.model,
                        'year': row.year,
                        'price': float(row.price) if row.price else None,
                        'km': row.km,
                        'bluetooth': row.bluetooth,
                        'car_play': row.car_play,
                        'descripcion': row.descripcion,
                        'similarity_score': float(row.similarity_score)
                    }
                    cars.append(car)
                
                return cars
                
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            raise
    
    def search_cars_hybrid(self, query: str, filters: Dict[str, Any] | None = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search cars using semantic similarity with additional filters.
        
        Args:
            query: Search query
            filters: Additional filters (make, model, year, price_range, etc.)
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of car results with similarity scores
        """
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            embedding_str = f"[{','.join(map(str, query_embedding))}]"
            
            session = SessionLocal()
            
            try:
                # Build dynamic SQL query with filters
                base_sql = """
                    SELECT 
                        stock_id,
                        make,
                        model,
                        year,
                        price,
                        km,
                        bluetooth,
                        car_play,
                        descripcion,
                        embedding <-> :embedding as similarity_score
                    FROM cars
                    WHERE embedding IS NOT NULL
                """
                
                params = {'embedding': embedding_str, 'limit': limit}
                
                # Add filters if provided
                if filters:
                    conditions = []
                    
                    if filters.get('make'):
                        conditions.append("make ILIKE :make")
                        params['make'] = f"%{filters['make']}%"
                    
                    if filters.get('model'):
                        conditions.append("model ILIKE :model")
                        params['model'] = f"%{filters['model']}%"
                    
                    if filters.get('year_min'):
                        conditions.append("year >= :year_min")
                        params['year_min'] = filters['year_min']
                    
                    if filters.get('year_max'):
                        conditions.append("year <= :year_max")
                        params['year_max'] = filters['year_max']
                    
                    if filters.get('price_min'):
                        conditions.append("price >= :price_min")
                        params['price_min'] = filters['price_min']
                    
                    if filters.get('price_max'):
                        conditions.append("price <= :price_max")
                        params['price_max'] = filters['price_max']
                    
                    if filters.get('bluetooth') is not None:
                        conditions.append("bluetooth = :bluetooth")
                        params['bluetooth'] = filters['bluetooth']
                    
                    if filters.get('car_play') is not None:
                        conditions.append("car_play = :car_play")
                        params['car_play'] = filters['car_play']
                    
                    if conditions:
                        base_sql += " AND " + " AND ".join(conditions)
                
                base_sql += " ORDER BY embedding <-> :embedding LIMIT :limit"
                
                sql_query = text(base_sql)
                result = session.execute(sql_query, params)
                
                # Convert results to list of dictionaries
                cars = []
                for row in result:
                    car = {
                        'stock_id': row.stock_id,
                        'make': row.make,
                        'model': row.model,
                        'year': row.year,
                        'price': float(row.price) if row.price else None,
                        'km': row.km,
                        'bluetooth': row.bluetooth,
                        'car_play': row.car_play,
                        'descripcion': row.descripcion,
                        'similarity_score': float(row.similarity_score)
                    }
                    cars.append(car)
                
                return cars
                
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ Error in hybrid search: {e}")
            raise
    
    def print_results(self, query: str, results: List[Dict[str, Any]], search_type: str = "Semantic"):
        """
        Print search results in a formatted way.
        
        Args:
            query: Original search query
            results: Search results
            search_type: Type of search performed
        """
        print(f"\n🔍 {search_type} Search Results for '{query}':")
        print("=" * 80)
        
        if not results:
            print("❌ No results found")
            return
        
        for i, car in enumerate(results, 1):
            print(f"\n{i}. {car['make']} {car['model']} {car['year']}")
            print(f"   Stock ID: {car['stock_id']}")
            print(f"   Price: ${car['price']:,.0f}" if car['price'] else "   Price: N/A")
            print(f"   KM: {car['km']:,} km")
            print(f"   Features: Bluetooth: {'✅' if car['bluetooth'] else '❌'}, CarPlay: {'✅' if car['car_play'] else '❌'}")
            print(f"   Similarity Score: {car['similarity_score']:.4f}")
            print(f"   Description: {car['descripcion']}")
            print("-" * 40)

def main():
    """Main function to run semantic search tests."""
    print("🧠 Semantic Search Test")
    print("=" * 50)
    
    try:
        # Initialize tester
        tester = SemanticSearchTester()
        
        # Test queries
        test_queries = [
            "chevrolet barato",
            "auto chico",
            "menos de 300000",
            "auto con bluetooth y carplay",
            "toyota corolla 2020",
            "bmw lujo",
            "suv familiar",
            "auto deportivo",
            "honda confiable",
            "nissan económico"
        ]
        
        print("🚀 Running semantic search tests...")
        
        for query in test_queries:
            try:
                # Perform semantic search
                results = tester.search_cars_semantic(query, limit=3)
                tester.print_results(query, results, "Semantic")
                
            except Exception as e:
                print(f"❌ Error testing query '{query}': {e}")
        
        print("\n" + "=" * 50)
        print("🔍 Testing hybrid search with filters...")
        
        # Test hybrid search with filters
        hybrid_tests = [
            {
                "query": "toyota confiable",
                "filters": {"make": "Toyota", "year_min": 2020}
            },
            {
                "query": "auto económico",
                "filters": {"price_max": 250000, "bluetooth": True}
            },
            {
                "query": "suv lujo",
                "filters": {"price_min": 400000, "car_play": True}
            }
        ]
        
        for test in hybrid_tests:
            try:
                results = tester.search_cars_hybrid(
                    query=test["query"],
                    filters=test["filters"],
                    limit=3
                )
                tester.print_results(test["query"], results, "Hybrid")
                
            except Exception as e:
                print(f"❌ Error testing hybrid search '{test['query']}': {e}")
        
        print("\n🎉 Semantic search tests completed!")
        
    except Exception as e:
        print(f"❌ Error initializing semantic search tester: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main() 