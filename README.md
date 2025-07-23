# Proyecto Kavak WhatsApp Bot
![CI](https://github.com/brianstanley/car-ai-agent-wpp-kavak/actions/workflows/ci.yml/badge.svg)


## Diagramas del Sistema

A continuación presento los diagramas principales que describen la arquitectura general del sistema y la arquitectura de prompts utilzada.:

### Diagrama de Arquitectura del Sistema

![System Design](diagrams/system_design.png)

### Diagrama de Flujo de Prompts

![Prompts Diagram](diagrams/prompts_diagram.png)



## Requisitos

- Docker
- Docker Compose
- Python 3.8+ (para desarrollo local)
- Click (incluido en requirements.txt)

## Instalación

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd challenge-kavak
```

### 2. Configurar variables de entorno

Copia el archivo de ejemplo y configura las credenciales presentadas:

```bash
cp env.example .env
```

### 3. Buildear y levantar los servicios (DB y API)

```bash
docker-compose up --build -d
```


### 4. Inicializar la base de datos y cargar agente de ventas.

Ejecuta los siguientes comandos dentro del contenedor de la API

```bash
# Crear tablas de la base de datos
docker-compose exec api python setup.py database

# Cargar datos iniciales (agente comercial de ventas)
docker-compose exec api python seeders.py
```

### 5. Generar embeddings y cargar información de Kavak

Para generar los embeddings de los autos y cargar la información de Kavak:

```bash
# Generar embeddings de autos desde CSV
docker-compose exec api python setup.py generate-car-embeddings

# Extraer información de Kavak desde el sitio web
docker-compose exec api python setup.py kavak-info-ingestion
```

### 6. Acceso a la API

La API estará disponible en: http://localhost:8000/api/v1

- Documentación Swagger: http://localhost:8000/docs
- Documentación ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/v1/health

## Modo Interactivo: Ejecutar el Chat

Para poder interactuar con el agente conversacional de Kavak ya sea para desarrollo o prueba se puede ejecutar de manera local usando el script `chat.py`.

### ¿Cómo ejecutarlo?



```bash
docker-compose exec api python chat.py
```

Vas a ver un prompt donde puedes escribir mensajes y recibir respuestas del agente. Usa `/quit` o `/exit` para salir del chat.

Esto eliminará todas las tablas y las creará nuevamente desde cero.

## Comandos útiles

### Setup.py Commands

El script `setup.py` ahora usa Click y proporciona varios comandos útiles:

```bash
# Ver todos los comandos disponibles
docker-compose exec api python setup.py --help

# Comandos de base de datos
docker-compose exec api python setup.py database              # Crear tablas.
docker-compose exec api python setup.py database --recreate  # Recrear todas las tablas.

# Generar embeddings y datos
docker-compose exec api python setup.py generate-car-embeddings  # Popular la tabla de autos.
docker-compose exec api python setup.py kavak-info-ingestion     # Extraer info de Kavak y generar los embeddings correspondientes.

# Ver ayuda específica de cada comando
docker-compose exec api python setup.py database --help
docker-compose exec api python setup.py generate-car-embeddings --help
docker-compose exec api python setup.py kavak-info-ingestion --help
```

### Otros comandos útiles

- Ejecutar seeders manualmente:
  ```bash
  docker-compose exec api python seeders.py
  ```

## Soporte

Si tenes problemas:

1. Verifica que Docker y Docker Compose estén instalados y ejecutándose.
2. Revisa los logs con `docker-compose logs`.
3. Asegúrate de que el archivo `.env` esté correctamente configurado. 
4. Revisa estar accediendo mediante el versionado v1 a la api.
5. Verifica haber corrido los scripts de migración y generación de embeddings.

