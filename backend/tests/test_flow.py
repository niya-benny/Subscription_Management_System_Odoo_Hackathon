import os, datetime as dt
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
if os.path.exists("test.db"): os.remove("test.db")
from fastapi.testclient import TestClient
from app.main import app

def H(c, e, p): return {"Authorization": "Bearer " + c.post("/auth/login", json={"email": e, "password": p}).json()["token"]}

def test_full_month():
    with TestClient(app) as c:
        a, st, cu = H(c, "admin@brightloop.io", "Admin@12345"), H(c, "staff@brightloop.io", "Staff@12345"), H(c, "acme@shop.com", "Cust@12345")
        assert c.post("/auth/signup", json={"email": "acme@shop.com", "name": "x", "password": "Cust@12345"}).status_code == 409
        assert c.post("/auth/signup", json={"email": "n@x.com", "name": "x", "password": "weakpass"}).status_code == 422
        assert c.post("/discounts", headers=st, json={}).status_code == 403          # only admin
        assert c.post("/staff", headers=st, json={"email": "z@x.com", "name": "z", "password": "Strong@Pass1"}).status_code == 403
        t = dt.date.today()
        c.post("/discounts", headers=a, json={"name": "Vol 10%", "kind": "percent", "value": 10, "min_qty": 5,
               "start_date": str(t - dt.timedelta(days=5)), "end_date": str(t + dt.timedelta(days=90)), "usage_limit": 100, "product_id": 1})
        cid = [u for u in c.get("/users/customers", headers=st).json() if u["email"] == "acme@shop.com"][0]["id"]
        sub = c.post("/subscriptions", headers=st, json={"customer_id": cid, "plan_id": 1, "start_date": str(t - dt.timedelta(days=65)),
                     "lines": [{"product_id": 1, "variant_id": 1, "qty": 5}]}).json()
        for _ in range(3): c.post(f"/subscriptions/{sub['id']}/advance", headers=st)
        n1 = c.post("/billing/run", headers=st).json()["invoices_created"]
        n2 = c.post("/billing/run", headers=st).json()["invoices_created"]
        assert n1 == 3 and n2 == 0                                                    # nothing billed twice or skipped
        inv = c.get("/invoices", headers=st).json()[0]
        assert inv["total"] == round(5 * 1560 * 0.9 * 1.18, 2)                       # variant + discount + tax
        assert c.post("/payments", headers=st, json={"invoice_id": inv["id"], "method": "UPI", "amount": 1, "paid_on": str(t)}).status_code == 422
        c.post(f"/invoices/{inv['id']}/confirm", headers=st)
        assert c.post("/payments", headers=cu, json={"invoice_id": inv["id"], "method": "UPI", "amount": inv["total"], "paid_on": str(t)}).status_code == 201
        assert c.get(f"/invoices/{inv['id']}", headers=st).json()["status"] == "Paid"
        r = c.get("/reports/summary", headers=st).json()
        assert r["active_subscriptions"] == 1 and r["revenue_collected"] == inv["total"]
