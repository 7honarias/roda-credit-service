from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from ..models import Credit, CreditStatus, PaymentSchedule
from ..schemas import CreditRequest, CreditStatusUpdate
from ..repositories import credit_repository, payment_schedule_repository


class CreditService:
    
    def calculate_monthly_payment(self, principal: Decimal, annual_rate: Decimal, months: int) -> Decimal:
        
        if annual_rate == 0:
            return principal / months
        
        monthly_rate = annual_rate / 100 / 12
        power = (1 + monthly_rate) ** months
        monthly_payment = principal * (monthly_rate * power) / (power - 1)
        
        return round(monthly_payment, 2)
    
    def create_credit_request(self, db: Session, user_id: str, credit_data: CreditRequest) -> Credit:
        monthly_payment = self.calculate_monthly_payment(
            credit_data.amount, 
            credit_data.interest_rate, 
            credit_data.term_months
        )
        
        credit_data_dict = credit_data.dict()
        credit_data_dict.update({
            "user_id": user_id,
            "monthly_payment": monthly_payment,
            "remaining_balance": credit_data.amount,
            "status": CreditStatus.PENDING
        })
        
        credit = credit_repository.create(db, obj_in=credit_data_dict)
        
        self.generate_payment_schedule(db, credit.id, credit_data.amount, 
                                     credit_data.interest_rate, credit_data.term_months,
                                     credit_data.amount, monthly_payment)
        
        return credit
    
    def approve_credit(self, db: Session, credit_id: int) -> Optional[Credit]:
        credit = credit_repository.get(db, credit_id)
        if not credit:
            raise ValueError("Crédito no encontrado")
        
        if credit.status != CreditStatus.PENDING:
            raise ValueError("Solo se pueden aprobar créditos pendientes")
        
        credit.status = CreditStatus.ACTIVE
        credit.approved_at = datetime.now()
        db.commit()
        db.refresh(credit)
        
        return credit
    
    def reject_credit(self, db: Session, credit_id: int, reason: str = None) -> Optional[Credit]:
        credit = credit_repository.get(db, credit_id)
        if not credit:
            raise ValueError("Crédito no encontrado")
        
        if credit.status not in [CreditStatus.PENDING]:
            raise ValueError("Solo se pueden rechazar créditos pendientes")
        
        credit.status = CreditStatus.REJECTED
        db.commit()
        db.refresh(credit)
        
        return credit
    
    def update_credit_status(self, db: Session, credit_id: int, status_data: CreditStatusUpdate) -> Optional[Credit]:
        credit = credit_repository.get(db, credit_id)
        if not credit:
            raise ValueError("Crédito no encontrado")
        
        valid_statuses = {status.value for status in CreditStatus}
        if status_data.status not in valid_statuses:
            raise ValueError(f"Estado inválido. Estados válidos: {', '.join(valid_statuses)}")
        
        credit.status = CreditStatus(status_data.status)
        db.commit()
        db.refresh(credit)
        
        return credit
    
    def get_user_credits(self, db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Credit]:
        print(f"Fetching credits for user_id: {user_id}")
        return credit_repository.get_by_user(db, user_id, skip, limit)
    
    def get_credit_with_schedule(self, db: Session, credit_id: int) -> Tuple[Credit, List[PaymentSchedule]]:
        credit = credit_repository.get(db, credit_id)
        if not credit:
            raise ValueError("Crédito no encontrado")
        
        schedule = payment_schedule_repository.get_by_credit(db, credit_id)
        
        return credit, schedule
    
    def generate_payment_schedule(self, db: Session, credit_id: int, principal: Decimal, 
                                annual_rate: Decimal, months: int, total_credit: Decimal,
                                monthly_payment: Decimal) -> List[PaymentSchedule]:
        
        existing_schedule = payment_schedule_repository.get_by_credit(db, credit_id)
        for installment in existing_schedule:
            db.delete(installment)
            db.commit()
        
        monthly_rate = annual_rate / 100 / 12
        remaining_balance = total_credit
        schedule = []
        
        for month in range(1, months + 1):
            interest_payment = round(remaining_balance * monthly_rate, 2)
            
            principal_payment = round(monthly_payment - interest_payment, 2)
            
            if month == months:
                principal_payment = remaining_balance
            
            remaining_balance = round(remaining_balance - principal_payment, 2)
            
            due_date = datetime.now() + timedelta(days=30 * month)
            
            installment_data = {
                "credit_id": credit_id,
                "installment_number": month,
                "due_date": due_date,
                "principal_amount": principal_payment,
                "interest_amount": interest_payment,
                "total_amount": round(principal_payment + interest_payment, 2)
            }
            
            installment = payment_schedule_repository.create(db, obj_in=installment_data)
            schedule.append(installment)
        
        return schedule
    
    def check_credit_status(self, db: Session, credit_id: int) -> str:
        credit = credit_repository.get(db, credit_id)
        if not credit:
            raise ValueError("Crédito no encontrado")
        
        if credit.status not in [CreditStatus.ACTIVE, CreditStatus.DELINQUENT]:
            return credit.status.value
        
        overdue_installments = payment_schedule_repository.get_overdue_installments(db, credit_id)
        
        if overdue_installments:
            credit.status = CreditStatus.DELINQUENT
        else:
            credit.status = CreditStatus.ACTIVE
        
        db.commit()
        return credit.status.value
    
    def calculate_credit_summary(self, db: Session, credit_id: int) -> dict:
        credit = credit_repository.get(db, credit_id)
        if not credit:
            raise ValueError("Crédito no encontrado")
        
        schedule = payment_schedule_repository.get_by_credit(db, credit_id)
        paid_installments = [i for i in schedule if i.is_paid]
        pending_installments = [i for i in schedule if not i.is_paid]
        overdue_installments = [i for i in pending_installments if i.due_date < datetime.now()]
        
        total_paid = sum(i.total_amount for i in paid_installments)
        total_pending = sum(i.total_amount for i in pending_installments)
        total_overdue = sum(i.total_amount for i in overdue_installments)
        
        return {
            "credit_id": credit_id,
            "total_credit": float(credit.amount),
            "remaining_balance": float(credit.remaining_balance or 0),
            "total_paid": float(total_paid),
            "total_pending": float(total_pending),
            "total_overdue": float(total_overdue),
            "paid_installments": len(paid_installments),
            "pending_installments": len(pending_installments),
            "overdue_installments": len(overdue_installments),
            "total_installments": len(schedule)
        }


credit_service = CreditService()