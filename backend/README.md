# Brightloop Subscription Management: Backend API

FastAPI + SQLAlchemy 2 + PostgreSQL (SQLite by default for zero-setup local runs).

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000/docs  (Swagger UI)
# or with Postgres:
docker compose up --build
pytest                                  # end-to-end test of a full billing month
```
Seed logins: admin@brightloop.io / Admin@12345, staff@brightloop.io / Staff@12345, acme@shop.com / Cust@12345

## Design highlights
- **No double billing:** `UNIQUE(subscription_id, period_start)` on invoices, with a savepoint per invoice in the billing run; the run is safe to repeat and catches up skipped periods.
- **Discounts:** applied automatically at invoice generation, only while valid and under the usage limit; usage is incremented atomically.
- **Roles:** admin (everything, only one who creates staff/discounts/products/plans), staff (day-to-day), customer (own subscriptions and invoices only).
- **Performance:** composite indexes on `(status, next_billing_date)` and `(status, due_date)`, paginated lists, SQL aggregates for the dashboard.
- **Payments:** row-locked, validated against invoice balance, auto-marks invoice Paid.

## Endpoints
| Area | Routes |
|---|---|
| Auth | `POST /auth/signup /auth/login /auth/forgot /auth/reset`, `POST /staff` (admin) |
| Catalog | `/products /plans /taxes /templates /discounts` (admin writes) |
| Subscriptions | `POST/GET /subscriptions`, `POST /subscriptions/{id}/{advance\|pause\|resume\|close\|renew}` |
| Invoices | `POST /billing/run`, `GET /invoices?status=&overdue=&outstanding=&q=&page=`, `POST /invoices/{id}/{confirm\|cancel\|send}` |
| Payments | `POST /payments`, `GET /payments` |
| Reports | `GET /reports/summary?date_from=&date_to=` |

Production TODOs: SMTP for reset and invoice emails, PDF invoice rendering, Alembic migrations, scheduled billing (cron/Celery beat).
