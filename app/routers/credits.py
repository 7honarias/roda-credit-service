import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config import settings
from ..schemas import CreditRequest, CreditResponse, CreditStatusUpdate, MessageResponse
from ..utils.database import get_db
from ..utils.security import verify_token
from ..services.credit import credit_service
from ..services.user import user_service
from jose import jwt

router = APIRouter()
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = settings.ALGORITHM
security = HTTPBearer()


def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        role = payload.get("role").upper()

        if role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado, rol insuficiente"
            )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
    return True

@router.post("/credits/", response_model=CreditResponse, status_code=status.HTTP_201_CREATED)
async def create_credit_request(
    credit_data: CreditRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Crear nueva solicitud de crédito
    """
    try:
        user_id = verify_token(credentials.credentials)
        user_exists = await user_service.validate_user_exists(user_id)
        if not user_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        credit = credit_service.create_credit_request(db, user_id, credit_data)
        
        return credit
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear solicitud de crédito: {str(e)}"
        )


@router.get("/credits/", response_model=List[CreditResponse])
async def get_user_credits(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Obtener créditos del usuario autenticado
    """
    try:
        user_id = verify_token(credentials.credentials)
        
        credits = credit_service.get_user_credits(db, user_id, skip, limit)
        return credits
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener créditos: {str(e)}"
        )


@router.get("/credits/{credit_id}", response_model=CreditResponse)
async def get_credit_by_id(
    credit_id: int,
    credentials: HTTPAuthorizationCredentials =Depends(security),
    db: Session = Depends(get_db)
):
    """
    Obtener crédito específico por ID
    """
    try:
        user_id = verify_token(credentials.credentials)
        
        response = credit_service.get_credit_with_schedule(db, credit_id)
        credit = response[0]
        if not credit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crédito no encontrado"
            )
        
        data = await user_service.get_user_info(user_id)
        user_info = data.get("data")
        if not user_service.validate_credit_permissions(user_info, credit.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este crédito"
            )
        
        return credit
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener crédito: {str(e)}"
        )


@router.put("/credits/{credit_id}/status", response_model=CreditResponse)
async def update_credit_status(
    credit_id: int,
    status_data: CreditStatusUpdate,
    credentials: HTTPAuthorizationCredentials =Depends(security),
    db: Session = Depends(get_db)
):
    """
    Actualizar estado del crédito (solo para administradores)
    """
    try:
        user_id = verify_token(credentials.credentials)
        
        data = await user_service.get_user_info(user_id)
        user_info = data.get('data')
        if not user_info.get("is_admin", False) and user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Se requieren permisos de administrador"
            )
        
        credit = credit_service.update_credit_status(db, credit_id, status_data)
        return credit
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar estado: {str(e)}"
        )


@router.post("/credits/{credit_id}/approve", response_model=CreditResponse, dependencies=[Depends(verify_admin)])
async def approve_credit(
    credit_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Aprobar crédito pendiente (solo para administradores)
    """
    try:
        user_id = verify_token(credentials.credentials)
        
        data = await user_service.get_user_info(user_id)
        user_info = data.get('data')
        if not user_info.get("is_admin", False) and user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Se requieren permisos de administrador"
            )
        
        credit = credit_service.approve_credit(db, credit_id)
        return credit
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al aprobar crédito: {str(e)}"
        )


@router.get("/credits/{credit_id}/summary", response_model=dict)
async def get_credit_summary(
    credit_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Obtener resumen detallado del crédito
    """
    try:
        # Verificar token y obtener user_id
        token_data = verify_token(credentials.credentials)
        user_id = int(token_data.get("sub") if isinstance(token_data, dict) else token_data)
        
        credit = credit_service.credit_repository.get(db, credit_id)
        if not credit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crédito no encontrado"
            )
        
        # Verificar permisos
        user_info = await user_service.get_user_info(user_id)
        if not user_service.validate_credit_permissions(user_info, credit.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este crédito"
            )
        
        summary = credit_service.calculate_credit_summary(db, credit_id)
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener resumen: {str(e)}"
        )


@router.get("/credits/{credit_id}/check-status", response_model=dict)
async def check_credit_status(
    credit_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Verificar y actualizar estado del crédito basado en pagos
    """
    try:
        user_id = verify_token(credentials.credentials)
        
        credit = credit_service.get_credit_with_schedule(db, credit_id)[0]
        if not credit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crédito no encontrado"
            )
        
        data = await user_service.get_user_info(user_id)
        user_info = data.get('data')
        if not user_service.validate_credit_permissions(user_info, credit.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este crédito"
            )
        
        status = credit_service.check_credit_status(db, credit_id)
        return {"credit_id": credit_id, "current_status": status}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar estado: {str(e)}"
        )