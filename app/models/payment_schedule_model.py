from sqlalchemy import Column, Integer, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..utils.database import Base

class PaymentSchedule(Base):
    __tablename__ = "payment_schedule"
    
    id = Column(Integer, primary_key=True, index=True)

    credit_id = Column(Integer, ForeignKey("credits.id"), nullable=False)

    installment_number = Column(Integer, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    principal_amount = Column(Numeric(10, 2), nullable=False)
    interest_amount = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    is_paid = Column(Boolean, default=False)
    paid_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    credit = relationship("Credit", back_populates="payment_schedule")
