#!/usr/bin/env python3
"""
Setup script for the chatbot memory system.
This script helps with initial project setup and verification.
"""
import logging
import os
import sys

import click
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) # workaround for CI to find the path
from db.database import engine
from kavak_chatbot.models.db import agent
from logging_config import setup_logging

load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)

Base = agent.Base

def recreate_db():
    print("Eliminando y recreando todas las tablas de la base de datos...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Base de datos recreada correctamente.")

def create_db():
    print("Creando tablas si no existen...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas correctamente.")

@click.group()
def cli():
    """Setup script for the Kavak chatbot system.

    Available commands:
    - database: Manage database operations
    - generate-car-embeddings: Generate car embeddings from CSV data
    - kavak-info-ingestion: Extract Kavak information from website
    """
    pass

@cli.command()
@click.option('--recreate', is_flag=True, help="Eliminar y recrear todas las tablas")
def database(recreate):
    """Manage database operations.

    Examples:
        python setup.py database              # Create tables if they don't exist
        python setup.py database --recreate  # Drop and recreate all tables
    """
    if recreate:
        recreate_db()
    else:
        create_db()

@cli.command()
def generate_car_embeddings():
    """Generate car embeddings from CSV data and store in database.

    This command reads car data from data/sample_caso_ai_engineer.csv,
    generates embeddings for each car description, and stores them in the database.

    Example:
        python setup.py generate-car-embeddings
    """
    from kavak_chatbot.scripts.generate_car_embeddings import run_parse_cars_to_database
    run_parse_cars_to_database()

@cli.command()
def kavak_info_ingestion():
    """Extract Kavak information from website and store in database.

    This command scrapes the Kavak website, chunks the content,
    generates embeddings, and stores the information in the database.

    Example:
        python setup.py kavak-info-ingestion
    """
    from kavak_chatbot.scripts.kavak_info_ingestion import run_kavak_info_ingestion
    run_kavak_info_ingestion()

if __name__ == "__main__":
    cli()