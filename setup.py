#!/usr/bin/env python3
"""
Setup script for the chatbot memory system.
This script helps with initial project setup and verification.
"""
import argparse
import subprocess
import sys
from pathlib import Path

def run_command(command, description, ignore_errors=False):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        if ignore_errors:
            print(f"⚠️  {description} failed (ignored): {e}")
            return True
        else:
            print(f"❌ {description} failed: {e}")
            print(f"Error output: {e.stderr}")
            return False

def check_docker():
    """Check if Docker is available."""
    return run_command("docker --version", "Checking Docker installation")

def check_docker_compose():
    """Check if Docker Compose is available."""
    return run_command("docker-compose --version", "Checking Docker Compose installation")

def check_python_dependencies():
    """Check if Python dependencies are installed."""
    try:
        import psycopg2
        import pydantic
        import dotenv
        print("✅ Python dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path("env.example")

    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        try:
            with open(env_example, 'r') as src:
                content = src.read()
            with open(env_file, 'w') as dst:
                dst.write(content)
            print("✅ .env file created successfully")
            print("⚠️  Please edit .env file with your actual credentials")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    elif env_file.exists():
        print("✅ .env file already exists")
        return True
    else:
        print("❌ env.example file not found")
        return False

def start_database():
    """Start the PostgreSQL database with Docker Compose."""
    return run_command("docker-compose up -d", "Starting PostgreSQL database")

def test_database_connection():
    """Test the database connection using the main script."""
    # Run from project root to ensure modules can be found
    return run_command("python -m scripts.check_db", "Testing database connection")

def main():
    parser = argparse.ArgumentParser(description="Setup script for the chatbot memory system")
    parser.add_argument('--reset-db', action='store_true', help="Reset the database by dropping and recreating it")
    parser.add_argument('--recreate', action='store_true', help="Remove existing containers and volumes before starting")
    args = parser.parse_args()
    if args.reset_db:
        print("🔄 Resetting database...")
        run_command("docker-compose down -v", "Eliminando base de datos y volumen")
    if args.recreate:
        print("🔄 Eliminando y recreando el contenedor de la base de datos...")
        # Force stop and remove containers
        run_command("docker-compose down -v", "Eliminando contenedor y volumen")
        # Force remove the container if it still exists (ignore if not found)
        run_command("docker rm -f chatbot_memory_db", "Forzando eliminación del contenedor", ignore_errors=True)
        # Remove any dangling containers
        run_command("docker container prune -f", "Limpiando contenedores huérfanos")
        run_command("docker-compose up -d", "Recreando contenedor de la base de datos")

    """Main setup function."""
    print("🚀 Chatbot Memory System - Setup")
    print("=" * 50)

    # Check prerequisites
    if not check_docker():
        print("❌ Docker is required but not found")
        sys.exit(1)

    if not check_docker_compose():
        print("❌ Docker Compose is required but not found")
        sys.exit(1)

    if not check_python_dependencies():
        print("❌ Python dependencies are missing")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

    # Create environment file
    if not create_env_file():
        print("❌ Failed to create environment file")
        sys.exit(1)

    # Start database
    if not start_database():
        print("❌ Failed to start database")
        sys.exit(1)

    # Wait a moment for database to be ready
    print("⏳ Waiting for database to be ready...")
    import time
    time.sleep(5)

    # Test connection
    if not test_database_connection():
        print("❌ Database connection test failed")
        print("Please check your .env file and ensure the database is running")
        sys.exit(1)

    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your OpenAI API key")
    print("2. Run 'python -m scripts.check_db' to verify everything works")
    print("3. Start building your chatbot memory system!")

if __name__ == "__main__":
    main()