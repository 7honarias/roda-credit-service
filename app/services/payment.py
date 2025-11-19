from datetime import datetime
from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from ..models import Payment, PaymentSchedule, PaymentStatus, CreditStatus
from ..schemas import PaymentRequest
from ..repositories import payment_repository, payment_schedule_repository, credit_repository
from .credit import credit_service


class PaymentService:
    
    def create_payment(self, db: Session, user_id: int, payment_data: PaymentRequest) -> Payment:
        credit = credit_repository.get(db, payment_data.credit_id)
        if not credit:
            raise ValueError("Crédito no encontrado")
        
        if str(credit.user_id) != user_id:
            raise ValueError("No tienes permisos para realizar pagos en este crédito")
        
        if credit.status not in [CreditStatus.ACTIVE, CreditStatus.DELINQUENT]:
            raise ValueError(f"No se pueden realizar pagos para créditos en estado: {credit.status.value}")
        
        if payment_data.amount > (credit.remaining_balance or 0):
            raise ValueError("El monto del pago excede el saldo pendiente")
        
        payment_data_dict = payment_data.dict()
        payment_data_dict.update({
            "payment_date": datetime.now(),
            "status": PaymentStatus.PAID
        })
        
        payment = payment_repository.create(db, obj_in=payment_data_dict)
        
        self.update_credit_balance(db, payment.credit_id, payment.amount)
        
        self.check_and_update_credit_status(db, payment.credit_id)
        
        return payment
    
    def update_credit_balance(self, db: Session, credit_id: int, payment_amount: Decimal):
        credit = credit_repository.get(db, credit_id)
        if credit:
            new_balance = (credit.remaining_balance or 0) - payment_amount
            if new_balance < 0:
                new_balance = 0
            
            credit.remaining_balance = round(new_balance, 2)
            db.commit()
            db.refresh(credit)
    
    def check_and_update_credit_status(self, db: Session, credit_id: int):
        credit = credit_repository.get(db, credit_id)
        if not credit:
            return
        
        if (credit.remaining_balance or 0) <= 0:
            credit.status = CreditStatus.PAID
            db.commit()
            db.refresh(credit)
    
    def get_credit_payments(self, db: Session, user_id: int, credit_id: int, 
                           skip: int = 0, limit: int = 100) -> List[Payment]:
        
        credit = credit_repository.get(db, credit_id)
        print(type(credit.user_id), type(user_id))
        if not credit or str(credit.user_id) != user_id:
            raise ValueError("Crédito no encontrado o sin permisos")
        return payment_repository.get_by_credit(db, credit_id, skip, limit)
        
    
    def get_user_payments(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Payment]:
        user_credits = credit_repository.get_by_user(db, user_id, 0, 1000)
        credit_ids = [credit.id for credit in user_credits]
        
        if not credit_ids:
            return []
        
        payments = db.query(Payment).filter(Payment.credit_id.in_(credit_ids)).offset(skip).limit(limit).all()
        return payments
    
    def mark_installment_as_paid(self, db: Session, user_id: int, schedule_id: int, 
                                payment_date: Optional[datetime] = None) -> PaymentSchedule:
        schedule = payment_schedule_repository.get(db, schedule_id)
        if not schedule:
            raise ValueError("Cuota no encontrada")
        
        credit = credit_repository.get(db, schedule.credit_id)
        if not credit or credit.user_id != user_id:
            raise ValueError("Cuota no encontrada o sin permisos")
        
        result = payment_schedule_repository.mark_as_paid(
            db, schedule_id, payment_date or datetime.now()
        )
        
        self.check_and_update_credit_status(db, schedule.credit_id)
        
        return result
    
    def calculate_payment_summary(self, db: Session, user_id: int, credit_id: Optional[int] = None) -> dict:
        if credit_id:
            credit = credit_repository.get(db, credit_id)
            if not credit or credit.user_id != user_id:
                raise ValueError("Crédito no encontrado o sin permisos")
            
            payments = payment_repository.get_by_credit(db, credit_id)
            schedule = payment_schedule_repository.get_by_credit(db, credit_id)
        else:
            user_credits = credit_repository.get_by_user(db, user_id, 0, 1000)
            credit_ids = [credit.id for credit in user_credits]
            
            if not credit_ids:
                return {"total_payments": 0, "total_amount": 0, "total_installments": 0}
            
            payments = db.query(Payment).filter(Payment.credit_id.in_(credit_ids)).all()
            all_schedule = []
            for cid in credit_ids:
                credit_schedule = payment_schedule_repository.get_by_credit(db, cid)
                all_schedule.extend(credit_schedule)
            schedule = all_schedule
        
        total_amount = sum(float(payment.amount) for payment in payments)
        paid_installments = [i for i in schedule if i.is_paid]
        pending_installments = [i for i in schedule if not i.is_paid]
        overdue_installments = [i for i in pending_installments if i.due_date < datetime.now()]
        
        return {
            "total_payments": len(payments),
            "total_amount": total_amount,
            "total_installments": len(schedule),
            "paid_installments": len(paid_installments),
            "pending_installments": len(pending_installments),
            "overdue_installments": len(overdue_installments),
            "overdue_amount": sum(float(i.total_amount) for i in overdue_installments)
        }
    
    def process_automatic_payment(self, db: Session, schedule_id: int) -> bool:
        schedule = payment_schedule_repository.get(db, schedule_id)
        if not schedule or schedule.is_paid:
            return False
        
        payment_data_dict = {
            "credit_id": schedule.credit_id,
            "amount": schedule.total_amount,
            "payment_method": "auto_debit",
            "description": f"Pago automático cuota #{schedule.installment_number}",
            "payment_date": datetime.now(),
            "status": PaymentStatus.PAID
        }
        
        payment = payment_repository.create(db, obj_in=payment_data_dict)
        
        payment_schedule_repository.mark_as_paid(db, schedule_id)
        
        self.update_credit_balance(db, schedule.credit_id, schedule.total_amount)
        
        return True


payment_service = PaymentService()