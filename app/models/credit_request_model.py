from sqlalchemy import Column, Integer, DateTime, Numeric, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..utils.database import Base
from .enums import CreditStatus

class CreditRequest(Base):
    __tablename__ = "credit_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    requested_amount = Column(Numeric(10, 2), nullable=False)
    requested_term_months = Column(Integer, nullable=False)
    requested_interest_rate = Column(Numeric(5, 2), nullable=False)
    status = Column(Enum(CreditStatus), default=CreditStatus.PENDING)
    rejection_reason = Column(Text, nullable=True)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
