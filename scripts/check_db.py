#!/usr/bin/env python3
"""
Main script for the chatbot memory system.
This script connects to the database and lists the created tables.
"""

import sys
from db.database import DatabaseManager
from db.config import Config

def main():
    """Main function to test database connection and list tables."""
    print("🤖 Chatbot Memory System - Database Test")
    print("=" * 50)

    # Validate configuration
    try:
        Config.validate()
        print("✅ Configuration validated successfully")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file and ensure all required variables are set.")
        sys.exit(1)

    # Initialize database manager
    db_manager = DatabaseManager()

    # Test database connection
    print("\n🔌 Testing database connection...")
    if db_manager.test_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        print("Make sure the PostgreSQL container is running with:")
        print("docker-compose up -d")
        sys.exit(1)

    # Check pgvector extension
    print("\n🔍 Checking pgvector extension...")
    if db_manager.check_pgvector_extension():
        print("✅ pgvector extension is installed")
    else:
        print("❌ pgvector extension not found")
        print("The database should have pgvector extension enabled")

    # List tables
    print("\n📋 Listing database tables...")
    tables = db_manager.list_tables()

    if tables:
        print(f"✅ Found {len(tables)} table(s):")
        for i, table_name in enumerate(tables, 1):
            print(f"  {i}. {table_name}")

        # Show detailed info for each table
        print("\n📊 Table details:")
        for table_name in tables:
            table_info = db_manager.get_table_info(table_name)
            if table_info:
                print(f"\n📋 Table: {table_info['table_name']}")
                for col in table_info['columns']:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    print(f"  - {col['column_name']}: {col['data_type']} {nullable}{default}")
    else:
        print("❌ No tables found in the database")
        print("Make sure the init.sql script was executed properly")

    print("\n🎉 Database setup complete!")

if __name__ == "__main__":
    main()