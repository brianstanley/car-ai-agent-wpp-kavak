# Proyecto Kavak WhatsApp Bot


## Diagramas del Sistema

A continuación presento los diagramas principales que describen la arquitectura general del sistema y la arquitectura de prompts utilzada.:

### Diagrama de Arquitectura del Sistema

![System Design](diagrams/system_design.png)

### Diagrama de Flujo de Prompts

![Prompts Diagram](diagrams/prompts_diagram.png)


![CI](https://github.com/brianstanley/car-ai-agent-wpp-kavak/actions/workflows/ci.yml/badge.svg)

## Requisitos

- Docker
- Docker Compose

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
docker-compose exec api python setup.py

docker-compose exec api python seeders.py
```
Esto generara un agente comercial de ventas de Kavak.

Luego para generar los embeddings de los autos y cargar la información de Kavak:

```bash
docker-compose exec api python scripts/generate_car_embeddings.py

docker-compose exec api python scripts/kavak_info_ingestion.py
```

### 5. Acceso a la API

La API estará disponible en: http://localhost:8000/api/v1

- Documentación Swagger: http://localhost:8000/docs
- Documentación ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### 6. (Opcional) Recrear la base de datos y el contenedor

Si necesitas eliminar y volver a crear la base de datos y el contenedor (por ejemplo, para un entorno limpio), ejecuta:

```bash
docker-compose exec api python setup.py --recreate
```

Esto eliminará el contenedor y el volumen de la base de datos, y los creará nuevamente desde cero.

## Comandos útiles
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

## Modo Interactivo: Ejecutar el Chat

Para poder interactuar con el agente conversacional de Kavak ya sea para desarrollo o prueba se puede ejecutar de manera local usando el script `chat.py`. 

### ¿Cómo ejecutarlo?

Asegúrate de tener las dependencias instaladas y las variables de entorno configuradas. Luego ejecuta:

```bash
python chat.py
```

Vas a ver un prompt donde puedes escribir mensajes y recibir respuestas del agente. Usa `/quit` o `/exit` para salir del chat.

