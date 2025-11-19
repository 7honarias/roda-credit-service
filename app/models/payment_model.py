from sqlalchemy import Column, Integer, DateTime, Numeric, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..utils.database import Base
from .enums import PaymentStatus


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)

    credit_id = Column(Integer, ForeignKey("credits.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime(timezone=True), nullable=False)
    payment_method = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PAID)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    credit = relationship("Credit", back_populates="payments")
