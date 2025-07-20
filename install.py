#!/usr/bin/env python3
"""
Script de instalación para el proyecto Kavak WhatsApp Bot.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_header():
    print("=" * 60)
    print("Instalador del Challenge de Kavak - Brian Stanley - Julio 2025.")
    print("=" * 60)
    print()

def print_step(step_number, title):
    print(f"PASO {step_number}: {title}")
    print("-" * 40)

def ask_user(prompt, default="y"):
    while True:
        response = input(f"{prompt} ({'Y/n' if default == 'y' else 'y/N'}): ").strip().lower()
        if response == "":
            response = default
        if response in ['y', 'yes', 's', 'si']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Por favor responde 'y' (sí) o 'n' (no)")

def run_command(command, description, ignore_errors=False):
    print(f"Ejecutando: {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completado")
        return True
    except subprocess.CalledProcessError as e:
        if ignore_errors:
            print(f"⚠ {description} falló (ignorado)")
            return True
        else:
            print(f"✗ {description} falló")
            print(f"Error: {e.stderr}")
            return False

def check_prerequisites():
    """Verificar prerequisitos del sistema."""
    print_step(1, "VERIFICACIÓN DE PREREQUISITOS")

    # Verificar Python
    print("Verificando Python...")
    if sys.version_info < (3, 8):
        print("✗ Se requiere Python 3.8 o superior")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detectado")

    # Verificar Docker
    if not run_command("docker --version", "Verificando Docker"):
        print("✗ Docker es requerido pero no se encontró")
        print("Instala Docker desde: https://docs.docker.com/get-docker/")
        return False

    # Verificar Docker Compose
    if not run_command("docker-compose --version", "Verificando Docker Compose"):
        print("✗ Docker Compose es requerido pero no se encontró")
        return False

    # Verificar archivo requirements.txt
    if not Path("requirements.txt").exists():
        print("✗ Archivo requirements.txt no encontrado")
        return False

    print("✓ Todos los prerequisitos están satisfechos")
    return True

def install_dependencies():
    """Instalar dependencias de Python."""
    print_step(2, "INSTALACIÓN DE DEPENDENCIAS")

    print("Instalando dependencias de Python...")
    if not run_command("pip install -r requirements.txt", "Instalando dependencias"):
        print("✗ Error al instalar dependencias")
        return False

    print("✓ Dependencias instaladas correctamente")
    return True

def setup_environment():
    """Configurar el entorno del proyecto."""
    print_step(3, "CONFIGURACIÓN DEL ENTORNO")

    # Crear archivo .env si no existe
    env_file = Path(".env")
    env_example = Path("env.example")

    if not env_file.exists() and env_example.exists():
        print("Creando archivo .env desde la plantilla...")
        try:
            with open(env_example, 'r') as src:
                content = src.read()
            with open(env_file, 'w') as dst:
                dst.write(content)
            print("✓ Archivo .env creado exitosamente")
            print("IMPORTANTE: Edita el archivo .env con tus credenciales reales")
            print("  - OPENAI_API_KEY: Tu clave de API de OpenAI")
            print("  - DATABASE_URL: URL de conexión a la base de datos")
        except Exception as e:
            print(f"✗ Error al crear archivo .env: {e}")
            return False
    elif env_file.exists():
        print("✓ Archivo .env ya existe")
    else:
        print("✗ Archivo env.example no encontrado")
        return False

    return True

def run_setup_py():
    """Ejecutar setup.py para configurar la base de datos."""
    print_step(4, "CONFIGURACIÓN DE LA BASE DE DATOS")

    print("Configurando base de datos PostgreSQL...")
    if not run_command("python setup.py", "Ejecutando setup.py"):
        print("✗ Error al configurar la base de datos")
        return False

    print("✓ Base de datos configurada correctamente")
    return True

def run_seeders():
    """Ejecutar los seeders para crear datos iniciales."""
    print_step(5, "CREACIÓN DE DATOS INICIALES")

    print("Ejecutando seeders...")
    print("  - Creará un agente comercial de Kavak por defecto")
    print("  - Creará un usuario de prueba")

    if not run_command("python seeders.py", "Ejecutando seeders"):
        print("✗ Error al ejecutar seeders")
        return False

    print("✓ Datos iniciales creados correctamente")
    return True

def upload_car_data():
    """Subir datos de autos desde el CSV."""
    print_step(6, "CARGA DE DATOS DE AUTOS")

    print("Procesando datos de autos desde CSV...")
    print("  - Leerá el archivo CSV con información de autos")
    print("  - Generará embeddings para búsqueda semántica")
    print("  - Almacenará los datos en la base de datos")
    print("  Nota: Este proceso puede tomar varios minutos...")

    if not run_command("python scripts/generate_car_embeddings.py", "Procesando datos de autos"):
        print("✗ Error al procesar datos de autos")
        print("Puedes ejecutar este paso manualmente más tarde con:")
        print("  python scripts/generate_car_embeddings.py")
        return False

    print("✓ Datos de autos cargados correctamente")
    return True

def extract_kavak_info():
    """Extraer información de Kavak y generar embeddings."""
    print_step(7, "EXTRACCIÓN DE INFORMACIÓN DE KAVAK")

    print("Extrayendo información de la página web de Kavak...")
    print("  - Extraerá información de las sedes de Kavak en México")
    print("  - Generará embeddings para búsqueda semántica")
    print("  - Almacenará la información en la base de datos")
    print("  Nota: Este proceso puede tomar unos minutos...")

    if not run_command("python scripts/kavak_info_ingestion.py", "Extrayendo información de Kavak"):
        print("✗ Error al extraer información de Kavak")
        print("Puedes ejecutar este paso manualmente más tarde con:")
        print("  python scripts/kavak_info_ingestion.py")
        return False

    print("✓ Información de Kavak extraída correctamente")
    return True

def start_api():
    """Iniciar la API."""
    print_step(8, "INICIO DE LA API")

    print("Iniciando la API del bot de WhatsApp...")
    print("  - La API estará disponible en: http://localhost:8000")
    print("  - Documentación disponible en: http://localhost:8000/docs")
    print("  - Para detener la API, presiona Ctrl+C")

    # Ejecutar la API
    try:
        print("Iniciando servidor...")
        subprocess.run("python main.py", shell=True, check=True)
    except KeyboardInterrupt:
        print("\nAPI detenida por el usuario")
    except Exception as e:
        print(f"✗ Error al iniciar la API: {e}")
        return False

    return True

def main():
    """Función principal del instalador."""
    print_header()

    # Verificar prerequisitos
    if not check_prerequisites():
        print("\n✗ Los prerequisitos no están satisfechos. Por favor instálalos y vuelve a intentar.")
        sys.exit(1)

    # Instalar dependencias
    if not install_dependencies():
        print("\n✗ Error al instalar dependencias.")
        sys.exit(1)

    # Configurar entorno
    if not setup_environment():
        print("\n✗ Error al configurar el entorno.")
        sys.exit(1)

    # Ejecutar setup.py
    if not run_setup_py():
        print("\n✗ Error al configurar la base de datos.")
        sys.exit(1)

    # Preguntar sobre seeders
    if ask_user("¿Deseas ejecutar los seeders para crear datos iniciales?", "y"):
        if not run_seeders():
            print("\n⚠ Error al ejecutar seeders, pero puedes continuar.")

    # Preguntar sobre datos de autos
    if ask_user("¿Deseas subir los datos de autos desde el CSV?", "y"):
        if not upload_car_data():
            print("\n⚠ Error al cargar datos de autos, pero puedes continuar.")

    # Preguntar sobre información de Kavak
    if ask_user("¿Deseas extraer información de la página web de Kavak?", "y"):
        if not extract_kavak_info():
            print("\n⚠ Error al extraer información de Kavak, pero puedes continuar.")

    # Preguntar sobre iniciar la API
    if ask_user("¿Deseas iniciar la API ahora?", "y"):
        start_api()
    else:
        print("\n✓ Instalación completada!")
        print("\nPara iniciar la API manualmente, ejecuta:")
        print("  python main.py")
        print("\nComandos útiles:")
        print("  - Verificar base de datos: python -m scripts.check_db")
        print("  - Ejecutar seeders: python seeders.py")
        print("  - Cargar datos de autos: python scripts/generate_car_embeddings.py")
        print("  - Extraer info de Kavak: python scripts/kavak_info_ingestion.py")

if __name__ == "__main__":
    main()