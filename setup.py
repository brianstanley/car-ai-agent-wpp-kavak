import logging

import click

from db.database import engine
from kavak_chatbot.models.db import agent

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
    pass

@cli.command()
@click.option('--recreate', is_flag=True, help="Eliminar y recrear todas las tablas")
def database(recreate):
    if recreate:
        recreate_db()
    else:
        create_db()

@cli.command()
def generate_car_embeddings():
    from kavak_chatbot.scripts.generate_car_embeddings import run_parse_cars_to_database
    run_parse_cars_to_database()

@cli.command()
def kavak_info_ingestion():
    from kavak_chatbot.scripts.kavak_info_ingestion import run_kavak_info_ingestion
    run_kavak_info_ingestion()

if __name__ == "__main__":
    cli()