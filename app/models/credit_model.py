from sqlalchemy import UUID, Column, Integer, DateTime, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..utils.database import Base
from .enums import CreditStatus

class Credit(Base):
    __tablename__ = "credits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    term_months = Column(Integer, nullable=False)
    status = Column(Enum(CreditStatus), default=CreditStatus.PENDING)
    monthly_payment = Column(Numeric(10, 2), nullable=True)
    remaining_balance = Column(Numeric(10, 2), nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    payments = relationship("Payment", back_populates="credit", cascade="all, delete-orphan")
    payment_schedule = relationship("PaymentSchedule", back_populates="credit", cascade="all, delete-orphan")
