"""Core billing engine: invoice generation, taxes, discounts, payments."""
import datetime as dt
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .models import Subscription, Invoice, InvoiceLine, Discount, Tax, Payment

STEP = {"daily": relativedelta(days=1), "weekly": relativedelta(weeks=1),
        "monthly": relativedelta(months=1), "yearly": relativedelta(years=1)}

def add_period(d: dt.date, period: str) -> dt.date:
    return d + STEP[period]

def next_number(db: Session, model, prefix: str) -> str:
    last = db.scalar(select(model.id).order_by(model.id.desc()).limit(1)) or 0
    return f"{prefix}{last + 1:06d}"

def build_invoice(db: Session, sub: Subscription, period_start: dt.date) -> Invoice:
    f = lambda x: float(x)
    lines = [dict(desc=l.description, qty=l.qty, price=f(l.unit_price), tax_id=l.tax_id, pid=l.product_id,
                  base=l.qty * f(l.unit_price), disc=0.0) for l in sub.lines]
    sub_total, total_qty, sub_disc, notes = sum(l["base"] for l in lines), sum(l["qty"] for l in lines), 0.0, []
    # Discounts apply automatically while valid and within usage limit, and stop on expiry / exhaustion.
    rules = db.scalars(select(Discount).where(Discount.start_date <= period_start, Discount.end_date >= period_start,
                                              Discount.used_count < Discount.usage_limit)).all()
    for d in rules:
        amount = 0.0
        if d.product_id:
            for l in lines:
                if l["pid"] == d.product_id and l["qty"] >= d.min_qty and l["base"] >= f(d.min_amount):
                    x = l["base"] * f(d.value) / 100 if d.kind == "percent" else min(f(d.value), l["base"])
                    l["disc"] += x; amount += x
        elif d.subscription_id in (None, sub.id) and sub_total >= f(d.min_amount) and total_qty >= d.min_qty:
            amount = sub_total * f(d.value) / 100 if d.kind == "percent" else min(f(d.value), sub_total)
            sub_disc += amount
        if amount:
            # atomic increment guards the usage limit under concurrency
            ok = db.execute(update(Discount).where(Discount.id == d.id, Discount.used_count < Discount.usage_limit)
                            .values(used_count=Discount.used_count + 1)).rowcount
            if ok: notes.append(f"{d.name}: -{amount:.2f}")
    rates = {t.id: f(t.rate) for t in db.scalars(select(Tax)).all()}
    inv = Invoice(number=next_number(db, Invoice, "INV"), subscription_id=sub.id, customer_id=sub.customer_id,
                  period_start=period_start, invoice_date=period_start,
                  due_date=period_start + dt.timedelta(days=sub.payment_terms_days),
                  discount_notes="; ".join(notes))
    un = tx = 0.0
    for l in lines:
        net = l["base"] - l["disc"] - (sub_disc * l["base"] / sub_total if sub_total else 0)
        tax = net * rates.get(l["tax_id"], 0) / 100
        un += net; tx += tax
        inv.lines.append(InvoiceLine(description=l["desc"], qty=l["qty"], unit_price=l["price"],
                                     discount=round(l["disc"], 2), net=round(net, 2), tax=round(tax, 2)))
    inv.untaxed, inv.tax, inv.total = round(un, 2), round(tx, 2), round(un + tx, 2)
    return inv

def run_billing(db: Session, today: dt.date | None = None) -> int:
    """Create every due invoice. Idempotent: the unique (subscription, period) constraint makes double billing impossible."""
    today, created = today or dt.date.today(), 0
    subs = db.scalars(select(Subscription).where(Subscription.status == "Active",
                                                 Subscription.next_billing_date <= today)).all()
    for s in subs:
        while s.next_billing_date <= today and s.next_billing_date <= s.expiry_date:
            try:
                with db.begin_nested():  # savepoint: a duplicate rolls back only itself (and its discount usage)
                    db.add(build_invoice(db, s, s.next_billing_date)); db.flush()
                created += 1
            except IntegrityError:
                pass
            s.next_billing_date = add_period(s.next_billing_date, s.plan.period)
        if s.expiry_date < today and s.plan.auto_close:
            s.status = "Closed"
    db.commit()
    return created

def record_payment(db: Session, invoice_id: int, method: str, amount: float, paid_on: dt.date, note: str) -> Payment:
    inv = db.scalar(select(Invoice).where(Invoice.id == invoice_id).with_for_update())
    if not inv: raise ValueError("Invoice not found")
    if inv.status != "Confirmed": raise ValueError("Only Confirmed invoices can receive payments")
    balance = round(float(inv.total) - float(inv.paid_amount), 2)
    if amount <= 0 or amount > balance + 0.005: raise ValueError(f"Amount must be between 0 and the balance {balance}")
    p = Payment(invoice_id=inv.id, method=method, amount=amount, paid_on=paid_on, note=note)
    db.add(p)
    inv.paid_amount = round(float(inv.paid_amount) + amount, 2)
    if inv.paid_amount >= float(inv.total) - 0.005: inv.status = "Paid"
    db.commit()
    return p
