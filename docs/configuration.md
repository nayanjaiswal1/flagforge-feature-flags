# Configuration Reference

---

## Flag Definition Fields

```yaml
# config/feature-flags.yaml
flags:
  my_feature:
    name: My Feature           # Human-readable name (required)
    description: |             # Optional description
      Enables the redesigned
      feature for eligible users.
    default_enabled: false     # Default state when no override applies
    is_public: false           # Include in unauthenticated /api/flags/ response
    rollout_percentage: 0      # 0 = full on/off, 1-100 = gradual rollout
    deprecated: false          # Mark as deprecated (still evaluated)
    environments:              # Restrict to these environments (null = all)
      - staging
      - production
```

### `rollout_percentage`

When `default_enabled: true` and `rollout_percentage > 0`, the flag is enabled for exactly that percentage of users via deterministic MurmurHash3 bucketing on `(tenant_id, flag_key, user_id)`.

The same user always gets the same result. Increasing the percentage gradually includes more users.

When `rollout_percentage: 0` and `default_enabled: true`, the flag is on for **everyone** in the tenant.

---

## Tenant Override Fields

Overrides are stored in the database (Django ORM or SQLAlchemy) and applied per-tenant.

| Field | Type | Description |
|-------|------|-------------|
| `key` | string | Flag key this override applies to |
| `tenant_id` | string | Tenant identifier |
| `enabled` | bool \| null | Override state (null = use definition default) |
| `rollout_percentage` | int \| null | Override rollout (null = use definition default) |
| `enabled_for_users` | list[str] | User IDs explicitly enabled |
| `enabled_for_groups` | list[str] | Group IDs explicitly enabled |
| `updated_by` | string \| null | Audit: who made the change |

---

## Resolution Priority Chain

1. **Environment gate** — If `environments` is set and the context's `environment` is not in the list → `False`
2. **User targeting** — If override exists and `context.user_id` is in `override.enabled_for_users` → `True`
3. **Group targeting** — If override exists and any of `context.group_ids` intersects `override.enabled_for_groups` → `True`
4. **Override state** — If `override.enabled` is not `None` → use that value (with optional rollout)
5. **Definition default** — `definition.default_enabled` (with optional rollout)

---

## FeatureContext Fields

```python
FeatureContext(
    tenant_id="acme",              # Required — identifies the tenant
    user_id="user_42",             # Optional — enables user targeting + rollout
    group_ids=["beta_testers"],    # Optional — enables group targeting
    environment="production",      # Optional — required for environment gating
    attributes={},                 # Optional — reserved for custom targeting (future)
)
```

---

## Cache Backends

### `LocalCache` / `AsyncLocalCache`

In-process memory cache, cleared each request (when using `RequestCacheMiddleware` or `FlagForgeMiddleware`). Best for single-process deployments.

```python
from flagforge.cache import LocalCache
cache = LocalCache()
```

### `RedisCache` / `AsyncRedisCache`

Distributed cache for multi-process/multi-instance deployments.

```python
from flagforge.cache import RedisCache

# From constructor
cache = RedisCache(host="localhost", port=6379, db=0, ttl=300)

# From URL
cache = RedisCache.from_url("redis://localhost:6379/0", ttl=300)

# Async
from flagforge.cache import AsyncRedisCache
cache = AsyncRedisCache.from_url("redis://localhost:6379/0", ttl=300)
```

Default TTL is `300` seconds (5 minutes).

### `NullCache` / `AsyncNullCache`

Disables caching. Every evaluation hits storage. Useful for testing.

```python
from flagforge.cache import NullCache
cache = NullCache()
```

---

## Storage Backends

### `InMemoryStorage` / `AsyncInMemoryStorage`

Stores definitions and overrides in a Python dict. Not persistent. Best for tests and development.

```python
from flagforge.storage.memory import InMemoryStorage
storage = InMemoryStorage()
```

### `DjangoStorageAdapter`

Uses Django ORM models. Requires `flagforge.contrib.django` in `INSTALLED_APPS` and migrations applied.

```python
from flagforge.contrib.django.storage import DjangoStorageAdapter
storage = DjangoStorageAdapter()
```

### `AsyncSQLAlchemyStorage`

Async SQLAlchemy 2.0 storage. Supports PostgreSQL (`asyncpg`) and SQLite (`aiosqlite`).

```python
from flagforge.contrib.fastapi.storage import AsyncSQLAlchemyStorage

storage = AsyncSQLAlchemyStorage(
    database_url="postgresql+asyncpg://user:pass@localhost/mydb  # pragma: allowlist secret",
    echo=False,   # Log SQL queries
)
await storage.init_db()   # Creates tables if they don't exist
```

### YAML Loader

Load flags from a YAML file into any storage backend.

```python
from flagforge.storage.yaml_loader import sync_from_yaml, load_flags
from pathlib import Path

# Load as list of FlagDefinition objects
flags = load_flags("config/feature-flags.yaml")

# Sync into storage (upserts, optionally deletes removed flags)
sync_from_yaml(storage, Path("config/feature-flags.yaml"), remove_deprecated=False)
```

---

## Engine API

### `FlagEngine` (sync)

```python
from flagforge import FlagEngine

engine = FlagEngine(storage=storage, cache=cache)

# Single flag
enabled: bool = engine.is_enabled("my_flag", context)

# Multiple flags
results: dict[str, bool] = engine.evaluate_many(["flag_a", "flag_b"], context)

# All flags for tenant
all_flags: dict[str, bool] = engine.evaluate_all(context)
```

### `AsyncFlagEngine` (async)

```python
from flagforge import AsyncFlagEngine

engine = AsyncFlagEngine(storage=storage, cache=cache)

enabled = await engine.is_enabled("my_flag", context)
results = await engine.evaluate_many(["flag_a", "flag_b"], context)
all_flags = await engine.evaluate_all(context)
```

### Global engine pattern

```python
import flagforge

# Configure once at app startup
flagforge.configure_engine(flagforge.FlagEngine(storage=storage))

# Use anywhere
enabled = flagforge.is_enabled("my_flag", context)
```

---

## Environment Variables

FlagForge itself has no required environment variables. Recommended patterns:

```bash
# FastAPI — database URL
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/mydb  # pragma: allowlist secret

# Redis cache
REDIS_URL=redis://localhost:6379/0

# Environment name (used in FeatureContext)
APP_ENV=production
```

---

## Django Settings Reference

All `FLAGFORGE_*` settings are optional. Defaults shown below.

### Tenancy

| Setting | Default | Description |
|---------|---------|-------------|
| `FLAGFORGE_TENANCY_MODE` | `"column"` | `"column"`, `"schema"`, or `"hybrid"` |
| `FLAGFORGE_DEFAULT_TENANT_ID` | `"default"` | Fallback tenant ID when none resolved from request |
| `FLAGFORGE_ENVIRONMENT` | `"production"` | Current environment name for environment gating |

### Cache

| Setting | Default | Description |
|---------|---------|-------------|
| `FLAGFORGE_CACHE_BACKEND` | `"local"` | `"local"`, `"redis"`, `"none"`, or dotted path to a `CacheBackend` subclass |
| `FLAGFORGE_CACHE_TTL` | `300` | Cache TTL in seconds for resolved flag values |
| `FLAGFORGE_REDIS_URL` | `None` | Redis connection URL (used when `CACHE_BACKEND="redis"`) |
| `FLAGFORGE_REDIS_HOST` | `"localhost"` | Redis host (used when `CACHE_BACKEND="redis"` and no URL set) |
| `FLAGFORGE_REDIS_PORT` | `6379` | Redis port |
| `FLAGFORGE_REDIS_DB` | `0` | Redis database number |
| `FLAGFORGE_REDIS_PASSWORD` | `None` | Redis password |

### Resolver hooks

| Setting | Default | Description |
|---------|---------|-------------|
| `FLAGFORGE_TENANT_RESOLVER` | `None` | Dotted path to `callable(request) -> str \| None` |
| `FLAGFORGE_USER_RESOLVER` | `None` | Dotted path to `callable(request) -> tuple[str \| None, list[str]]` |

When `FLAGFORGE_TENANT_RESOLVER` is not set, FlagForge checks `request.tenant_id`, then `request.tenant.schema_name` (django-tenants), then falls back to `FLAGFORGE_DEFAULT_TENANT_ID`.

When `FLAGFORGE_USER_RESOLVER` is not set, FlagForge uses Django's built-in `request.user` and `request.user.groups`.

**Example resolver:**

```python
# myapp/resolvers.py
def get_tenant_id(request):
    # Read tenant from JWT, header, subdomain, etc.
    return request.headers.get("X-Tenant-ID")

def get_user_info(request):
    if request.user.is_authenticated:
        return str(request.user.id), list(request.user.roles.values_list("name", flat=True))
    return None, []
```

```python
# settings.py
FLAGFORGE_TENANT_RESOLVER = "myapp.resolvers.get_tenant_id"
FLAGFORGE_USER_RESOLVER = "myapp.resolvers.get_user_info"
```

### Permissions

| Setting | Default | Description |
|---------|---------|-------------|
| `FLAGFORGE_ADMIN_PERMISSION` | `"rest_framework.permissions.IsAdminUser"` | Dotted path to DRF permission class for admin endpoints |

```python
# settings.py — use a custom permission class
FLAGFORGE_ADMIN_PERMISSION = "myapp.permissions.IsPlatformStaff"
```

### System checks

Run `python manage.py check` to validate all settings. FlagForge registers checks for:

| Check ID | What it validates |
|----------|------------------|
| `flagforge.E001` | `FLAGFORGE_TENANCY_MODE` is `column`, `schema`, or `hybrid` |
| `flagforge.E002` | `FLAGFORGE_CACHE_BACKEND` is valid or importable |
| `flagforge.E003` | Redis host/URL is set when `CACHE_BACKEND="redis"` |
| `flagforge.E004` | `FLAGFORGE_TENANT_RESOLVER` is importable |
| `flagforge.E005` | `FLAGFORGE_USER_RESOLVER` is importable |
| `flagforge.E006` | `FLAGFORGE_ADMIN_PERMISSION` is importable |
| `flagforge.E007` | `FLAGFORGE_CACHE_TTL` is a positive integer |
