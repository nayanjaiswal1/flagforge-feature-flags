# FastAPI Integration Guide

FlagForge ships a full FastAPI integration (`flagforge.contrib.fastapi`) that provides:

- Async engine with async SQLAlchemy storage
- Lifespan context manager for startup/shutdown
- APIRouter with full CRUD + evaluation endpoints
- Dependency injection helpers
- Middleware for request-scoped caching

---

## Requirements

- Python 3.10+
- FastAPI 0.100+
- SQLAlchemy 2.0+ (asyncio)
- asyncpg (PostgreSQL async driver)

---

## Installation

```bash
pip install flagforge[fastapi]

# With Redis caching
pip install flagforge[fastapi,redis]
```

---

## Quickstart

### Minimal setup

```python
# main.py
from fastapi import FastAPI
from flagforge.contrib.fastapi import create_flagforge_lifespan
from flagforge.contrib.fastapi.router import router as flags_router

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/mydb"

app = FastAPI(
    title="My App",
    lifespan=create_flagforge_lifespan(DATABASE_URL),
)

app.include_router(flags_router, prefix="/api")
```

This automatically:

1. Creates the `feature_flag_definition` and `tenant_feature_flag` tables on startup
2. Wires `app.state.flagforge_storage` and `app.state.flagforge_engine`
3. Shuts down the connection pool cleanly on exit

---

## Lifespan Options

### Factory function (recommended)

```python
from flagforge.contrib.fastapi import create_flagforge_lifespan

app = FastAPI(
    lifespan=create_flagforge_lifespan(
        database_url="postgresql+asyncpg://user:pass@localhost/mydb",
        echo=False,   # Set True to log SQL queries
    )
)
```

### Composing with other lifespan handlers

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from flagforge.contrib.fastapi.lifespan import flagforge_lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Your own startup logic
    await some_startup_task()

    # FlagForge startup
    async with flagforge_lifespan(app, database_url=DATABASE_URL):
        yield

    # Your own shutdown logic
    await some_shutdown_task()

app = FastAPI(lifespan=lifespan)
```

---

## Evaluating Flags

### In route handlers

```python
from fastapi import Depends, Request
from flagforge.core.engine import AsyncFlagEngine
from flagforge.core.context import FeatureContext
from flagforge.contrib.fastapi.dependencies import get_engine, get_context

@app.get("/dashboard")
async def dashboard(
    engine: AsyncFlagEngine = Depends(get_engine),
    context: FeatureContext = Depends(get_context),
):
    new_ui = await engine.is_enabled("new_dashboard", context)
    return {"new_ui": new_ui}
```

### Evaluate multiple flags

```python
@app.get("/app-config")
async def app_config(
    engine: AsyncFlagEngine = Depends(get_engine),
    context: FeatureContext = Depends(get_context),
):
    flags = await engine.evaluate_many(
        ["new_dashboard", "beta_checkout", "dark_mode"],
        context
    )
    return flags
```

---

## Dependency Injection

### `feature_flag_dependency` — Guard a route

Raise `404` automatically if a flag is off:

```python
from flagforge.contrib.fastapi.dependencies import feature_flag_dependency

@app.get("/beta")
async def beta_endpoint(_=Depends(feature_flag_dependency("beta_feature"))):
    return {"message": "You're in the beta!"}
```

### `get_engine` — Access the engine

```python
from flagforge.contrib.fastapi.dependencies import get_engine

@app.get("/flags/evaluate/{key}")
async def evaluate_flag(
    key: str,
    engine: AsyncFlagEngine = Depends(get_engine),
    context: FeatureContext = Depends(get_context),
):
    return {"key": key, "enabled": await engine.is_enabled(key, context)}
```

### `get_context` — Build the current context

`get_context` calls `context_factory(request)` which reads tenant/user info from request state. Customize this for your auth setup:

```python
# flagforge_context.py — override context_factory
from fastapi import Request
from flagforge.core.context import FeatureContext

def my_context_factory(request: Request) -> FeatureContext:
    # Example: read from JWT payload attached by auth middleware
    user = getattr(request.state, "user", None)
    return FeatureContext(
        tenant_id=getattr(request.state, "tenant_id", None),
        user_id=str(user.id) if user else None,
        group_ids=getattr(request.state, "group_ids", []),
        environment="production",
    )
```

---

## REST API Endpoints

The included `router` exposes these endpoints at your chosen prefix (e.g. `/api/flags`):

### `GET /api/flags/` — Evaluate all flags

Returns resolved values for the current user/tenant.

```
GET /api/flags/
Authorization: Bearer <token>

200 OK
{
    "new_dashboard": true,
    "beta_checkout": false,
    "dark_mode": true
}
```

Anonymous requests (no tenant/user) return `{}`.

### Admin endpoints

```
GET    /api/flags/admin/                                List all definitions
POST   /api/flags/admin/                                Create a definition
PUT    /api/flags/admin/{key}/                          Update a definition
DELETE /api/flags/admin/{key}/                          Delete a definition
PUT    /api/flags/admin/{key}/tenants/{tenant_id}/      Upsert tenant override
DELETE /api/flags/admin/{key}/tenants/{tenant_id}/      Delete tenant override
```

**Create a flag:**

```
POST /api/flags/admin/
Content-Type: application/json

{
    "key": "new_dashboard",
    "name": "New Dashboard",
    "description": "Redesigned main dashboard",
    "default_enabled": false,
    "is_public": true,
    "rollout_percentage": 0,
    "environments": ["staging", "production"]
}
```

**Upsert tenant override:**

```
PUT /api/flags/admin/new_dashboard/tenants/acme_corp/
Content-Type: application/json

{
    "enabled": true,
    "rollout_percentage": null,
    "enabled_for_users": ["user_42", "user_99"],
    "enabled_for_groups": ["beta_testers"]
}
```

---

## Middleware

The FastAPI middleware handles per-request context setup:

```python
# main.py
from flagforge.contrib.fastapi.middleware import FlagForgeMiddleware

app.add_middleware(FlagForgeMiddleware)
```

---

## Redis Cache (Production)

```python
from flagforge.cache import AsyncRedisCache
from flagforge.core.engine import AsyncFlagEngine
from flagforge.contrib.fastapi.storage import AsyncSQLAlchemyStorage
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    storage = AsyncSQLAlchemyStorage(database_url=DATABASE_URL)
    await storage.init_db()

    cache = AsyncRedisCache.from_url("redis://localhost:6379/0", ttl=300)

    engine = AsyncFlagEngine(storage=storage, cache=cache)
    app.state.flagforge_storage = storage
    app.state.flagforge_engine = engine

    yield

    await storage.close()

app = FastAPI(lifespan=lifespan)
```

---

## SQLite for Development

Use SQLite with the aiosqlite driver for local development:

```bash
pip install aiosqlite
```

```python
DATABASE_URL = "sqlite+aiosqlite:///./flags.db"
app = FastAPI(lifespan=create_flagforge_lifespan(DATABASE_URL))
```

---

## Complete Example

```python
# main.py
from fastapi import FastAPI, Depends, Request
from flagforge.contrib.fastapi import create_flagforge_lifespan
from flagforge.contrib.fastapi.router import router as flags_router
from flagforge.contrib.fastapi.dependencies import get_engine, get_context, feature_flag_dependency
from flagforge.core.engine import AsyncFlagEngine
from flagforge.core.context import FeatureContext

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/mydb"

app = FastAPI(
    title="My SaaS App",
    lifespan=create_flagforge_lifespan(DATABASE_URL),
)

# Mount the flags REST API
app.include_router(flags_router, prefix="/api")


@app.get("/")
async def home(
    engine: AsyncFlagEngine = Depends(get_engine),
    context: FeatureContext = Depends(get_context),
):
    flags = await engine.evaluate_many(
        ["new_dashboard", "beta_checkout"], context
    )
    return {"flags": flags}


# This route only works when "beta_feature" is enabled for the tenant/user
@app.get("/beta")
async def beta(_=Depends(feature_flag_dependency("beta_feature"))):
    return {"message": "You're in the beta!"}
```

**Middleware example (setting tenant from header):**

```python
from starlette.middleware.base import BaseHTTPMiddleware

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.tenant_id = request.headers.get("X-Tenant-ID", "default")
        return await call_next(request)

app.add_middleware(TenantMiddleware)
```
