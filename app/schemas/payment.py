from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from .credit import CreditResponse


class PaymentBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Monto del pago")
    payment_method: str = Field(..., description="Método de pago: tarjeta, transferencia, efectivo, etc.")
    description: Optional[str] = None


class PaymentRequest(PaymentBase):
    credit_id: int


class PaymentResponse(PaymentBase):
    id: int
    credit_id: int
    status: str
    payment_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentScheduleBase(BaseModel):
    credit_id: int
    installment_number: int
    due_date: datetime
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal


class PaymentScheduleResponse(PaymentScheduleBase):
    id: int
    is_paid: bool
    paid_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentScheduleUpdate(BaseModel):
    is_paid: bool = Field(..., description="Marcar si se pagó la cuota")
    paid_date: Optional[datetime] = Field(None, description="Fecha en que se pagó")

class PaymentScheduleCreate(BaseModel):
    is_paid: bool = Field(..., description="Marcar si se pagó la cuota")
    paid_date: Optional[datetime] = Field(None, description="Fecha en que se pagó")


class CreditWithSchedule(BaseModel):
    credit: 'CreditResponse'
    payment_schedule: List[PaymentScheduleResponse]
    
    class Config:
        from_attributes = True
