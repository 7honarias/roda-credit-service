from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime
from ..models import Payment, PaymentSchedule, PaymentStatus
from ..schemas import PaymentRequest, PaymentScheduleUpdate
from .base import BaseRepository


class PaymentRepository(BaseRepository[Payment, PaymentRequest, dict]):
    
    def get_by_credit(self, db: Session, credit_id: int, skip: int = 0, limit: int = 100) -> List[Payment]:
        return db.query(Payment).filter(Payment.credit_id == credit_id).offset(skip).limit(limit).all()
    
    def get_recent_payments(self, db: Session, skip: int = 0, limit: int = 50) -> List[Payment]:
        return db.query(Payment).order_by(desc(Payment.created_at)).offset(skip).limit(limit).all()
    
    def get_payments_by_date_range(self, db: Session, start_date: datetime, end_date: datetime) -> List[Payment]:
        return db.query(Payment).filter(
            and_(
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date
            )
        ).all()
    
    def get_total_payments_by_credit(self, db: Session, credit_id: int) -> float:
        result = db.query(Payment).filter(
            and_(
                Payment.credit_id == credit_id,
                Payment.status == PaymentStatus.PAID
            )
        ).all()
        return sum(payment.amount for payment in result)


class PaymentScheduleRepository(BaseRepository[PaymentSchedule, dict, PaymentScheduleUpdate]):
    
    def get_by_credit(self, db: Session, credit_id: int) -> List[PaymentSchedule]:
        return db.query(PaymentSchedule).filter(
            PaymentSchedule.credit_id == credit_id
        ).order_by(PaymentSchedule.installment_number).all()
    
    def get_pending_installments(self, db: Session, credit_id: int) -> List[PaymentSchedule]:
        return db.query(PaymentSchedule).filter(
            and_(
                PaymentSchedule.credit_id == credit_id,
                PaymentSchedule.is_paid == False
            )
        ).order_by(PaymentSchedule.installment_number).all()
    
    def get_overdue_installments(self, db: Session, credit_id: int = None) -> List[PaymentSchedule]:
        today = datetime.now()
        query = db.query(PaymentSchedule).filter(
            and_(
                PaymentSchedule.is_paid == False,
                PaymentSchedule.due_date < today
            )
        )
        
        if credit_id:
            query = query.filter(PaymentSchedule.credit_id == credit_id)
        
        return query.all()
    
    def mark_as_paid(self, db: Session, schedule_id: int, payment_date: Optional[datetime] = None) -> Optional[PaymentSchedule]:
        schedule = self.get(db, schedule_id)
        if schedule:
            schedule.is_paid = True
            schedule.paid_date = payment_date or datetime.now()
            db.commit()
            db.refresh(schedule)
        return schedule
    
    def get_installment_by_number(self, db: Session, credit_id: int, installment_number: int) -> Optional[PaymentSchedule]:
        return db.query(PaymentSchedule).filter(
            and_(
                PaymentSchedule.credit_id == credit_id,
                PaymentSchedule.installment_number == installment_number
            )
        ).first()
    
    def get_next_installment(self, db: Session, credit_id: int) -> Optional[PaymentSchedule]:
        return db.query(PaymentSchedule).filter(
            and_(
                PaymentSchedule.credit_id == credit_id,
                PaymentSchedule.is_paid == False
            )
        ).order_by(PaymentSchedule.installment_number).first()


payment_repository = PaymentRepository(Payment)
payment_schedule_repository = PaymentScheduleRepository(PaymentSchedule)