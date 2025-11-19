from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from ..models import Credit, CreditStatus
from ..schemas import CreditCreate, CreditUpdate
from .base import BaseRepository


class CreditRepository(BaseRepository[Credit, CreditCreate, CreditUpdate]):
    
    def get_by_user(self, db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Credit]:
        return db.query(Credit).filter(Credit.user_id == user_id).offset(skip).limit(limit).all()
    
    def get_by_status(self, db: Session, status: CreditStatus, skip: int = 0, limit: int = 100) -> List[Credit]:
        return db.query(Credit).filter(Credit.status == status).offset(skip).limit(limit).all()
    
    def get_active_credits(self, db: Session, user_id: int) -> List[Credit]:
        return db.query(Credit).filter(
            and_(
                Credit.user_id == user_id,
                Credit.status.in_([CreditStatus.ACTIVE, CreditStatus.DELINQUENT])
            )
        ).all()
    
    def get_pending_credits(self, db: Session, skip: int = 0, limit: int = 100) -> List[Credit]:
        return db.query(Credit).filter(Credit.status == CreditStatus.PENDING).offset(skip).limit(limit).all()
    
    def get_overdue_credits(self, db: Session) -> List[Credit]:
        return db.query(Credit).filter(Credit.status == CreditStatus.DELINQUENT).all()
    
    def update_status(self, db: Session, credit_id: int, status: CreditStatus) -> Optional[Credit]:
        credit = self.get(db, credit_id)
        if credit:
            credit.status = status
            db.commit()
            db.refresh(credit)
        return credit
    
    def update_balance(self, db: Session, credit_id: int, new_balance: float) -> Optional[Credit]:
        credit = self.get(db, credit_id)
        if credit:
            credit.remaining_balance = new_balance
            db.commit()
            db.refresh(credit)
        return credit
    
    def get_recent_credits(self, db: Session, limit: int = 10) -> List[Credit]:
        return db.query(Credit).order_by(desc(Credit.created_at)).limit(limit).all()


credit_repository = CreditRepository(Credit)