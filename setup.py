#!/usr/bin/env python3
"""
Setup script for the chatbot memory system.
This script helps with initial project setup and verification.
"""
import argparse
from db.database import engine
from models.db import agent, chat_session, conversation_memory, kavak_info, persona, summary, user  # Asegura que todos los modelos estén importados
from sqlalchemy.orm import declarative_base

# Si tienes un Base centralizado, usa ese. Si no, crea uno aquí:
Base = agent.Base  # Ajusta si tu Base está en otro módulo

def recreate_db():
    print("Eliminando y recreando todas las tablas de la base de datos...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Base de datos recreada correctamente.")

def create_db():
    print("Creando tablas si no existen...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas correctamente.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup de la base de datos")
    parser.add_argument('--recreate', action='store_true', help="Eliminar y recrear todas las tablas")
    args = parser.parse_args()

    if args.recreate:
        recreate_db()
    else:
        create_db()