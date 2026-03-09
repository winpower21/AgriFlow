# AgriFlow - Backend Capability Report

**Generated:** 2026-03-07
**Codebase Version:** 1.0.0 (commit c8fca7e)
**Status:** Early development — has errors and incomplete/unimplemented features

---

## 1. Architecture Overview

| Layer | Technology | Notes |
|-------|-----------|-------|
| Framework | FastAPI (Python) | Async-capable, currently uses sync endpoints |
| ORM | SQLAlchemy 2.x | Modern `Mapped`/`mapped_column` style |
| Database | PostgreSQL 17 | Via `psycopg` driver |
| Migrations | Alembic | 13 migration versions exist |
| Auth | JWT (HS256) | Via `python-jose` + `bcrypt` |
| Package Mgmt | `uv` | Modern Python package manager |
| Frontend | Vue 3 + Vite 7 | Composition API, Pinia, Axios |

### Backend Structure

```
backend/app/
├── main.py                  # App factory, lifespan, CORS, router mounting
├── config.py                # Pydantic Settings (env-based config)
├── database.py              # SQLAlchemy engine, session, Base, get_db()
├── core/
│   ├── security.py          # JWT creation, bcrypt hashing
│   └── dependencies.py      # Auth dependencies (get_current_user, roles_required/accepted)
├── models/                  # 12 ORM model files (22 tables)
├── schemas/                 # 12 Pydantic v2 schema files
├── crud/                    # 7 service files (class-based pattern)
├── routers/                 # 10 router files
└── api/
    └── openweathermap.py    # External API client
```

---

## 2. Implemented Features (Working)

### 2.1 Authentication & Authorization
- **JWT Bearer Auth** — HS256 tokens with configurable expiry (default 60 min)
- **Password hashing** — bcrypt via `bcrypt` library
- **Role-based access control** — Three seeded roles: `admin`, `manager`, `user`
- **Many-to-many user-roles** — via `user_roles` association table
- **First-user auto-admin** — First registered user gets admin role automatically
- **Dependency factories** — `roles_required("admin")` and `roles_accepted(["admin", "manager"])`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/login` | POST | Public | OAuth2 token login (email as username) |
| `/users/register` | POST | Public | Register new user |
| `/users/all` | GET | Admin | List all users |
| `/users/unverified` | GET | Admin | List unverified users |
| `/users/update/{id}` | PUT | Admin | Update user details |
| `/users/delete-user/{id}` | DELETE | Admin | Delete a user |
| `/users/change-role/{id}` | PUT | Admin | Change user's role |

### 2.2 Plantation Management
- Full CRUD for plantations (name + location)
- **Location tracking** — city, state, country, latitude, longitude (one-to-one with plantation)
- **Lease history** — Tracks lease agreements (start/end dates, cost) as append-only history
- **Safe delete** — Pre-delete check for lease history; force flag required if history exists

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/plantations/` | GET | Authenticated | List all plantations |
| `/plantations/{id}` | GET | Authenticated | Get plantation detail |
| `/plantations/{id}/lease-history` | GET | Authenticated | Get lease history |
| `/plantations/{id}/delete-check` | GET | Authenticated | Check before delete |
| `/plantations/` | POST | Admin | Create plantation |
| `/plantations/{id}` | PUT | Admin | Update plantation |
| `/plantations/{id}` | DELETE | Admin | Delete (force flag) |

### 2.3 Personnel Management
- Full CRUD for workers/staff
- **Wage types** — Configurable (e.g., DAILY, PER_KG)
- **Current rate tracking** — Personnel have a mutable `current_rate`
- Eager-loaded wage type data in responses

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/personnel/` | GET | Authenticated | List all personnel |
| `/personnel/wage-types` | GET | Authenticated | List wage types |
| `/personnel/{id}` | GET | Authenticated | Get personnel detail |
| `/personnel/` | POST | Authenticated | Create personnel |
| `/personnel/{id}` | PUT | Authenticated | Update personnel |
| `/personnel/{id}` | DELETE | Authenticated | Delete personnel |

### 2.4 Expense Tracking
- Create and list expenses
- Filter expenses by plantation
- Category validation before creation
- Expenses linkable to plantation and/or vehicle

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/expenses/` | GET | Authenticated | List all expenses |
| `/expenses/by-plantation/{id}` | GET | Authenticated | Filter by plantation |
| `/expenses/` | POST | Admin | Create expense |

### 2.5 Settings / Configuration Management
Full CRUD for all configurable lookup tables:

| Entity | Endpoints | Description |
|--------|-----------|-------------|
| **Transformation Types** | `/settings/transformation-types` | Processing step types (HARVEST, CLEAN, DRY, etc.) |
| **Wage Types** | `/settings/wage-types` | How workers are paid (DAILY, PER_KG, etc.) |
| **Batch Stages** | `/settings/batch-stages` | Material processing stages |
| **Expense Categories** | `/settings/expense-categories` | Expense classification |

Each supports: GET all, POST create, PUT update, DELETE.

### 2.6 Weather Integration (Google Maps)
- **Location autocomplete** — Google Places Autocomplete proxy (regions only)
- **Place details** — Lat/lng and address from place ID
- **Current conditions** — Google Weather API proxy
- **Daily forecast** — Configurable forecast days (1-10)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/weather/search-locations` | GET | Public | Location autocomplete |
| `/api/weather/place-details` | GET | Public | Place lat/lng details |
| `/api/weather/current` | GET | Public | Current weather |
| `/api/weather/forecast` | GET | Public | Daily forecast |

### 2.7 General / Utility
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | Public | API health check / welcome |
| `/health` | GET | Public | Health check |
| `/connection` | GET | Public | DB connection test |
| `/home` | GET | Authenticated | User welcome + role info |
| `/admin` | GET | Admin | Admin dashboard check |

---

## 3. Database Models (Defined but NOT Fully Wired to API)

The following models exist in the ORM layer with full relationship definitions, but **lack CRUD services and/or router endpoints**:

### 3.1 Batch System
**Models:** `Batch`, `BatchStage`

- Batch tracks physical material quantities (weight in kg)
- `batch_code` — unique identifier per batch
- `initial_weight_kg` / `remaining_weight_kg` — tracks consumption
- `is_depleted` — flags when material is used up
- `parent_batch_id` — self-referential FK for lineage tracking (material splitting/transformation trees)
- `stage_id` — FK to configurable BatchStage
- `plantation_id` — origin plantation

**Status:** Schema exists (`BatchSchema`, `BatchCreate`, `BatchUpdate`). No CRUD service. No router endpoints. BatchStage is manageable via Settings, but Batch itself has no API.

### 3.2 Transformation System
**Models:** `Transformation`, `TransformationType`, `TransformationInput`, `TransformationOutput`

- Records processing events (e.g., HARVEST, CLEAN, DRY)
- Each transformation has a date range (`from_date`, `to_date`)
- **Inputs** — links source batches to transformation with `input_weight`
- **Outputs** — links result batches to transformation with `output_weight`
- Related to personnel assignments, vehicle usage, consumable consumption

**Status:** `TransformationType` is manageable via Settings. `Transformation` itself has full schemas (`TransformationSchema`, `TransformationCreate`) but **no CRUD service and no router endpoints**.

### 3.3 Personnel Assignment (Historical Cost Freezing)
**Model:** `TransformationPersonnel`

- Links personnel to transformations
- **Freezes wage data at time of assignment:** `rate_at_time`, `wage_type_at_time_id`, `wage_paid`
- Supports daily (`days_worked`) and per-kg (`output_weight_considered`) wage calculations
- Tracks `additional_payments` with description

**Status:** Model and schema exist. No CRUD. No endpoints. Cannot assign personnel to transformations via API.

### 3.4 Vehicle Usage (Historical Cost Freezing)
**Model:** `TransformationVehicle`

- Links vehicles to transformations
- Tracks `hours_used`, `fuel_consumed`
- **Freezes costs:** `cost_per_hour`, `total_cost`

**Status:** Vehicle model exists but has no CRUD or router. `TransformationVehicle` schema exists but no endpoints.

### 3.5 Consumable Inventory (FIFO Costing)
**Models:** `Consumable`, `ConsumablePurchase`, `ConsumableConsumption`, `ConsumptionAllocation`

- **Consumable** — item definition (name, unit)
- **ConsumablePurchase** — purchase lots with FIFO ordering by `purchase_date`
  - Tracks `remaining_quantity` for FIFO consumption
  - `unit_cost` frozen at purchase time
  - DB constraints: `remaining_quantity >= 0` and `remaining_quantity <= quantity`
- **ConsumableConsumption** — usage in transformations
- **ConsumptionAllocation** — FIFO allocation linking consumption to purchase lots
  - Allocates from oldest purchase lot first
  - Freezes `cost` per allocation

**Status:** All models defined. No CRUD services. No router endpoints. The entire consumable inventory system is unimplemented at the API level.

### 3.6 Sales & Retail Inventory (FIFO Costing)
**Models:** `RetailInventory`, `Sale`, `SaleAllocation`

- **RetailInventory** — retail-stage batches as sellable inventory lots
  - Tracks `quantity`, `remaining_quantity`, `cost_per_kg`
  - FIFO ordering by `created_date`
  - DB constraints for non-negative remaining quantity
  - Computed properties: `is_exhausted`, `sold_quantity`, `total_cost`
- **Sale** — sales transactions
  - `quantity_sold`, `selling_price`, `cost_of_goods_sold` (frozen)
  - Customer info (name, phone, address), invoice number
  - Computed properties: `unit_selling_price`, `profit`, `profit_margin`
- **SaleAllocation** — FIFO allocation from inventory lots to sales
  - `quantity_allocated`, `cost_allocated` (frozen)

**Status:** All models defined with comprehensive properties. No CRUD. No endpoints. The entire sales system is unimplemented at the API level.

### 3.7 Weather Data Storage
**Model:** `Weather`

- Stores weather readings: `temperature_c`, `humidity_percent`, `precipitation_mm`
- Linked to `Location` via FK

**Status:** Model exists. `WeatherCRUD` and `LocationCRUD` exist in `crud/weather.py` but reference non-existent imports (`WeatherData`, `WeatherDataSchema`). Not wired to any router. The Google weather proxy works but doesn't persist data.

---

## 4. Known Bugs and Issues

### 4.1 Critical
| Issue | Location | Description |
|-------|----------|-------------|
| **User model inconsistency** | `models/user.py:51` | Has both `role_id` (single FK) AND `roles` (M2M relationship). These can diverge. |
| **Weather CRUD broken imports** | `crud/weather.py:5-6` | References `WeatherData` and `WeatherDataSchema` which don't exist (model is `Weather`, schema is `WeatherSchema`) |
| **OpenWeatherMap router broken** | `routers/weather.py` | Uses GET with request body (`LocationSearchRequest`), which doesn't work in HTTP GET. Also imports non-existent `WeatherData` schema. Not mounted in `main.py` correctly (imported but note: `weather_google` is used instead). |
| **OpenWeatherMap API client inconsistency** | `api/openweathermap.py:38` | `get_weather_data()` takes `latitude, longitude` params but the router calls it with `city` string |
| **Config duplicate field** | `config.py:9,29` | `APP_NAME` defined twice — first as "AgriFlow", then overwritten as "FastAPI Backend" |
| **Debug print statements** | Multiple files | Production debug prints in `dependencies.py`, `crud/user.py`, `routers/auth.py` |

### 4.2 Moderate
| Issue | Location | Description |
|-------|----------|-------------|
| **Unverified users query bug** | `crud/user.py:46` | `not User.is_verified` — Python `not` on column object, should be `User.is_verified == False` or `~User.is_verified` |
| **Delete user returns bool** | `crud/user.py:108-116` | Returns `True/False` but router expects User object for `response_model=User` |
| **Deprecated declarative_base** | `database.py:3` | Uses `sqlalchemy.ext.declarative.declarative_base` — deprecated in SQLAlchemy 2.x, should use `sqlalchemy.orm.DeclarativeBase` |
| **No session cleanup in lifespan** | `main.py:18-35` | `db = SessionLocal()` opened but never closed in the lifespan context manager |
| **API key leak in error** | `routers/weather_google.py:40` | Error detail includes `settings.GOOGLE_MAPS_API_KEY` value |
| **Weather endpoints not authenticated** | `routers/weather_google.py` | No auth dependency — anyone can proxy requests through the API |
| **Batch __repr__ references wrong attribute** | `models/batch.py:81` | References `self.weight_kg` which doesn't exist (should be `self.remaining_weight_kg`) |

### 4.3 Minor
| Issue | Location | Description |
|-------|----------|-------------|
| No test suite | — | No tests exist |
| No linting configured | — | No ruff/flake8/mypy setup |
| No input validation | Multiple | No field-level validation on schemas (min/max lengths, value ranges) |
| No pagination on most list endpoints | Routers | Most GET-all endpoints return unbounded results |
| CORS allows all methods/headers | `main.py:56-57` | Overly permissive for production |

---

## 5. Feature Completeness Matrix

| Domain | Models | Schemas | CRUD | Router | Status |
|--------|--------|---------|------|--------|--------|
| Auth/Users | DONE | DONE | DONE | DONE | **Working** |
| Roles | DONE | DONE | DONE | DONE | **Working** |
| Plantations | DONE | DONE | DONE | DONE | **Working** |
| Lease History | DONE | DONE | DONE | DONE | **Working** |
| Locations | DONE | DONE | Partial | Partial | **Partial** (created via plantation) |
| Personnel | DONE | DONE | DONE | DONE | **Working** |
| Expenses | DONE | DONE | DONE | DONE | **Working** (no update/delete) |
| Expense Categories | DONE | DONE | DONE | DONE | **Working** |
| Transformation Types | DONE | DONE | DONE | DONE | **Working** |
| Wage Types | DONE | DONE | DONE | DONE | **Working** |
| Batch Stages | DONE | DONE | DONE | DONE | **Working** |
| Batches | DONE | DONE | NONE | NONE | **Not implemented** |
| Transformations | DONE | DONE | NONE | NONE | **Not implemented** |
| Personnel Assignments | DONE | DONE | NONE | NONE | **Not implemented** |
| Vehicles | DONE | Partial | NONE | NONE | **Not implemented** |
| Vehicle Usage | DONE | DONE | NONE | NONE | **Not implemented** |
| Consumables | DONE | NONE | NONE | NONE | **Not implemented** |
| Consumable Purchases | DONE | NONE | NONE | NONE | **Not implemented** |
| Consumable Consumption | DONE | DONE | NONE | NONE | **Not implemented** |
| Retail Inventory | DONE | NONE | NONE | NONE | **Not implemented** |
| Sales | DONE | NONE | NONE | NONE | **Not implemented** |
| Sale Allocations | DONE | NONE | NONE | NONE | **Not implemented** |
| Weather (Google) | DONE | DONE | NONE | DONE | **Working** (proxy only, no persistence) |
| Weather (OWM) | DONE | Partial | Broken | Broken | **Broken** |

---

## 6. Recommendations for Next Steps

### Priority 1 — Fix Critical Bugs
1. Fix User model `role_id` / `roles` M2M inconsistency (choose one pattern)
2. Fix `crud/weather.py` broken imports
3. Remove debug print statements
4. Fix `config.py` duplicate `APP_NAME`
5. Close DB session in lifespan
6. Remove API key from error messages

### Priority 2 — Core Business Logic (The Pipeline)
These are the heart of AgriFlow — the crop processing pipeline:

1. **Batch CRUD** — Create, list, update, track batches of material
2. **Transformation CRUD** — Record processing events with inputs/outputs
3. **Batch lineage** — Query transformation history / parent-child trees
4. **Personnel assignment to transformations** — With historical cost freezing
5. **Vehicle usage tracking** — With cost freezing

### Priority 3 — Inventory & Sales
1. **Consumable management** — CRUD for consumables, purchases, consumption
2. **FIFO consumable allocation** — Implement the allocation algorithm
3. **Retail inventory** — Move batches to retail stage
4. **Sales recording** — Record sales with FIFO inventory allocation
5. **COGS calculation** — Cost of goods sold from allocation chain

### Priority 4 — Reporting & Analytics
1. **Batch cost rollup** — Sum all costs (personnel, vehicle, consumable) for a batch
2. **Profit/loss per sale** — Revenue minus FIFO-allocated COGS
3. **Plantation yield reports** — Production volume by plantation
4. **Expense summaries** — By category, plantation, date range

### Priority 5 — Infrastructure
1. Add test suite (pytest + httpx for async)
2. Add linting (ruff)
3. Add input validation to schemas
4. Add pagination to list endpoints
5. Persist weather data to database
6. Tighten CORS for production
7. Add proper logging (replace print statements)

---

## 7. API Endpoint Summary (All Current Endpoints)

Total: **37 endpoints** across 8 routers

| Router | Prefix | Endpoints | Auth Level |
|--------|--------|-----------|------------|
| auth | `/auth` | 1 | Public |
| users | `/users` | 5 | Mixed (register public, rest admin) |
| personnel | `/personnel` | 6 | Authenticated |
| plantations | `/plantations` | 7 | Mixed (reads auth, writes admin) |
| expenses | `/expenses` | 3 | Mixed (reads auth, create admin) |
| settings | `/settings` | 16 | Authenticated |
| general | (none) | 2 | Mixed |
| weather | `/api/weather` | 4 | Public |
| utility | `/`, `/health`, `/connection` | 3 | Public |