# Brightloop – Subscription Management System

A full-stack Subscription Management System developed for the Odoo Hackathon. Brightloop simplifies subscription management, recurring billing, invoice generation, discount management, payment tracking, and financial reporting through a role-based web application.

> **Note:** The current implementation uses FastAPI, SQLAlchemy, PostgreSQL/SQLite, and a lightweight HTML, CSS, and JavaScript frontend. It is not currently an Odoo module or connected to an Odoo instance.

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [User Roles](#user-roles)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Demo Credentials](#demo-credentials)
- [Application Workflow](#application-workflow)
- [API Endpoints](#api-endpoints)
- [Business Logic](#business-logic)
- [Testing](#testing)
- [Environment Configuration](#environment-configuration)
- [Future Enhancements](#future-enhancements)

## Project Overview

Brightloop is designed to automate and simplify the complete subscription lifecycle, from customer registration and subscription creation to recurring invoice generation and payment tracking.

The system provides an integrated platform where administrators and staff can manage products, subscription plans, quotations, discounts, invoices, and payments, while customers can access and manage their own subscriptions.

The application focuses on reducing manual billing operations, maintaining accurate financial records, and providing better visibility into subscription and revenue information.

## Key Features

### 1. Authentication and User Management

- Customer registration and login.
- JWT-based authentication.
- Secure password hashing using PBKDF2-HMAC-SHA256.
- Role-based access control.
- Forgot-password and password-reset functionality.
- Admin-controlled staff account creation.
- Separate access permissions for Admin, Staff, and Customer.

### 2. Product Management

- Create and manage products.
- Configure product sales prices and cost prices.
- Add product variants.
- Maintain product descriptions and notes.
- Associate products with subscription plans and quotations.

### 3. Subscription Plan Management

- Create subscription plans with different billing frequencies:
  - Daily
  - Weekly
  - Monthly
  - Yearly
- Configure minimum subscription quantities.
- Define plan availability dates.
- Enable or disable pausing, closing, renewal, and automatic closure.
- Manage subscription terms and conditions.

### 4. Quotation Management

- Create quotation templates.
- Associate templates with subscription plans.
- Add predefined products and quantities.
- Configure quotation validity periods.
- Create subscriptions using existing quotation templates.

### 5. Subscription Lifecycle Management

The application supports the following subscription states:

- Draft
- Quotation
- Confirmed
- Active
- Paused
- Closed

Features include:

- Create subscriptions for registered customers.
- Automatically generate subscription numbers.
- Validate plan availability and minimum quantities.
- Advance subscriptions through their lifecycle.
- Pause and resume eligible subscriptions.
- Close subscriptions based on plan configuration.
- Renew eligible closed subscriptions.
- Allow customers to manage their own eligible subscriptions.

### 6. Automated Recurring Billing

- Generate invoices automatically for subscriptions whose billing dates are due.
- Support daily, weekly, monthly, and yearly billing cycles.
- Handle multiple missed billing periods.
- Calculate invoice amounts based on subscription products and quantities.
- Apply eligible discounts automatically.
- Calculate taxes and final invoice totals.
- Prevent duplicate invoice generation for the same subscription period.

### 7. Discount Management

- Create percentage-based and fixed-value discounts.
- Configure discount validity periods.
- Define minimum purchase quantities.
- Define minimum purchase amounts.
- Configure usage limits.
- Apply discounts to specific products, subscriptions, or eligible billing transactions.
- Automatically validate discount eligibility during invoice generation.

### 8. Invoice Management

- Automatically generate invoices.
- View invoice details and line items.
- Track invoice status.
- Confirm and cancel invoices.
- Mark invoices as sent.
- Calculate outstanding balances.
- Identify overdue invoices.
- Filter invoices by status and other criteria.

### 9. Payment Management

- Record payments against confirmed invoices.
- Support different payment methods.
- Maintain payment dates and notes.
- Validate payment amounts against outstanding balances.
- Automatically update invoice status when the full amount is paid.
- Allow customers to make payments against their own invoices.

### 10. Dashboard and Financial Reporting

The dashboard provides an overview of important financial metrics:

- Active Subscriptions
- Monthly Recurring Revenue (MRR)
- Revenue Collected
- Outstanding Amount
- Overdue Invoice Count
- Overdue Invoice Amount

The reporting API also supports date-based filtering for collected revenue.

### 11. Responsive User Interface

- Responsive web interface.
- Role-specific dashboards and navigation.
- Customer account area.
- Subscription and invoice management screens.
- Financial overview.
- Light and dark system theme support.

## User Roles

The application supports three roles.

| Feature | Admin | Staff | Customer |
|---|---|---|---|
| Login | Yes | Yes | Yes |
| Customer Registration | No | No | Yes |
| Create Staff Accounts | Yes | No | No |
| Manage Products | Yes | No | No |
| Manage Subscription Plans | Yes | No | No |
| Manage Discounts | Yes | No | No |
| Manage Quotations | Yes | No | No |
| Create Subscriptions | Yes | Yes | No |
| View Subscriptions | Yes | Yes | Own only |
| Pause/Resume Subscriptions | Yes | Yes | Own only |
| Run Recurring Billing | Yes | Yes | No |
| Manage Invoices | Yes | Yes | Own invoices |
| Record Payments | Yes | Yes | Own invoices |
| View Financial Reports | Yes | Yes | No |

## Technology Stack

| Component | Technologies |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| Database ORM | SQLAlchemy |
| Database | PostgreSQL, SQLite |
| Data Validation | Pydantic |
| Authentication | JWT, PyJWT |
| Password Security | PBKDF2-HMAC-SHA256 |
| Frontend | HTML, CSS, JavaScript |
| API Server | Uvicorn |
| Testing | Pytest, HTTPX |
| Containerization | Docker, Docker Compose |

## Project Structure

```text
Subscription_Management_System_Odoo_Hackathon/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── billing.py
│   │   └── seed.py
│   │
│   ├── tests/
│   │   └── test_flow.py
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── frontend/
│   └── index.html
│
├── .gitignore
└── README.md
```

### Backend Files

| File | Description |
|---|---|
| `main.py` | FastAPI application, API routes, authentication, subscriptions, invoices, payments, and reports |
| `models.py` | SQLAlchemy database models |
| `schemas.py` | Pydantic request validation schemas |
| `database.py` | Database engine and session configuration |
| `security.py` | Password hashing, JWT generation, and role-based authorization |
| `billing.py` | Recurring billing, invoice generation, discount calculations, and payment processing |
| `seed.py` | Initial database records and demo accounts |
| `test_flow.py` | End-to-end workflow testing |

## Installation and Setup

### Prerequisites

- Python 3.10 or above
- pip
- Git
- A modern web browser

For Docker deployment:

- Docker Desktop or Docker Engine
- Docker Compose

### Step 1: Clone the Repository

```bash
git clone https://github.com/niya-benny/Subscription_Management_System_Odoo_Hackathon.git
```

Navigate to the project directory:

```bash
cd Subscription_Management_System_Odoo_Hackathon
```

### Step 2: Navigate to Backend

```bash
cd backend
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment.

**Windows:**

```powershell
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Start the Backend Server

```bash
python -m uvicorn app.main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

### Step 6: Open the Frontend

Navigate to the project directory and open:

```text
frontend/index.html
```

You can open the HTML file directly in your browser.

Ensure that the API URL on the login screen is set to:

```text
http://127.0.0.1:8000
```

### Step 7: Access API Documentation

FastAPI automatically generates interactive API documentation.

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

The database tables and initial demo data are created automatically when the backend starts.

## Running with Docker

The project also includes Docker configuration for running the API with PostgreSQL.

Navigate to the backend directory:

```bash
cd backend
```

Build and start the containers:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

To stop the containers:

```bash
docker compose down
```

To remove the database volume as well:

```bash
docker compose down -v
```

**Warning:** Removing the volume permanently deletes the PostgreSQL data stored in it.

## Demo Credentials

The application automatically creates the following demo accounts when the database is initialized for the first time.

| Role | Email | Password |
|---|---|---|
| Admin | admin@brightloop.io | Admin@12345 |
| Staff | staff@brightloop.io | Staff@12345 |
| Customer | acme@shop.com | Cust@12345 |

> These credentials are intended only for local testing and demonstration. Do not use them in a production deployment.

## Application Workflow

The general application workflow is:

1. Admin logs into the system.
2. Admin configures products, product variants, subscription plans, tax rates, and discount rules.
3. Admin creates quotation templates if required.
4. Staff creates a subscription for a registered customer.
5. The subscription progresses through Draft, Quotation, Confirmed, and Active.
6. The recurring billing process checks active subscriptions and their next billing dates.
7. Invoices are generated for eligible billing periods.
8. Applicable discounts and taxes are calculated.
9. Staff confirms invoices.
10. Customers make payments against their invoices.
11. The system updates payment records and invoice statuses.
12. Admin and Staff monitor revenue, outstanding balances, active subscriptions, and overdue invoices through the dashboard.

## API Endpoints

The backend exposes REST APIs through FastAPI.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register a customer |
| POST | `/auth/login` | Authenticate a user |
| POST | `/auth/forgot` | Request password reset |
| POST | `/auth/reset` | Reset password |

### User Management

| Method | Endpoint | Description |
|---|---|---|
| POST | `/staff` | Create a staff account |
| GET | `/users/customers` | Retrieve customer list |

### Product and Catalog Management

| Method | Endpoint | Description |
|---|---|---|
| GET | `/products` | Retrieve products |
| POST | `/products` | Create a product |
| GET | `/plans` | Retrieve subscription plans |
| POST | `/plans` | Create a subscription plan |
| GET | `/taxes` | Retrieve tax rates |
| POST | `/taxes` | Create a tax rate |
| GET | `/templates` | Retrieve quotation templates |
| POST | `/templates` | Create a quotation template |
| GET | `/discounts` | Retrieve discounts |
| POST | `/discounts` | Create a discount |

### Subscription Management

| Method | Endpoint | Description |
|---|---|---|
| POST | `/subscriptions` | Create a subscription |
| GET | `/subscriptions` | Retrieve subscriptions |
| POST | `/subscriptions/{sid}/{action}` | Perform subscription lifecycle actions |

Supported actions include:

- `advance`
- `pause`
- `resume`
- `close`
- `renew`

### Invoice Management

| Method | Endpoint | Description |
|---|---|---|
| POST | `/billing/run` | Generate recurring invoices |
| GET | `/invoices` | Retrieve invoices |
| GET | `/invoices/{iid}` | Retrieve a specific invoice |
| POST | `/invoices/{iid}/{action}` | Perform invoice actions |

Supported invoice actions:

- `confirm`
- `cancel`
- `send`

### Payment Management

| Method | Endpoint | Description |
|---|---|---|
| POST | `/payments` | Record a payment |
| GET | `/payments` | Retrieve payment records |

### Reporting

| Method | Endpoint | Description |
|---|---|---|
| GET | `/reports/summary` | Retrieve financial summary |

## Business Logic

### Recurring Billing

The billing engine checks active subscriptions and identifies those with due billing dates.

It generates invoices for each eligible billing period and advances the next billing date according to the subscription plan.

The billing engine also supports catching up on missed billing periods.

### Duplicate Invoice Prevention

A unique database constraint on subscription ID and billing period prevents duplicate invoices from being created for the same subscription period.

This makes repeated billing runs safe against duplicate invoice creation.

### Discount Calculation

The system supports fixed-value and percentage-based discounts.

Discount eligibility is evaluated using:

- Discount start and end dates.
- Minimum quantity.
- Minimum purchase amount.
- Usage limits.
- Product or subscription association.

Eligible discounts are applied automatically during invoice generation.

### Tax Calculation

The system calculates applicable taxes based on configured tax rates and discounted invoice amounts.

The final invoice total is calculated using:

**Invoice Total = Untaxed Amount + Tax**

### Payment Validation

Payments can only be recorded against confirmed invoices.

The system validates that:

- Payment amount is greater than zero.
- Payment amount does not exceed the remaining balance.
- The invoice belongs to the customer when the request is made by a customer.

Once the full invoice amount is paid, the invoice status changes to `Paid`.

### Security and Authorization

- JWT authentication.
- Password hashing.
- Role-based access restrictions.
- Customers can only access their own subscription and invoice records.
- Administrative operations are restricted to authorized users.

## Testing

The project includes an end-to-end test that validates the subscription and billing workflow.

The test covers:

- User authentication.
- Role-based permissions.
- Customer registration validation.
- Discount application.
- Subscription creation.
- Recurring invoice generation.
- Duplicate invoice prevention.
- Tax and discount calculations.
- Payment validation.
- Financial reporting.

Run the tests from the `backend` directory:

```bash
pytest -q
```

The test uses a separate SQLite database.

## Environment Configuration

The backend supports the following environment variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./brightloop.db` | Database connection URL |
| `SECRET_KEY` | `dev-secret-change-me` | JWT signing secret |

For PostgreSQL, the database URL follows this format:

```text
postgresql+psycopg2://username:password@localhost:5432/database_name
```

For production deployment, use a strong secret key and secure database credentials. Never commit real credentials or secrets to GitHub.

## Future Enhancements

Potential improvements for future versions include:

- Integration with an actual Odoo instance.
- Payment gateway integration.
- Automated email notifications.
- PDF invoice generation and downloads.
- Scheduled recurring billing using a background scheduler.
- Database migrations using Alembic.
- Enhanced analytics and financial visualizations.
- Improved production security and deployment configuration.
- Detailed audit logs and transaction history.

---

**Developed as a Subscription Management System hackathon project.**
