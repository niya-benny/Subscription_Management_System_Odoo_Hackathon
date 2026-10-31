# Brightloop Subscription Management: Backend API

FastAPI + SQLAlchemy 2 + PostgreSQL (SQLite by default for zero-setup local runs).

## Getting Started

You can run the project in two ways. Both give you the full system: the API and the web app.

**Demo logins**

| Role | Email | Password |
|---|---|---|
| Admin | admin@brightloop.io | Admin@12345 |
| Staff | staff@brightloop.io | Staff@12345 |
| Customer | acme@shop.com | Cust@12345 |

### Option 1: Run locally with Python

**Requirements:** Python 3.10 or newer. No database setup is needed, because SQLite is used by default.

1. Clone the repository and open the backend folder:
   ```bash
   git clone https://github.com/<your-username>/<repo-name>.git
   cd <repo-name>/backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv

   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   source venv/bin/activate
   ```
   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

3. Install the dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

4. Start the API:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   The API runs at http://127.0.0.1:8000 and the interactive API docs are at http://127.0.0.1:8000/docs. Sample data is created automatically on first start.

5. Open the web app: double-click `frontend/index.html` (or open it in your browser) and sign in with a demo login above.

6. (Optional) Run the automated tests:
   ```bash
   python -m pytest -q
   ```

### Option 2: Run with Docker

**Requirements:** Docker Desktop (or Docker Engine with Compose). This starts the API together with a PostgreSQL database.

1. Clone the repository and open the backend folder:
   ```bash
   git clone https://github.com/<your-username>/<repo-name>.git
   cd <repo-name>/backend
   ```

2. Build and start everything:
   ```bash
   docker compose up --build
   ```
   The API runs at http://localhost:8000 and the API docs at http://localhost:8000/docs.

3. Open the web app: open `frontend/index.html` in your browser and sign in with a demo login above.

4. Stop the services with `Ctrl+C`, then remove the containers with:
   ```bash
   docker compose down
   ```

### Troubleshooting

- **"Cannot reach the API" in the web app:** the backend isn't running, or it runs at a different address. The API URL can be changed at the bottom of the login card.
- **`uvicorn` is not recognized:** use `python -m uvicorn ...` as shown above, with the virtual environment activated.
- **Port 8000 already in use:** start the API on another port with `--port 8001` and update the API URL on the login card.
- **Reset to fresh sample data (Option 1):** stop the server, delete `backend/brightloop.db`, and start it again.

<!-- ## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000/docs  (Swagger UI)
# or with Postgres:
docker compose up --build
pytest                                  # end-to-end test of a full billing month
```
Seed logins: admin@brightloop.io / Admin@12345, staff@brightloop.io / Staff@12345, acme@shop.com / Cust@12345 -->

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
