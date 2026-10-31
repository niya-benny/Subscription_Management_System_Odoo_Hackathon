import secrets, datetime as dt
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from . import schemas as s
from .database import Base, engine, get_db
from .models import *
from .security import hash_pw, verify_pw, make_token, current_user, require
from .billing import run_billing, record_payment, add_period, next_number

app = FastAPI(title="Brightloop Subscription Management API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
ADMIN, STAFF, ANY = require("admin"), require("admin", "staff"), require("admin", "staff", "customer")

from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    from .seed import seed
    seed()

def dump(o, *skip):
    return {c.name: getattr(o, c.name) for c in o.__table__.columns if c.name not in skip}

# ---------- AUTH ----------
@app.post("/auth/signup", status_code=201, tags=["auth"])
def signup(b: s.SignupIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == b.email.lower())):
        raise HTTPException(409, "Email already registered")  # each email belongs to one account
    u = User(email=b.email.lower(), name=b.name, password_hash=hash_pw(b.password), role="customer")
    db.add(u); db.commit()
    return {"token": make_token(u), "role": u.role}

@app.post("/auth/login", tags=["auth"])
def login(b: s.LoginIn, db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.email == b.email.lower()))
    if not u or not verify_pw(b.password, u.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": make_token(u), "role": u.role, "name": u.name}

@app.post("/auth/forgot", tags=["auth"])
def forgot(b: s.ForgotIn, db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.email == b.email.lower()))
    if u:
        t = secrets.token_urlsafe(32)[:48]
        db.add(PasswordReset(token=t, user_id=u.id, expires_at=dt.datetime.utcnow() + dt.timedelta(hours=1))); db.commit()
        print(f"[EMAIL to {u.email}] reset link: https://app.brightloop.io/reset?token={t}")  # swap for SMTP in production
    return {"detail": "If the email is registered, a reset link has been sent"}

@app.post("/auth/reset", tags=["auth"])
def reset(b: s.ResetIn, db: Session = Depends(get_db)):
    r = db.get(PasswordReset, b.token)
    if not r or r.used or r.expires_at < dt.datetime.utcnow(): raise HTTPException(400, "Invalid or expired token")
    db.get(User, r.user_id).password_hash = hash_pw(b.new_password); r.used = True; db.commit()
    return {"detail": "Password updated"}

@app.post("/staff", status_code=201, tags=["auth"])
def add_staff(b: s.StaffIn, db: Session = Depends(get_db), _=Depends(ADMIN)):  # only admin adds staff
    if db.scalar(select(User).where(User.email == b.email.lower())): raise HTTPException(409, "Email already registered")
    u = User(email=b.email.lower(), name=b.name, password_hash=hash_pw(b.password), role="staff"); db.add(u); db.commit()
    return dump(u, "password_hash")

@app.get("/users/customers", tags=["auth"])
def customers(db: Session = Depends(get_db), _=Depends(STAFF)):
    return [dump(u, "password_hash") for u in db.scalars(select(User).where(User.role == "customer")).all()]

# ---------- CATALOG (admin writes) ----------
@app.post("/taxes", status_code=201, tags=["catalog"])
def add_tax(b: s.TaxIn, db: Session = Depends(get_db), _=Depends(ADMIN)):
    t = Tax(**b.model_dump()); db.add(t); db.commit(); return dump(t)

@app.get("/taxes", tags=["catalog"])
def taxes(db: Session = Depends(get_db), _=Depends(ANY)): return [dump(t) for t in db.scalars(select(Tax)).all()]

@app.post("/products", status_code=201, tags=["catalog"])
def add_product(b: s.ProductIn, db: Session = Depends(get_db), _=Depends(ADMIN)):
    p = Product(**b.model_dump(exclude={"variants"}), variants=[ProductVariant(**v.model_dump()) for v in b.variants])
    db.add(p); db.commit()
    return {**dump(p), "variants": [dump(v) for v in p.variants]}

@app.get("/products", tags=["catalog"])
def products(db: Session = Depends(get_db), _=Depends(ANY)):
    return [{**dump(p), "variants": [dump(v) for v in p.variants]} for p in db.scalars(select(Product)).all()]

@app.post("/plans", status_code=201, tags=["catalog"])
def add_plan(b: s.PlanIn, db: Session = Depends(get_db), _=Depends(ADMIN)):
    p = Plan(**b.model_dump()); db.add(p); db.commit(); return dump(p)

@app.get("/plans", tags=["catalog"])
def plans(db: Session = Depends(get_db), _=Depends(ANY)): return [dump(p) for p in db.scalars(select(Plan)).all()]

@app.post("/templates", status_code=201, tags=["catalog"])
def add_template(b: s.TemplateIn, db: Session = Depends(get_db), _=Depends(ADMIN)):
    t = QuotationTemplate(name=b.name, plan_id=b.plan_id, validity_days=b.validity_days,
                          lines=[TemplateLine(product_id=l.product_id, variant_id=l.variant_id, qty=l.qty) for l in b.lines])
    db.add(t); db.commit(); return {**dump(t), "lines": [dump(l) for l in t.lines]}

@app.get("/templates", tags=["catalog"])
def templates(db: Session = Depends(get_db), _=Depends(STAFF)):
    return [{**dump(t), "lines": [dump(l) for l in t.lines]} for t in db.scalars(select(QuotationTemplate)).all()]

@app.post("/discounts", status_code=201, tags=["catalog"])
def add_discount(b: s.DiscountIn, db: Session = Depends(get_db), _=Depends(ADMIN)):  # only admin creates discount rules
    d = Discount(**b.model_dump()); db.add(d); db.commit(); return dump(d)

@app.get("/discounts", tags=["catalog"])
def discounts(db: Session = Depends(get_db), _=Depends(STAFF)): return [dump(d) for d in db.scalars(select(Discount)).all()]

# ---------- SUBSCRIPTIONS ----------
def make_lines(db, lines, default_tax=None):
    out = []
    for l in lines:
        p = db.get(Product, l.product_id)
        if not p: raise HTTPException(404, f"Product {l.product_id} not found")
        v = db.get(ProductVariant, l.variant_id) if l.variant_id else None
        out.append(SubscriptionLine(product_id=p.id, variant_id=v.id if v else None, qty=l.qty,
                                    description=p.name + (f" ({v.attribute}: {v.value})" if v else ""),
                                    unit_price=float(p.sales_price) + (float(v.extra_price) if v else 0),
                                    tax_id=l.tax_id if l.tax_id is not None else default_tax))
    return out

def sub_out(x: Subscription):
    return {**dump(x), "plan": x.plan.name, "period": x.plan.period,
            "lines": [dump(l) for l in x.lines], "total": sum(l.qty * float(l.unit_price) for l in x.lines)}

@app.post("/subscriptions", status_code=201, tags=["subscriptions"])
def create_sub(b: s.SubscriptionIn, db: Session = Depends(get_db), _=Depends(STAFF)):
    tpl = db.get(QuotationTemplate, b.template_id) if b.template_id else None
    plan = db.get(Plan, tpl.plan_id if tpl else b.plan_id)
    if not plan: raise HTTPException(404, "Plan not found")
    lines_in = [s.LineIn(product_id=l.product_id, variant_id=l.variant_id, qty=l.qty) for l in tpl.lines] if tpl else b.lines
    if not lines_in: raise HTTPException(422, "At least one line is required")
    if any(l.qty < plan.min_qty for l in lines_in): raise HTTPException(422, f"Minimum quantity for this plan is {plan.min_qty}")
    if not (plan.available_from <= b.start_date <= plan.available_to): raise HTTPException(422, "Plan not available on that date")
    default_tax = db.scalar(select(Tax.id).order_by(Tax.id).limit(1))
    sub = Subscription(number=next_number(db, Subscription, "SUB"), customer_id=b.customer_id, plan_id=plan.id,
                       start_date=b.start_date, expiry_date=b.expiry_date or b.start_date + dt.timedelta(days=365),
                       payment_terms_days=b.payment_terms_days, next_billing_date=b.start_date,
                       quote_valid_until=dt.date.today() + dt.timedelta(days=tpl.validity_days) if tpl else None,
                       lines=make_lines(db, lines_in, default_tax))
    db.add(sub); db.commit(); return sub_out(sub)

@app.get("/subscriptions", tags=["subscriptions"])
def list_subs(status: str | None = None, page: int = 1, size: int = Query(50, le=200),
              db: Session = Depends(get_db), user: User = Depends(ANY)):
    q = select(Subscription).order_by(Subscription.id.desc())
    if user.role == "customer": q = q.where(Subscription.customer_id == user.id)  # customers only see their own
    if status: q = q.where(Subscription.status == status)
    return [sub_out(x) for x in db.scalars(q.offset((page - 1) * size).limit(size)).all()]

FLOW = {"Draft": "Quotation", "Quotation": "Confirmed", "Confirmed": "Active"}

@app.post("/subscriptions/{sid}/{action}", tags=["subscriptions"])
def transition(sid: int, action: str, db: Session = Depends(get_db), user: User = Depends(ANY)):
    x = db.get(Subscription, sid)
    if not x or (user.role == "customer" and x.customer_id != user.id): raise HTTPException(404, "Subscription not found")
    pl, st = x.plan, x.status
    if user.role == "customer" and action not in ("pause", "resume", "close"): raise HTTPException(403, "Not allowed")
    if action == "advance" and st in FLOW: x.status = FLOW[st]
    elif action == "pause" and st == "Active" and pl.pausable: x.status = "Paused"
    elif action == "resume" and st == "Paused": x.status = "Active"
    elif action == "close" and st in ("Active", "Paused") and pl.closable: x.status = "Closed"
    elif action == "renew" and st == "Closed" and pl.renewable:
        today = dt.date.today(); x.status = "Active"
        x.expiry_date = add_period(max(x.expiry_date, today), "yearly"); x.next_billing_date = max(x.next_billing_date, today)
    else: raise HTTPException(409, f"Action '{action}' not allowed from {st} on plan '{pl.name}'")
    db.commit(); return sub_out(x)

# ---------- INVOICES ----------
def inv_out(i: Invoice):
    return {**dump(i), "balance": round(float(i.total) - float(i.paid_amount), 2),
            "overdue": i.status == "Confirmed" and i.due_date < dt.date.today(), "lines": [dump(l) for l in i.lines]}

@app.post("/billing/run", tags=["invoices"])
def billing_run(db: Session = Depends(get_db), _=Depends(STAFF)):
    return {"invoices_created": run_billing(db)}

@app.get("/invoices", tags=["invoices"])
def list_invoices(status: str | None = None, overdue: bool | None = None, outstanding: bool | None = None,
                  customer_id: int | None = None, q: str | None = None, page: int = 1, size: int = Query(50, le=200),
                  db: Session = Depends(get_db), user: User = Depends(ANY)):
    qs = select(Invoice).order_by(Invoice.id.desc())
    if user.role == "customer": qs = qs.where(Invoice.customer_id == user.id, Invoice.status != "Draft")
    elif customer_id: qs = qs.where(Invoice.customer_id == customer_id)
    if status: qs = qs.where(Invoice.status == status)
    if outstanding: qs = qs.where(Invoice.status == "Confirmed")
    if overdue: qs = qs.where(Invoice.status == "Confirmed", Invoice.due_date < dt.date.today())
    if q: qs = qs.where(Invoice.number.ilike(f"%{q}%"))
    return [inv_out(i) for i in db.scalars(qs.offset((page - 1) * size).limit(size)).all()]

@app.get("/invoices/{iid}", tags=["invoices"])
def get_invoice(iid: int, db: Session = Depends(get_db), user: User = Depends(ANY)):
    i = db.get(Invoice, iid)
    if not i or (user.role == "customer" and i.customer_id != user.id): raise HTTPException(404, "Invoice not found")
    return inv_out(i)

@app.post("/invoices/{iid}/{action}", tags=["invoices"])
def invoice_action(iid: int, action: str, db: Session = Depends(get_db), _=Depends(STAFF)):
    i = db.get(Invoice, iid)
    if not i: raise HTTPException(404, "Invoice not found")
    if action == "confirm" and i.status == "Draft": i.status = "Confirmed"
    elif action == "cancel" and i.status in ("Draft", "Confirmed"): i.status = "Cancelled"
    elif action == "send" and i.status != "Cancelled": i.sent = True  # hook SMTP / PDF here
    else: raise HTTPException(409, f"Cannot {action} an invoice in status {i.status}")
    db.commit(); return inv_out(i)

# ---------- PAYMENTS ----------
@app.post("/payments", status_code=201, tags=["payments"])
def pay(b: s.PaymentIn, db: Session = Depends(get_db), user: User = Depends(ANY)):
    if user.role == "customer":
        inv = db.get(Invoice, b.invoice_id)
        if not inv or inv.customer_id != user.id: raise HTTPException(404, "Invoice not found")
    try: return dump(record_payment(db, **b.model_dump()))
    except ValueError as e: raise HTTPException(422, str(e))

@app.get("/payments", tags=["payments"])
def list_payments(page: int = 1, size: int = Query(50, le=200), db: Session = Depends(get_db), _=Depends(STAFF)):
    return [dump(p) for p in db.scalars(select(Payment).order_by(Payment.id.desc()).offset((page - 1) * size).limit(size)).all()]

# ---------- REPORTS ----------
@app.get("/reports/summary", tags=["reports"])
def summary(date_from: dt.date | None = None, date_to: dt.date | None = None,
            db: Session = Depends(get_db), _=Depends(STAFF)):
    """Aggregates in SQL so it stays fast with thousands of rows."""
    today = dt.date.today()
    active = db.scalar(select(func.count()).select_from(Subscription).where(Subscription.status == "Active"))
    rq = select(func.coalesce(func.sum(Payment.amount), 0))
    if date_from: rq = rq.where(Payment.paid_on >= date_from)
    if date_to: rq = rq.where(Payment.paid_on <= date_to)
    owed = db.scalar(select(func.coalesce(func.sum(Invoice.total - Invoice.paid_amount), 0)).where(Invoice.status == "Confirmed"))
    od = db.execute(select(func.count(), func.coalesce(func.sum(Invoice.total - Invoice.paid_amount), 0))
                    .where(Invoice.status == "Confirmed", Invoice.due_date < today)).one()
    per = db.execute(select(Plan.period, func.sum(SubscriptionLine.qty * SubscriptionLine.unit_price))
                     .join(Subscription, Subscription.plan_id == Plan.id).join(SubscriptionLine, SubscriptionLine.subscription_id == Subscription.id)
                     .where(Subscription.status == "Active").group_by(Plan.period)).all()
    k = {"daily": 365 / 12, "weekly": 52 / 12, "monthly": 1, "yearly": 1 / 12}
    return {"active_subscriptions": active, "revenue_collected": float(db.scalar(rq)), "outstanding": float(owed),
            "overdue_count": od[0], "overdue_amount": float(od[1]), "mrr": round(sum(float(v) * k[p] for p, v in per), 2)}
