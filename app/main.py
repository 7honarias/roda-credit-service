from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.utils.database import engine, Base
from app.config.settings import settings
from app.routers import credits_router, payments_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando Credit Management Service...")
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas de base de datos creadas exitosamente")
    except Exception as e:
        logger.error(f"Error al crear tablas: {e}")
    
    yield
    
    logger.info("Cerrando Credit Management Service...")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(credits_router, prefix="/api/v1", tags=["credits"])
app.include_router(payments_router, prefix="/api/v1", tags=["payments"])


@app.get("/", tags=["root"])
async def root():
    return {
        "service": "Credit Management API",
        "version": settings.API_VERSION,
        "status": "active",
        "description": "Microservicio para gestión de créditos y pagos"
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "credit-service",
        "version": settings.API_VERSION
    }


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "detail": str(exc),
            "type": "validation_error"
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": "El recurso solicitado no fue encontrado",
            "type": "not_found"
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    logger.error(f"Error interno del servidor: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "Error interno del servidor",
            "type": "internal_error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    )