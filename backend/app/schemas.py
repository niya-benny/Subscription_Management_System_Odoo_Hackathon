import re, datetime as dt
from typing import Literal
from pydantic import BaseModel, EmailStr, field_validator

def check_password(p: str) -> str:
    if not (len(p) > 8 and re.search(r"[A-Z]", p) and re.search(r"[a-z]", p) and re.search(r"[^A-Za-z0-9]", p)):
        raise ValueError("Password must be more than 8 characters with an uppercase letter, a lowercase letter and a special character")
    return p

class SignupIn(BaseModel):
    email: EmailStr
    name: str
    password: str
    _v = field_validator("password")(check_password)

class StaffIn(SignupIn):
    pass

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ForgotIn(BaseModel):
    email: EmailStr

class ResetIn(BaseModel):
    token: str
    new_password: str
    _v = field_validator("new_password")(check_password)

class TaxIn(BaseModel):
    name: str
    rate: float

class VariantIn(BaseModel):
    attribute: str = "Brand"
    value: str
    extra_price: float = 0

class ProductIn(BaseModel):
    name: str
    type: str
    sales_price: float
    cost_price: float = 0
    notes: str = ""
    variants: list[VariantIn] = []

class PlanIn(BaseModel):
    name: str
    period: Literal["daily", "weekly", "monthly", "yearly"]
    min_qty: int = 1
    available_from: dt.date
    available_to: dt.date
    auto_close: bool = False
    closable: bool = False
    pausable: bool = False
    renewable: bool = False

class LineIn(BaseModel):
    product_id: int
    variant_id: int | None = None
    qty: int
    tax_id: int | None = None

class TemplateIn(BaseModel):
    name: str
    plan_id: int
    validity_days: int = 30
    lines: list[LineIn]

class SubscriptionIn(BaseModel):
    customer_id: int
    plan_id: int | None = None
    template_id: int | None = None
    start_date: dt.date
    expiry_date: dt.date | None = None
    payment_terms_days: int = 15
    lines: list[LineIn] = []

class DiscountIn(BaseModel):
    name: str
    kind: Literal["percent", "fixed"]
    value: float
    min_amount: float = 0
    min_qty: int = 1
    start_date: dt.date
    end_date: dt.date
    usage_limit: int = 1000000
    product_id: int | None = None
    subscription_id: int | None = None

class PaymentIn(BaseModel):
    invoice_id: int
    method: str
    amount: float
    paid_on: dt.date
    note: str = ""
