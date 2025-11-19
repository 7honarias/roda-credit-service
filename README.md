# roda-credit-service

### Paso 1: Configuración del Entorno
```bash
cd roda-credit-service

python3 -m venv venv
venv\Scripts\activate 
pip install -r requirements.txt
```


### Paso 4: Ejecutar Migraciones
```bash
alembic init migrations

alembic revision --autogenerate -m "Initial migration"

alembic upgrade head
```

### Paso 5: Ejecutar el Servicio
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

### Documentación Automática
- Swagger UI: http://localhost:8003/docs

### Health Check
```bash
curl http://localhost:8003/health
```


## Docker
```bash
docker build -t roda-auth .

docker run -p 8001:8001 \
  -e DATABASE_URL=postgresql://usuario:password@host:5432/roda_db \
  -e SECRET_KEY=clave-secreta \
  roda-auth

docker-compose up -d
```

### Servicios Disponibles
- **Auth Service**: http://localhost:8003
- **PostgreSQL**: localhost:5433



### Google Cloud Storage
1. Crear proyecto en GCP
2. Crear bucket y service account
3. Descargar credentials JSON
4. Configurar en `.env`:


```bash
DATABASE_URL=postgresql://postgres:jhon1987@localhost:5432/roda_credit_db

SECRET_KEY=jwt-secret-key-development-roda

ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

ALGORITHM=HS256
GCP_PROJECT_ID=jackiarpet
GCP_BUCKET_NAME=roda-files
CLOUD_PROVIDER=gcp

DEBUG=true
APP_NAME="Roda Auth Service"
APP_VERSION="1.0.0"
```




