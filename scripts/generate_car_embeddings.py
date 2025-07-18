#!/usr/bin/env python3
"""
Script to generate embeddings for car data and save them to the cars table.
"""

import pandas as pd
import os
import sys
from typing import List, Dict, Any
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal
from db.config import Config

# Load environment variables
load_dotenv()

# Configuration
CSV_PATH = "sample_caso_ai_engineer.csv"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536  # For text-embedding-3-small

def validate_environment():
    """Validate that required environment variables are set."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        sys.exit(1)
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ Error: DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    print("✅ Environment variables validated")

def create_description(row: pd.Series) -> str:
    """
    Create a comprehensive description of the car from the row data.
    
    Args:
        row: Pandas Series containing car data
        
    Returns:
        str: Formatted description of the car
    """
    # Handle boolean values for features
    bluetooth = "con bluetooth" if row.get("bluetooth") == "Sí" else "sin bluetooth"
    car_play = "con CarPlay" if row.get("car_play") == "Sí" else "sin CarPlay"
    
    # Build description
    desc_parts = [
        f"{row['make']} {row['model']} {row['year']}",
        f"versión {row['version']}",
        f"{row['km']:,} km",
        f"${row['price']:,.0f}",
        bluetooth,
        car_play
    ]
    
    # Add dimensions if available
    if pd.notna(row.get('largo')) and pd.notna(row.get('ancho')) and pd.notna(row.get('altura')):
        desc_parts.append(f"{row['largo']}m de largo, {row['ancho']}m de ancho, {row['altura']}m de alto")
    
    return ", ".join(desc_parts)

def generate_embedding(text: str, client: OpenAI) -> List[float]:
    """
    Generate embedding for the given text using OpenAI API.
    
    Args:
        text: Text to embed
        client: OpenAI client instance
        
    Returns:
        List[float]: Embedding vector
    """
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        raise

def insert_car_to_database(
    stock_id: str,
    km: int,
    price: float,
    make: str,
    model: str,
    year: int,
    version: str,
    bluetooth: bool,
    largo: float | None,
    ancho: float | None,
    altura: float | None,
    car_play: bool,
    descripcion: str,
    embedding: List[float],
    session
) -> bool:
    """
    Insert car data with embedding into the database.
    
    Args:
        stock_id: Stock ID of the car
        km: Kilometers
        price: Price
        make: Car make
        model: Car model
        year: Year
        version: Version
        bluetooth: Bluetooth availability
        largo: Length
        ancho: Width
        altura: Height
        car_play: CarPlay availability
        descripcion: Description
        embedding: Embedding vector
        session: Database session
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert embedding to PostgreSQL vector format
        embedding_str = f"[{','.join(map(str, embedding))}]"
        
        # Insert the car data
        query = text("""
            INSERT INTO cars (
                stock_id, km, price, make, model, year, version, 
                bluetooth, largo, ancho, altura, car_play, descripcion, embedding
            ) VALUES (
                :stock_id, :km, :price, :make, :model, :year, :version,
                :bluetooth, :largo, :ancho, :altura, :car_play, :descripcion, :embedding
            )
        """)
        
        session.execute(query, {
            'stock_id': stock_id,
            'km': km,
            'price': price,
            'make': make,
            'model': model,
            'year': year,
            'version': version,
            'bluetooth': bluetooth,
            'largo': largo,
            'ancho': ancho,
            'altura': altura,
            'car_play': car_play,
            'descripcion': descripcion,
            'embedding': embedding_str
        })
        
        session.commit()
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error inserting car {stock_id}: {e}")
        session.rollback()
        return False
    except Exception as e:
        print(f"❌ Error inserting car {stock_id}: {e}")
        session.rollback()
        return False

def process_csv_data():
    """Process the CSV file and generate embeddings for all cars."""
    print("🚗 Starting car embedding generation...")
    
    # Validate environment
    validate_environment()
    
    # Check if CSV file exists
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: CSV file '{CSV_PATH}' not found")
        sys.exit(1)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Read CSV data
    print(f"📖 Reading CSV file: {CSV_PATH}")
    try:
        df = pd.read_csv(CSV_PATH)
        print(f"✅ Loaded {len(df)} cars from CSV")
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        sys.exit(1)
    
    # Initialize database session
    session = SessionLocal()
    
    try:
        # Process each car
        successful_inserts = 0
        failed_inserts = 0
        
        print("🔄 Processing cars and generating embeddings...")
        
        for index, row in tqdm(df.iterrows(), total=len(df), desc="Processing cars"):
            try:
                # Create description
                descripcion = create_description(row)
                
                # Generate embedding
                embedding = generate_embedding(descripcion, client)
                
                # Prepare data for insertion
                stock_id = str(row['stock_id'])
                km = int(row['km'])
                price = float(row['price'])
                make = str(row['make'])
                model = str(row['model'])
                year = int(row['year'])
                version = str(row['version'])
                bluetooth = row.get('bluetooth') == 'Sí'
                largo = float(row['largo']) if pd.notna(row.get('largo')) else None
                ancho = float(row['ancho']) if pd.notna(row.get('ancho')) else None
                altura = float(row['altura']) if pd.notna(row.get('altura')) else None
                car_play = row.get('car_play') == 'Sí'
                
                # Insert into database
                success = insert_car_to_database(
                    stock_id=stock_id,
                    km=km,
                    price=price,
                    make=make,
                    model=model,
                    year=year,
                    version=version,
                    bluetooth=bluetooth,
                    largo=largo,
                    ancho=ancho,
                    altura=altura,
                    car_play=car_play,
                    descripcion=descripcion,
                    embedding=embedding,
                    session=session
                )
                
                if success:
                    successful_inserts += 1
                else:
                    failed_inserts += 1
                    
            except Exception as e:
                print(f"❌ Error processing car {row.get('stock_id', 'unknown')}: {e}")
                failed_inserts += 1
        
        # Print summary
        print("\n" + "="*50)
        print("📊 PROCESSING SUMMARY")
        print("="*50)
        print(f"✅ Successful inserts: {successful_inserts}")
        print(f"❌ Failed inserts: {failed_inserts}")
        print(f"📈 Total processed: {successful_inserts + failed_inserts}")
        print(f"📈 Success rate: {(successful_inserts / (successful_inserts + failed_inserts) * 100):.1f}%")
        
        if successful_inserts > 0:
            print("\n🎉 Car embedding generation completed successfully!")
        else:
            print("\n❌ No cars were successfully processed.")
            
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        sys.exit(1)
    finally:
        session.close()

def main():
    """Main function to run the car embedding generation."""
    print("🤖 Car Embedding Generator")
    print("=" * 50)
    
    try:
        process_csv_data()
    except KeyboardInterrupt:
        print("\n⏹️ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 