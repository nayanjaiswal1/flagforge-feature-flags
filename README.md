# FlagForge

**Enterprise Multi-Tenant Feature Flag Control Plane for Python**

[![PyPI version](https://badge.fury.io/py/flagforge.svg)](https://badge.fury.io/py/flagforge)
[![Python Versions](https://img.shields.io/pypi/pyversions/flagforge.svg)](https://pypi.org/project/flagforge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

FlagForge is a production-ready feature flag library for Python with first-class support for **Django** and **FastAPI**. It supports multi-tenancy, gradual rollouts, user/group targeting, environment gating, and pluggable storage/cache backends.

---

## Features

- **Multi-Tenant** — Per-tenant flag overrides; column-based or schema-based tenancy
- **Gradual Rollout** — Deterministic percentage-based bucketing via MurmurHash3
- **User & Group Targeting** — Explicitly enable flags for individual users or groups
- **Environment Gates** — Restrict flags to `staging`, `production`, etc.
- **Pluggable Storage** — Django ORM, SQLAlchemy (async), or in-memory YAML
- **Caching** — Request-scoped local cache or distributed Redis cache
- **Django Integration** — App config, migrations, REST API, admin, template tags, decorators
- **FastAPI Integration** — Async engine, lifespan setup, dependency injection
- **REST API** — Expose flags to frontends (React, Vue, mobile) via HTTP
- **CLI** — `flagforge sync / status / enable / disable`
- **Type-safe** — Full type hints and `py.typed` marker

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Django Integration](#django-integration)
- [FastAPI Integration](#fastapi-integration)
- [React / Frontend Integration](#react--frontend-integration)
- [Flag Configuration](#flag-configuration)
- [Caching](#caching)
- [CLI Reference](#cli-reference)
- [API Reference](#api-reference)
- [Contributing](#contributing)

---

## Installation

```bash
# Core library only
pip install flagforge

# Django support (adds Django ORM storage + DRF REST API)
pip install flagforge[django]

# FastAPI support (adds async SQLAlchemy storage)
pip install flagforge[fastapi]

# Redis cache backend
pip install flagforge[redis]

# Everything
pip install flagforge[all]
```

---

## Quick Start

```python
from flagforge import FlagEngine, FeatureContext
from flagforge.storage.memory import InMemoryStorage
from flagforge.cache import LocalCache
from flagforge.core.models import FlagDefinition

# 1. Create storage and engine
storage = InMemoryStorage()
engine = FlagEngine(storage=storage, cache=LocalCache())

# 2. Define a flag
storage.upsert_definition(FlagDefinition(
    key="new_dashboard",
    name="New Dashboard",
    default_enabled=False,
))

# 3. Evaluate
context = FeatureContext(tenant_id="acme", user_id="user_42")
if engine.is_enabled("new_dashboard", context):
    print("Show new dashboard")
```

### Async (FastAPI / asyncio)

```python
from flagforge import AsyncFlagEngine, FeatureContext
from flagforge.storage.memory import AsyncInMemoryStorage
from flagforge.cache import AsyncLocalCache

engine = AsyncFlagEngine(storage=AsyncInMemoryStorage(), cache=AsyncLocalCache())

ctx = FeatureContext(tenant_id="acme", user_id="user_42")
enabled = await engine.is_enabled("new_dashboard", ctx)
```

### Global Engine Pattern

```python
import flagforge
from flagforge.storage.memory import InMemoryStorage

flagforge.configure_engine(flagforge.FlagEngine(storage=InMemoryStorage()))

# Anywhere in your app:
enabled = flagforge.is_enabled("my_flag", context)
```

---

## Django Integration

See the **[Django Guide](docs/django.md)** for the full walkthrough.

### 1. Install & add to `INSTALLED_APPS`

```bash
pip install flagforge[django]
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    "flagforge.contrib.django",
]

MIDDLEWARE = [
    ...
    "flagforge.contrib.django.middleware.RequestCacheMiddleware",
]
```

### 2. Run migrations

```bash
python manage.py migrate
```

### 3. Include the REST API (optional)

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    ...
    path("api/flags/", include("flagforge.contrib.django.urls")),
]
```

### 4. Use in views

```python
from flagforge.contrib.django.engine import flag_enabled

def my_view(request):
    if flag_enabled("new_checkout", request):
        return render(request, "checkout_v2.html")
    return render(request, "checkout.html")
```

### 5. Use the decorator

```python
from flagforge.contrib.django.decorators import flag_required

@flag_required("beta_dashboard", redirect_to="/")
def beta_view(request):
    ...
```

### 6. Template tags

```django
{% load flagforge %}

{% flag "new_dashboard" request %}
  <p>New dashboard is active!</p>
{% endflag %}
```

### 7. Sync flags from YAML

```bash
python manage.py sync_feature_flags --config config/feature-flags.yaml
```

---

## FastAPI Integration

See the **[FastAPI Guide](docs/fastapi.md)** for the full walkthrough.

```python
from fastapi import FastAPI
from flagforge.contrib.fastapi import create_flagforge_lifespan
from flagforge.contrib.fastapi.router import router as flags_router

app = FastAPI(
    lifespan=create_flagforge_lifespan(
        database_url="postgresql+asyncpg://user:pass@localhost/mydb"
    )
)
app.include_router(flags_router, prefix="/api")
```

### Dependency injection

```python
from fastapi import Depends
from flagforge.contrib.fastapi.dependencies import feature_flag_dependency

@app.get("/new-feature")
async def new_feature(_=Depends(feature_flag_dependency("new_feature"))):
    return {"message": "New feature!"}
```

---

## React / Frontend Integration

See the **[React Guide](docs/react.md)** for components, hooks, and usage patterns.

FlagForge exposes a REST endpoint (`GET /api/flags/`) that returns all resolved flag values for the current user. Your frontend can fetch these once and use them throughout the app.

```
GET /api/flags/
Authorization: Bearer <token>

{
  "new_dashboard": true,
  "beta_checkout": false,
  "dark_mode": true
}
```

**Quick React example:**

```tsx
import { useFlags } from "./hooks/useFlags";

function App() {
  const { flags, loading } = useFlags("/api/flags/");

  if (loading) return <Spinner />;

  return flags.new_dashboard ? <NewDashboard /> : <OldDashboard />;
}
```

---

## Flag Configuration

### YAML file (`config/feature-flags.yaml`)

```yaml
flags:
  new_dashboard:
    name: New Dashboard
    description: Redesigned dashboard UI
    default_enabled: false
    is_public: true
    rollout_percentage: 0
    environments:
      - staging
      - production

  beta_checkout:
    name: Beta Checkout Flow
    description: New one-page checkout
    default_enabled: false
    is_public: false
    rollout_percentage: 20   # 20% gradual rollout

  dark_mode:
    name: Dark Mode
    description: Dark theme for all users
    default_enabled: true
    is_public: true
```

### Flag fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `key` | string | — | Unique identifier |
| `name` | string | — | Human-readable name |
| `description` | string | `""` | Optional description |
| `default_enabled` | bool | `false` | Default state |
| `is_public` | bool | `false` | Exposed to unauthenticated users |
| `rollout_percentage` | int 0–100 | `0` | Gradual rollout percentage |
| `deprecated` | bool | `false` | Mark as deprecated |
| `environments` | list[str] | `null` | Restrict to environments |

### Resolution Priority

1. **Environment gate** — if `environments` set and current env not in list → `False`
2. **User targeting** — if user is in tenant override's `enabled_for_users` → `True`
3. **Group targeting** — if user's group is in `enabled_for_groups` → `True`
4. **Tenant override** — explicit `enabled: true/false` on tenant
5. **Default + rollout** — `default_enabled` with optional `rollout_percentage`

---

## Caching

| Backend | Class | Use Case |
|---------|-------|----------|
| Local (in-memory) | `LocalCache` / `AsyncLocalCache` | Single-process, request-scoped |
| Redis | `RedisCache` / `AsyncRedisCache` | Multi-process, distributed |
| Null | `NullCache` / `AsyncNullCache` | Testing / disable caching |

### Redis cache

```python
from flagforge.cache import RedisCache

cache = RedisCache(host="localhost", port=6379, db=0, ttl=300)
engine = FlagEngine(storage=storage, cache=cache)
```

---

## CLI Reference

```bash
# Sync flag definitions from YAML to database
flagforge sync --config config/feature-flags.yaml

# Show flag status for a tenant
flagforge status --tenant acme_corp

# Enable a flag for a tenant
flagforge enable --flag new_dashboard --tenant acme_corp

# Disable a flag for a tenant
flagforge disable --flag new_dashboard --tenant acme_corp
```

### Django management commands

```bash
python manage.py sync_feature_flags --config config/feature-flags.yaml
python manage.py show_flag_status --tenant acme_corp
python manage.py enable_flag_for_tenant --flag new_dashboard --tenant acme_corp
python manage.py disable_flag_for_tenant --flag new_dashboard --tenant acme_corp
```

---

## API Reference

### `FlagEngine`

```python
engine = FlagEngine(storage, cache=None)

engine.is_enabled(key: str, context: FeatureContext) -> bool
engine.evaluate_many(keys: list[str], context: FeatureContext) -> dict[str, bool]
engine.evaluate_all(context: FeatureContext) -> dict[str, bool]
```

### `AsyncFlagEngine`

Same interface but all methods are `async`.

### `FeatureContext`

```python
FeatureContext(
    tenant_id: str,          # Required — tenant identifier
    user_id: str | None,     # Optional — user identifier
    group_ids: list[str],    # Optional — user's groups
    environment: str | None, # Optional — e.g. "production"
    attributes: dict,        # Optional — custom attributes
)
```

### REST Endpoints (Django & FastAPI)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/flags/` | Optional | Get all resolved flags for current user |
| `GET` | `/api/flags/admin/` | Admin | List all flag definitions |
| `POST` | `/api/flags/admin/` | Admin | Create flag definition |
| `PUT` | `/api/flags/admin/{key}/` | Admin | Update flag definition |
| `DELETE` | `/api/flags/admin/{key}/` | Admin | Delete flag definition |
| `PUT` | `/api/flags/admin/{key}/tenants/{tenant_id}/` | Admin | Upsert tenant override |
| `DELETE` | `/api/flags/admin/{key}/tenants/{tenant_id}/` | Admin | Delete tenant override |

---

## Contributing

```bash
# Clone and set up
git clone https://github.com/flagforge/flagforge
cd flagforge
python -m venv venv && source venv/bin/activate
pip install -e ".[dev,django,fastapi,redis]"

# Run tests
pytest

# Lint
ruff check src/
mypy src/
```

Pull requests are welcome. Please open an issue first to discuss major changes.

---

## License

MIT — see [LICENSE](LICENSE)
