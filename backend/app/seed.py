import datetime as dt
from sqlalchemy import select
from .database import SessionLocal
from .models import *
from .security import hash_pw

def seed():
    with SessionLocal() as db:
        if db.scalar(select(User.id).limit(1)): return
        t = dt.date.today()
        db.add_all([User(email="admin@brightloop.io", name="Admin", role="admin", password_hash=hash_pw("Admin@12345")),
                    User(email="staff@brightloop.io", name="Staff", role="staff", password_hash=hash_pw("Staff@12345")),
                    User(email="acme@shop.com", name="Acme Shop", role="customer", password_hash=hash_pw("Cust@12345")),
                    Tax(name="GST 18%", rate=18), Tax(name="No tax", rate=0),
                    Plan(name="Monthly Pro", period="monthly", min_qty=1, available_from=t - dt.timedelta(days=400),
                         available_to=t + dt.timedelta(days=800), auto_close=True, closable=True, pausable=True, renewable=True),
                    Product(name="Brightloop ERP", type="Software", sales_price=1000, cost_price=400, notes="Core suite",
                            variants=[ProductVariant(attribute="Brand", value="Odoo", extra_price=560)])])
        db.commit()
