import enum


class CreditStatus(enum.Enum):
    """Estados posibles del crédito"""
    PENDING = "pendiente"
    APPROVED = "aprobado"
    ACTIVE = "al_dia"
    DELINQUENT = "en_mora"
    PAID = "pagado"
    REJECTED = "rechazado"


class PaymentStatus(enum.Enum):
    """Estados posibles del pago"""
    PENDING = "pendiente"
    PAID = "pagado"
    OVERDUE = "vencido"
