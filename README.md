# Proyecto Kavak WhatsApp Bot

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
# Edita .env con tus credenciales reales si es necesario
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

- Verificar la conexión a la base de datos:
  ```bash
  docker-compose exec api python -m scripts.check_db
  ```
- Ejecutar seeders manualmente:
  ```bash
  docker-compose exec api python seeders.py
  ```

## Soporte

Si tienes problemas:

1. Verifica que Docker y Docker Compose estén instalados y ejecutándose.
2. Revisa los logs con `docker-compose logs`.
3. Asegúrate de que el archivo `.env` esté correctamente configurado. 
4. Revisa estar accediendo mediante el versionado v1 a la api.
5. Verifica haber corrido los scripts de migración y generación de embeddings.