"""
Utilidades comunes para el microservicio de créditos
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional


def format_currency(amount: Decimal, currency: str = "USD") -> str:
    return f"{currency} {amount:,.2f}"


def calculate_days_overdue(due_date: datetime) -> int:

    today = datetime.now().date()
    due_date_only = due_date.date()
    
    if today <= due_date_only:
        return 0
    
    return (today - due_date_only).days


def validate_credit_amount(amount: Decimal, min_amount: Decimal = Decimal("1000.00"), 
                          max_amount: Decimal = Decimal("100000.00")) -> bool:

    return min_amount <= amount <= max_amount


def validate_interest_rate(rate: Decimal, min_rate: Decimal = Decimal("5.0"), 
                          max_rate: Decimal = Decimal("30.0")) -> bool:

    return min_rate <= rate <= max_rate


def validate_term_months(months: int, min_months: int = 6, max_months: int = 360) -> bool:

    return min_months <= months <= max_months


def format_payment_method(method: str) -> str:

    method_mapping = {
        "tarjeta_credito": "Tarjeta de Crédito",
        "tarjeta_debito": "Tarjeta de Débito", 
        "transferencia": "Transferencia Bancaria",
        "efectivo": "Efectivo",
        "cheque": "Cheque",
        "auto_debit": "Débito Automático",
        "online": "Pago en Línea"
    }
    
    return method_mapping.get(method, method.title())


def get_next_business_day(date: datetime) -> datetime:

    days_to_add = 1
    current_date = date
    
    while days_to_add > 0:
        current_date = current_date.replace(day=current_date.day + days_to_add)
        # Si es lunes (0) o domingo (6), saltar al siguiente día hábil
        weekday = current_date.weekday()
        if weekday in (5, 6):  # Sábado o domingo
            days_to_add += 1
        else:
            break
    
    return current_date


def calculate_remaining_months(approved_date: datetime, term_months: int) -> int:

    today = datetime.now()
    
    months_passed = (today.year - approved_date.year) * 12 + (today.month - approved_date.month)
    
    if today.day <= approved_date.day:
        months_passed -= 1
    
    remaining_months = max(0, term_months - max(0, months_passed))
    
    return remaining_months


def generate_credit_reference() -> str:

    import uuid
    return f"CREDIT-{str(uuid.uuid4())[:8].upper()}"


class CreditValidator:
    
    @staticmethod
    def is_valid_credit_request(amount: Decimal, interest_rate: Decimal, term_months: int) -> tuple[bool, str]:

        if not validate_credit_amount(amount):
            return False, f"Monto debe estar entre {format_currency(Decimal('1000.00'))} y {format_currency(Decimal('100000.00'))}"
        
        if not validate_interest_rate(interest_rate):
            return False, f"Tasa de interés debe estar entre 5% y 30%"
        
        if not validate_term_months(term_months):
            return False, f"Plazo debe estar entre 6 y 360 meses"
        
        return True, "Solicitud válida"
    
    @staticmethod
    def can_make_payment(current_balance: Decimal, payment_amount: Decimal) -> tuple[bool, str]:

        if payment_amount <= 0:
            return False, "El monto del pago debe ser mayor a 0"
        
        if payment_amount > current_balance:
            return False, "El monto del pago no puede exceder el saldo pendiente"
        
        return True, "Pago válido"


class DateUtils:
    
    @staticmethod
    def get_due_date_from_months(start_date: datetime, months_ahead: int) -> datetime:

        try:
            return start_date.replace(month=start_date.month + months_ahead)
        except ValueError:
            if start_date.month + months_ahead > 12:
                year = start_date.year + (start_date.month + months_ahead - 1) // 12
                month = (start_date.month + months_ahead - 1) % 12 + 1
            else:
                year = start_date.year
                month = start_date.month + months_ahead
            
            from datetime import timedelta
            next_month_first = start_date.replace(year=year, month=month, day=1)
            return next_month_first - timedelta(days=1)
    
    @staticmethod
    def is_payment_due(due_date: datetime, grace_days: int = 3) -> bool:

        today = datetime.now().date()
        due_date_only = due_date.date()
        
        grace_date = due_date_only.replace(day=due_date_only.day + grace_days)
        
        return today > grace_date
