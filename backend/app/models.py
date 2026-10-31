import datetime as dt
from sqlalchemy import (String, Integer, Numeric, Boolean, Date, DateTime, ForeignKey,
                        UniqueConstraint, Index, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="customer")  # admin|staff|customer

class PasswordReset(Base):
    __tablename__ = "password_resets"
    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)

class Tax(Base):
    __tablename__ = "taxes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    rate: Mapped[float] = mapped_column(Numeric(6, 2))

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    type: Mapped[str] = mapped_column(String(60))
    sales_price: Mapped[float] = mapped_column(Numeric(12, 2))
    cost_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    variants: Mapped[list["ProductVariant"]] = relationship(cascade="all, delete-orphan", lazy="selectin")

class ProductVariant(Base):
    __tablename__ = "product_variants"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    attribute: Mapped[str] = mapped_column(String(60))   # e.g. Brand
    value: Mapped[str] = mapped_column(String(60))       # e.g. Odoo
    extra_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)  # e.g. 560

class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    period: Mapped[str] = mapped_column(String(10))  # daily|weekly|monthly|yearly
    min_qty: Mapped[int] = mapped_column(Integer, default=1)
    available_from: Mapped[dt.date] = mapped_column(Date)
    available_to: Mapped[dt.date] = mapped_column(Date)
    auto_close: Mapped[bool] = mapped_column(Boolean, default=False)
    closable: Mapped[bool] = mapped_column(Boolean, default=False)
    pausable: Mapped[bool] = mapped_column(Boolean, default=False)
    renewable: Mapped[bool] = mapped_column(Boolean, default=False)

class QuotationTemplate(Base):
    __tablename__ = "quotation_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    validity_days: Mapped[int] = mapped_column(Integer, default=30)
    lines: Mapped[list["TemplateLine"]] = relationship(cascade="all, delete-orphan", lazy="selectin")

class TemplateLine(Base):
    __tablename__ = "template_lines"
    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("quotation_templates.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"), nullable=True)
    qty: Mapped[int] = mapped_column(Integer, default=1)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    start_date: Mapped[dt.date] = mapped_column(Date)
    expiry_date: Mapped[dt.date] = mapped_column(Date)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=15)
    status: Mapped[str] = mapped_column(String(15), default="Draft")  # Draft|Quotation|Confirmed|Active|Paused|Closed
    next_billing_date: Mapped[dt.date] = mapped_column(Date)
    quote_valid_until: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    lines: Mapped[list["SubscriptionLine"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    plan: Mapped[Plan] = relationship(lazy="joined")
    __table_args__ = (Index("ix_sub_status_next", "status", "next_billing_date"),)

class SubscriptionLine(Base):
    __tablename__ = "subscription_lines"
    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"), nullable=True)
    description: Mapped[str] = mapped_column(String(255))
    qty: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2))
    tax_id: Mapped[int | None] = mapped_column(ForeignKey("taxes.id"), nullable=True)

class Discount(Base):
    __tablename__ = "discounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(10))  # percent|fixed
    value: Mapped[float] = mapped_column(Numeric(12, 2))
    min_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    min_qty: Mapped[int] = mapped_column(Integer, default=1)
    start_date: Mapped[dt.date] = mapped_column(Date)
    end_date: Mapped[dt.date] = mapped_column(Date)
    usage_limit: Mapped[int] = mapped_column(Integer, default=1000000)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)           # product scope
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"), nullable=True)  # one sub; both null = all subs

class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    period_start: Mapped[dt.date] = mapped_column(Date)
    invoice_date: Mapped[dt.date] = mapped_column(Date)
    due_date: Mapped[dt.date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(12), default="Draft")  # Draft|Confirmed|Paid|Cancelled
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    untaxed: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    tax: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    paid_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    discount_notes: Mapped[str] = mapped_column(Text, default="")
    lines: Mapped[list["InvoiceLine"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    # NOTHING BILLED TWICE: DB-level guarantee, one invoice per subscription per period
    __table_args__ = (UniqueConstraint("subscription_id", "period_start", name="uq_invoice_sub_period"),
                      Index("ix_invoice_status_due", "status", "due_date"))

class InvoiceLine(Base):
    __tablename__ = "invoice_lines"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    description: Mapped[str] = mapped_column(String(255))
    qty: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2))
    discount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    net: Mapped[float] = mapped_column(Numeric(12, 2))
    tax: Mapped[float] = mapped_column(Numeric(12, 2))

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    method: Mapped[str] = mapped_column(String(30))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    paid_on: Mapped[dt.date] = mapped_column(Date, index=True)
    note: Mapped[str] = mapped_column(String(255), default="")
