from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class CreditBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Monto del crédito")
    interest_rate: Decimal = Field(..., gt=0, le=100, description="Tasa de interés anual (%)")
    term_months: int = Field(..., gt=0, le=360, description="Plazo en meses")


class CreditRequest(CreditBase):
    pass


class CreditResponse(CreditBase):
    id: int
    user_id: UUID
    status: str
    monthly_payment: Optional[Decimal] = None
    remaining_balance: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CreditUpdate(BaseModel):
    status: Optional[str] = None

class CreditCreate(BaseModel):
    status: Optional[str] = None


class CreditStatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None


class CreditSummary(BaseModel):
    id: int
    amount: Decimal
    status: str
    monthly_payment: Optional[Decimal]
    remaining_balance: Optional[Decimal]
    created_at: datetime
    
    class Config:
        from_attributes = True

class CreditWithSchedule(BaseModel):
    id: int
    amount: Decimal
    status: str
    monthly_payment: Optional[Decimal]
    remaining_balance: Optional[Decimal]
    created_at: datetime
    
    class Config:
        from_attributes = True