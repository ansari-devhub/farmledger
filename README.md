# FarmLedger

A multi-tenant farm management API for tracking everything that happens between planting a crop and getting paid for it — inputs, labour, harvests, and sales — built with Django REST Framework.

Every farm owner sees only their own data. Every expense, harvest, and labour log traces back to a single `PlantingRecord`, so a farmer (or a report) can answer: *what did this crop actually cost me, and what did it bring in?*

## Why

Smallholder and small-commercial farms in Kenya rarely track input costs, labour, and sales in one place — it's scattered across notebooks and M-Pesa statements. FarmLedger gives each farm owner a single source of truth: register a farm, open a season, plant a crop, log expenses and labour against that planting, record the harvest, and sell it to a buyer with partial-payment tracking.

## Features

- **JWT authentication** — register, obtain token pair, refresh, via `djangorestframework-simplejwt`
- **Ownership-based permissions** — object-level checks (`IsFarmOwner`, `IsPlantingOwner`) ensure a user can only ever touch their own farm's data, no matter how deep the relation chain
- **Farm structure** — Farms → Seasons → Plantings, with a shared, admin-managed Crop reference table
- **Planting-centric ledger** — `PlantingRecord` is the spine every input expense, harvest, and labour log hangs off of
- **Input expense tracking** — seed, fertilizer, pesticide, herbicide, equipment costs per planting
- **Labour logging** — workers, daily rates, task types, days worked, pay per log
- **Harvest & sales** — harvest by quality grade, sell to buyers in KSh with partial-payment and outstanding-balance tracking
- **Auto-generated API docs** — OpenAPI schema via `drf-spectacular`
- **UUID primary keys + timestamps** on every model via a shared abstract base

## Tech stack

| Layer | Choice |
|---|---|
| Framework | Django 5.0 + Django REST Framework |
| Auth | SimpleJWT |
| Database | PostgreSQL |
| Cache | Redis (`django-redis`) |
| API docs | drf-spectacular (OpenAPI 3) |
| Testing | pytest-django + factory-boy + pytest-cov |
| Server | Gunicorn |
| Containerization | Docker + docker-compose |

## Data model

```
Farm (owner: User)
 └── Season (name, start_date, end_date)
      └── PlantingRecord (crop, date_planted, field_area_acres)
           ├── InputExpense   (input_type, item_name, quantity, amount_ksh)
           ├── LabourLog      (worker, task_type, days_worked, total_pay_ksh)
           └── HarvestRecord  (harvest_date, quantity_kg, quality_grade)
                └── Sale      (buyer, kg_sold, price_per_kg_ksh, payment_status)

Crop   — shared reference table (cereal, legume, vegetable, fruit, tuber, other)
Buyer  — belongs to a Farm
Worker — belongs to a Farm, has a daily_rate_ksh
```

Every write operation is checked against the requesting user's ownership of the farm at the top of that chain, even for nested resources like harvests and labour logs.

## Project structure

```
farmledger/
├── apps/
│   ├── core/         # abstract base model (UUID PK + timestamps), shared permissions
│   ├── users/         # custom user model, register/login/refresh
│   ├── farms/         # Farm, Season, Crop
│   ├── operations/    # PlantingRecord, InputExpense
│   ├── labour/        # Worker, LabourLog
│   └── commerce/       # Buyer, HarvestRecord, Sale
├── config/
│   └── settings/       # base / dev / prod split
├── docker-compose.yml   # web + postgres + redis
├── Dockerfile
├── requirements.txt
├── pytest.ini
└── schema.yaml          # generated OpenAPI schema
```

## Getting started

### With Docker (recommended)

```bash
git clone https://github.com/ansari-devhub/farmledger.git
cd farmledger
cp .env.example .env   # fill in SECRET_KEY, DB and Redis settings
docker-compose up --build
```

The API will be available at `http://localhost:8000/`.

### Without Docker

```bash
git clone https://github.com/ansari-devhub/farmledger.git
cd farmledger
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Requires a running PostgreSQL instance and Redis instance matching your `.env` config.

## Auth flow

```
POST /auth/register/     → create a farm-owner account
POST /auth/login/        → obtain access + refresh JWT pair
POST /auth/refresh/      → rotate access token
```

Authenticated requests use `Authorization: Bearer <access_token>`.

## API docs

Once running, the OpenAPI schema is available via drf-spectacular. Typical routes:

- `/api/schema/` — raw OpenAPI schema
- `/api/docs/` — Swagger/Redoc UI (if wired up in `config/urls.py`)

## Testing

```bash
pytest
```

Coverage is tracked via `pytest-cov`; test data is built with `factory-boy`.

## Roadmap

- [ ] M-Pesa Daraja integration for sale payments
- [ ] Per-season / per-planting profitability reports (cost vs. revenue)
- [ ] Celery-based reminders (e.g. overdue buyer payments)
- [ ] Swagger UI wired into `config/urls.py` by default

## License

Not yet specified — add a `LICENSE` file to make reuse terms explicit.
