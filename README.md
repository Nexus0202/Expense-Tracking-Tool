# Expense-Tracking-Tool

# 💰 Expense Tracker — Full Stack Application

A production-ready expense tracking application built with **FastAPI** (Python backend) and **Vanilla HTML/CSS/JS** frontend. Supports manual expense entry and AI-powered PDF bank statement parsing via **Google Gemini**. No login required — open the app and start tracking immediately.

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Setup & Installation](#setup--installation)
5. [Environment Variables](#environment-variables)
6. [Running the Application](#running-the-application)
7. [Using the UI](#using-the-ui)
8. [API Reference](#api-reference)
9. [Database & Migrations](#database--migrations)
10. [Architecture Overview](#architecture-overview)
11. [How PDF Parsing Works](#how-pdf-parsing-works)
12. [Example API Requests (curl)](#example-api-requests-curl)

---

## Features

| Feature | Description |
|---|---|
| **Expense CRUD** | Create, view, edit, and delete expense records |
| **Filters** | Filter expenses by date range and category |
| **Pagination** | Browse large lists page by page |
| **Dashboard** | Summary cards, category pie chart, monthly bar chart |
| **PDF Upload** | Upload a bank statement PDF — Gemini AI extracts all transactions automatically |
| **No login required** | Open the app and use it directly — no account or password needed |
| **Swagger UI** | Auto-generated interactive API docs at `/docs` |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend framework** | FastAPI (Python) |
| **Database** | SQLite via SQLAlchemy 2.x ORM |
| **Migrations** | Alembic |
| **Data validation** | Pydantic v2 |
| **PDF parsing** | PyMuPDF (`fitz`) |
| **AI extraction** | Google Gemini API (`gemini-1.5-flash`) |
| **Retry logic** | `tenacity` (for Gemini API calls) |
| **Frontend** | Vanilla HTML + CSS + JavaScript (no frameworks) |
| **Charts** | Chart.js (loaded from CDN) |

---

## Project Structure

```
expense_tracking_tool/
│
├── app/                          ← Backend (FastAPI)
│   ├── main.py                   ← App entry point, middleware, startup
│   ├── config.py                 ← Settings loaded from .env
│   │
│   ├── api/                      ← HTTP layer (routes only, no business logic)
│   │   ├── deps.py               ← Shared dependencies (DB session)
│   │   └── v1/
│   │       ├── router.py         ← Mounts all sub-routers at /api/v1
│   │       ├── expenses.py       ← CRUD endpoints for expenses
│   │       ├── dashboard.py      ← GET /dashboard/summary
│   │       └── pdf_upload.py     ← POST /upload/pdf
│   │
│   ├── models/                   ← SQLAlchemy database models (table definitions)
│   │   ├── base.py               ← DeclarativeBase (shared by all models)
│   │   └── expense.py            ← Expense table
│   │
│   ├── schemas/                  ← Pydantic schemas (request & response shapes)
│   │   ├── expense.py            ← ExpenseCreate, ExpenseUpdate, ExpenseResponse
│   │   └── common.py             ← PaginatedResponse, DashboardSummary, etc.
│   │
│   ├── services/                 ← Business logic (pure Python, no HTTP concerns)
│   │   ├── expense_service.py    ← DB queries, aggregations, bulk create
│   │   ├── gemini_service.py     ← Gemini API calls + JSON parsing + retry
│   │   └── pdf_service.py        ← PDF → plain text using PyMuPDF
│   │
│   ├── database/
│   │   └── session.py            ← SQLAlchemy engine + get_db() dependency
│   │
│   └── utils/
│       ├── exceptions.py         ← Custom exception classes + FastAPI handlers
│       └── logging_config.py     ← Structured logging setup
│
├── alembic/                      ← Database migration system
│   ├── env.py                    ← Migration environment config
│   ├── script.py.mako            ← Migration file template
│   └── versions/
│       └── 001_initial_schema.py ← First migration (creates expenses table)
│
├── frontend/                     ← UI (plain HTML/CSS/JS, no build step)
│   ├── index.html                ← All pages (dashboard + expenses + upload)
│   ├── style.css                 ← All styles (CSS variables, layout, components)
│   └── app.js                    ← All JavaScript (API calls, DOM, charts)
│
├── alembic.ini                   ← Alembic configuration file
├── requirements.txt              ← Python dependencies
├── .env.example                  ← Template for your .env file
└── README.md                     ← This file
```

---

## Setup & Installation

### Prerequisites

- Python 3.10 or higher
- A Google Gemini API key — free at [https://aistudio.google.com](https://aistudio.google.com)

### Step 1 — Open the project folder

```bash
cd c:\prasanta\expense_tracking_tool
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv
```

Activate it:

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Create your `.env` file

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and set your Gemini API key (see [Environment Variables](#environment-variables) below).

---

## Environment Variables

Edit the `.env` file in the project root:

```env
# Application
APP_NAME=Expense Tracker API
DEBUG=false                        # Set to true to see SQL queries in terminal

# Database
DATABASE_URL=sqlite:///./expense_tracker.db   # SQLite file, created automatically

# Google Gemini AI (required for PDF upload feature)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-flash
GEMINI_MAX_RETRIES=3
```

> **How to get a Gemini API key:**
> 1. Go to [https://aistudio.google.com](https://aistudio.google.com)
> 2. Click **Get API key** → **Create API key**
> 3. Paste it into your `.env` file

---

## Running the Application

### Start the backend server

```bash
uvicorn app.main:app --reload --port 8000
```

The server starts at **http://localhost:8000**. The database file (`expense_tracker.db`) is created automatically on first run.

### Open the UI

Double-click `frontend/index.html` — the app opens immediately with no login screen.

> **If you see a CORS error**, serve the frontend with a local server instead:
>
> ```bash
> cd frontend
> python -m http.server 3000
> # Then open http://localhost:3000
> ```

### Open the API documentation

| URL | Description |
|---|---|
| http://localhost:8000/docs | Swagger UI — interactive, try any endpoint in the browser |
| http://localhost:8000/redoc | ReDoc — clean readable documentation |
| http://localhost:8000/health | Health check — returns `{"status": "healthy"}` |

---

## Using the UI

The app opens directly on the **Dashboard**. Use the sidebar to navigate between three sections.

---

### Dashboard

```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Total Spent │ │Transactions │ │Top Category │ │Avg per Txn  │
│  ₹12,450   │ │     47      │ │    Food     │ │   ₹264     │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘

┌──────────────────────┐  ┌────────────────────────────────────┐
│   Category Donut     │  │         Monthly Bar Chart          │
│  (spending by type)  │  │  (Jan, Feb, Mar … spending trend)  │
└──────────────────────┘  └────────────────────────────────────┘
```

- Use the **From / To date** pickers (top right) to filter the summary to a date range
- Click **Clear** to reset and show all-time data

---

### Expenses

A table of all your expense records.

- **+ Add Expense** (top right) — opens a modal form to add a new record
- **Filter bar** — filter by date range and/or category, then click **Search**
- **Reset** — clears all filters
- Each row has **✏️ Edit** and **🗑️ Delete** actions

#### Add / Edit Expense form fields

| Field | Required | Notes |
|---|---|---|
| Amount | Yes | Must be greater than 0 |
| Date | Yes | Defaults to today |
| Category | Yes | Choose from the dropdown |
| Description | No | Optional note, max 500 characters |

---

### Upload PDF

Upload a bank statement, receipt, or any financial PDF to auto-extract expenses.

1. **Drag and drop** a PDF onto the upload area, or **click** to browse
2. The filename appears below the drop zone
3. Click **Extract Expenses with AI**
4. Gemini reads the text and returns a structured list of transactions
5. All valid transactions are saved with `source = "pdf"`
6. A result table shows what was found
7. Click **View All Expenses** to see them in the Expenses tab

> **Note:** PDF upload requires a valid `GEMINI_API_KEY` in `.env`.

---

## API Reference

All endpoints are prefixed with `/api/v1`. No authentication is required.

### Expenses

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/expenses/` | Create a new expense |
| `GET` | `/expenses/` | List all expenses (filters + pagination) |
| `GET` | `/expenses/{id}` | Get one expense by UUID |
| `PATCH` | `/expenses/{id}` | Partially update an expense |
| `DELETE` | `/expenses/{id}` | Delete an expense |

**Query parameters for `GET /expenses/`:**

| Parameter | Type | Description |
|---|---|---|
| `start_date` | datetime | Filter on or after this date (ISO 8601) |
| `end_date` | datetime | Filter on or before this date (ISO 8601) |
| `category` | string | Partial match, case-insensitive |
| `page` | int | Page number, starts at 1 (default: 1) |
| `page_size` | int | Results per page, max 100 (default: 20) |

**Expense object:**

| Field | Type | Description |
|---|---|---|
| `id` | string (UUID) | Auto-generated unique ID |
| `amount` | float | Positive number |
| `category` | string | e.g. Food, Transport, Bills |
| `description` | string | Optional note |
| `date` | datetime | When the expense occurred |
| `source` | string | `"manual"` or `"pdf"` |
| `created_at` | datetime | Record creation timestamp |
| `updated_at` | datetime | Last update timestamp |

---

### Dashboard

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/dashboard/summary` | Aggregated totals, category breakdown, monthly breakdown |

**Query parameters:** `start_date`, `end_date` (both optional, ISO 8601)

**Response example:**

```json
{
  "total_expenses": 12450.00,
  "total_count": 47,
  "by_category": [
    { "category": "Food",      "total": 4200.00, "count": 18 },
    { "category": "Transport", "total": 2100.00, "count": 12 }
  ],
  "by_month": [
    { "year": 2026, "month": 3, "total": 5200.00, "count": 21 },
    { "year": 2026, "month": 4, "total": 7250.00, "count": 26 }
  ]
}
```

---

### PDF Upload

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload/pdf` | Upload PDF, extract and save expenses via Gemini AI |

- **Request:** `multipart/form-data` with a `file` field containing the PDF
- **Response:** Array of created expense objects
- Returns `[]` if no transactions were detected

---

### Health Check

| Method | Endpoint | Response |
|---|---|---|
| `GET` | `/health` | `{"status": "healthy", "app": "...", "version": "1.0.0"}` |

---

## Database & Migrations

### Development (automatic)

The app creates all tables automatically on startup — no manual steps needed.

### Production (Alembic)

```bash
# Apply all pending migrations
alembic upgrade head

# Check current version
alembic current

# View migration history
alembic history

# Generate a new migration after changing a model
alembic revision --autogenerate -m "add tag column to expenses"

# Roll back one step
alembic downgrade -1
```

The initial migration is at [alembic/versions/001_initial_schema.py](alembic/versions/001_initial_schema.py).

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                   Browser (UI)                        │
│   index.html  +  style.css  +  app.js                │
│   • Calls API with fetch()                            │
│   • Renders charts with Chart.js                      │
└───────────────────────┬──────────────────────────────┘
                        │ HTTP REST (no auth)
┌───────────────────────▼──────────────────────────────┐
│                  FastAPI Backend                       │
│                                                       │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────┐  │
│  │  Routes  │──▶│ Services │──▶│ SQLAlchemy ORM   │  │
│  │ (api/v1) │   │(business │   │ (database layer) │  │
│  │          │   │  logic)  │   │                  │  │
│  └──────────┘   └──┬───┬───┘   └────────┬─────────┘  │
│                    │   │                │             │
│            ┌───────┘   └──────┐         │             │
│            ▼                  ▼         ▼             │
│      GeminiService       PDFService   SQLite DB       │
│      (Google AI API)     (PyMuPDF)    (local file)    │
└──────────────────────────────────────────────────────┘
```

### Key design patterns

| Pattern | Where | What it means |
|---|---|---|
| **Separation of concerns** | routes vs services | Routes handle HTTP; services handle logic |
| **Dependency Injection** | `deps.py`, `get_db()` | FastAPI provides the DB session automatically per request |
| **Pydantic validation** | `schemas/` | All input is validated before it reaches the service layer |
| **Service layer** | `services/` | All database access and business logic lives here |
| **Retry pattern** | `tenacity` in Gemini service | Automatically retries failed AI calls up to 3 times |

---

## How PDF Parsing Works

```
1. You upload a PDF file
        │
        ▼
2. PDFService reads the file bytes
   PyMuPDF (fitz) extracts raw text page by page
        │
        ▼
3. GeminiService sends the text to Google Gemini
   with this strict prompt:
   "Return ONLY a JSON array of expenses.
    Each item must have: date, amount, category, description"
        │
        ▼
4. Gemini returns JSON (may include markdown fences like ```json)
   GeminiService strips the fences and parses the JSON
        │
        ▼
5. Each item is validated:
   • date must be YYYY-MM-DD format
   • amount must be a positive number
   • category is mapped to a known value (or "Other")
   • Invalid items are skipped with a warning log
        │
        ▼
6. Valid expenses are saved to the database with source = "pdf"
        │
        ▼
7. The saved records are returned to the UI as a result table
```

If Gemini fails or returns malformed JSON, `tenacity` retries up to **3 times** with exponential back-off (2s → 4s → 8s) before returning an error.

---

## Example API Requests (curl)

### Create an expense

```bash
curl -X POST http://localhost:8000/api/v1/expenses/ \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 250.00,
    "category": "Food",
    "description": "Lunch at cafe",
    "date": "2026-04-22T12:00:00",
    "source": "manual"
  }'
```

### List expenses with filters

```bash
curl "http://localhost:8000/api/v1/expenses/?category=Food&start_date=2026-04-01T00:00:00&page=1&page_size=10"
```

### Update an expense

```bash
curl -X PATCH http://localhost:8000/api/v1/expenses/<expense-id> \
  -H "Content-Type: application/json" \
  -d '{"amount": 300.00, "description": "Updated description"}'
```

### Delete an expense

```bash
curl -X DELETE http://localhost:8000/api/v1/expenses/<expense-id>
```

### Get dashboard summary

```bash
curl "http://localhost:8000/api/v1/dashboard/summary?start_date=2026-01-01T00:00:00"
```

### Upload a PDF

```bash
curl -X POST http://localhost:8000/api/v1/upload/pdf \
  -F "file=@/path/to/bank_statement.pdf"
```

---

## Category Reference

| Category | Examples |
|---|---|
| Food | Restaurants, groceries, cafes |
| Transport | Fuel, Uber, bus tickets, metro |
| Shopping | Clothes, electronics, Amazon |
| Bills | Electricity, water, internet, rent |
| Entertainment | Movies, OTT subscriptions, games |
| Healthcare | Medicines, doctor visits, labs |
| Travel | Hotels, flights, holiday expenses |
| Education | Courses, books, tuition fees |
| Other | Anything that doesn't fit above |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Activate the virtual environment and run `pip install -r requirements.txt` |
| CORS error in browser | Serve via `cd frontend && python -m http.server 3000` instead of opening the file directly |
| Gemini returns no results | Check that `GEMINI_API_KEY` is set correctly in `.env` |
| PDF shows "No text found" | The PDF may be image-only (scanned). PyMuPDF only reads text-based PDFs |
| Port 8000 already in use | Use a different port: `uvicorn app.main:app --reload --port 8001` |
| `alembic: command not found` | Activate the virtual environment first |

