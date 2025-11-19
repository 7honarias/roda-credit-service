from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..schemas import (
    PaymentRequest, PaymentResponse, PaymentScheduleResponse, 
    PaymentScheduleUpdate, MessageResponse, CreditWithSchedule
)
from ..utils.database import get_db
from ..utils.security import verify_token
from ..services.payment import payment_service
from ..services.credit import credit_service
from ..services.user import user_service

router = APIRouter()

security = HTTPBearer()


@router.post("/payments/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Registrar un nuevo pago
    """
    try:
        user_id = verify_token(credentials.credentials)
        
        user_exists = await user_service.validate_user_exists(user_id)
        if not user_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        payment = payment_service.create_payment(db, user_id, payment_data)
        return payment
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar pago: {str(e)}"
        )


@router.get("/credits/{credit_id}/payments", response_model=List[PaymentResponse])
async def get_credit_payments(
    credit_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Obtener pagos de un crédito específico
    """
    try:
        user_id = verify_token(credentials.credentials)
        
        payments = payment_service.get_credit_payments(db, user_id, credit_id, skip, limit)
        return payments
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener pagos: {str(e)}"
        )


@router.get("/payments/", response_model=List[PaymentResponse])
async def get_user_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los pagos del usuario
    """
    try:
        user_id = verify_token(credentials.credentials)
        
        payments = payment_service.get_user_payments(db, user_id, skip, limit)
        return payments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener pagos: {str(e)}"
        )


@router.get("/payments/summary", response_model=dict)
async def get_payment_summary(
    credit_id: int = Query(None, description="ID específico de crédito (opcional)"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Obtener resumen de pagos del usuario
    """
    try:
        # Verificar token y obtener user_id
        user_id = verify_token(credentials.credentials)
        
        summary = payment_service.calculate_payment_summary(db, user_id, credit_id)
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener resumen: {str(e)}"
        )


@router.get("/credits/{credit_id}/schedule", response_model=List[PaymentScheduleResponse])
async def get_payment_schedule(
    credit_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Obtener calendario de pagos de un crédito
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
        print("validateeeeee", user_info)
        if not user_service.validate_credit_permissions(user_info, credit.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este crédito"
            )
        
        schedule = credit_service.get_credit_with_schedule(db, credit_id)[1]
        return schedule
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener calendario: {str(e)}"
        )


@router.put("/schedule/{schedule_id}", response_model=PaymentScheduleResponse)
async def update_installment_payment(
    schedule_id: int,
    update_data: PaymentScheduleUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Marcar una cuota específica como pagada
    """
    try:
        # Verificar token y obtener user_id
        user_id = verify_token(credentials.credentials)
        
        schedule = payment_service.mark_installment_as_paid(
            db, user_id, schedule_id, update_data.paid_date
        )
        return schedule
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar cuota: {str(e)}"
        )


@router.get("/credits/{credit_id}/with-schedule", response_model=CreditWithSchedule)
async def get_credit_with_schedule(
    credit_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Obtener crédito completo con su calendario de pagos
    """
    try:
        user_id = verify_token(credentials.credentials)
        
        credit, schedule = credit_service.get_credit_with_schedule(db, credit_id)
        
        user_info = await user_service.get_user_info(user_id)
        if not user_service.validate_credit_permissions(user_info, credit.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este crédito"
            )
        
        return {
            "credit": credit,
            "payment_schedule": schedule
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener crédito completo: {str(e)}"
        )


@router.post("/schedule/{schedule_id}/auto-payment", response_model=MessageResponse)
async def process_automatic_payment(
    schedule_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Procesar pago automático de una cuota vencida (solo administradores)
    """
    try:
        # Verificar token y obtener user_id
        user_id = verify_token(credentials.credentials)
        
        # Verificar permisos de administrador
        user_info = await user_service.get_user_info(user_id)
        if not user_info.get("is_admin", False) and user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Se requieren permisos de administrador"
            )
        
        success = payment_service.process_automatic_payment(db, schedule_id)
        if success:
            return MessageResponse(message="Pago automático procesado exitosamente")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo procesar el pago automático"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar pago automático: {str(e)}"
        )


@router.get("/schedule/overdue", response_model=List[PaymentScheduleResponse])
async def get_overdue_installments(
    credit_id: int = Query(None, description="ID específico de crédito (opcional)"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Obtener cuotas vencidas (solo para administradores)
    """
    try:
        user_id = verify_token(credentials.credentials)
        
        user_info = await user_service.get_user_info(user_id)
        if not user_info.get("is_admin", False) and user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Se requieren permisos de administrador"
            )
        
        overdue_installments = payment_service.payment_schedule_repository.get_overdue_installments(
            db, credit_id
        )
        return overdue_installments
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener cuotas vencidas: {str(e)}"
        )