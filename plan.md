# FlagForge — Project Plan

> Enterprise Multi-Tenant Feature Flag Control Plane for Python
> Version: 1.0.0 | License: MIT | Target: PyPI
> Last updated: 2026-02-27 (rev 6)

---

## Overview

FlagForge is a self-hosted, framework-agnostic feature flag engine comparable to LaunchDarkly and Unleash, optimized for multi-tenant SaaS. It provides centralized flag definitions, sparse tenant overrides, user/group targeting, deterministic rollouts, multi-tier caching, YAML governance, and Django + FastAPI integrations.

**Key user decisions:**
- Django DB: PostgreSQL (`ArrayField` for user/group targeting)
- Multi-tenancy: Both `tenant_id` column and schema-per-tenant supported
- CLI: Click

---

## Directory Structure

```
flagforge/                              ← repo root (no spaces in directory name)
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── LICENSE                             MIT
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── .gitignore
├── .python-version                     3.12
├── plan.md                             ← this file
│
├── config/
│   └── feature-flags.yaml             governance source of truth
│
├── src/
│   └── flagforge/
│       ├── __init__.py                re-exports: FlagEngine, AsyncFlagEngine, FeatureContext, is_enabled, evaluate_many, request_context, async_request_context
│       ├── py.typed                   PEP 561 marker (ship with package for downstream mypy)
│       │
│       ├── core/
│       │   ├── context.py             FeatureContext dataclass + request_context() ctx manager
│       │   ├── engine.py              FlagEngine (sync) + AsyncFlagEngine (async) — main public API
│       │   ├── resolver.py            Resolution order logic (pure functions)
│       │   ├── hasher.py              Deterministic rollout hashing (MurmurHash3)
│       │   ├── models.py              FlagDefinition, TenantOverride (plain dataclasses, no ORM)
│       │   └── exceptions.py          FlagForgeError, StorageError, CacheError
│       │
│       ├── storage/
│       │   ├── base.py                StorageBackend ABC + AsyncStorageBackend ABC
│       │   ├── memory.py              InMemoryStorage (sync) + AsyncInMemoryStorage (async, for testing AsyncFlagEngine)
│       │   └── yaml_loader.py         Loads feature-flags.yaml → FlagDefinition list
│       │
│       ├── cache/
│       │   ├── base.py                CacheBackend ABC + AsyncCacheBackend ABC
│       │   ├── null.py                NullCache + AsyncNullCache (no-op, for testing)
│       │   ├── local.py               LocalCache (thread-local + contextvars, request-level)
│       │   ├── redis_cache.py         RedisCache (sync, cross-request, redis-py)
│       │   ├── async_redis_cache.py   AsyncRedisCache (async, redis.asyncio)
│       │   └── keys.py                Cache key builders (smart: omits user_id when unnecessary)
│       │
│       ├── contrib/
│       │   ├── django/
│       │   │   ├── apps.py            FlagForgeDjangoConfig (AppConfig)
│       │   │   ├── models.py          FeatureFlagDefinition, TenantFeatureFlag (ORM)
│       │   │   ├── migrations/        shipped migrations (created via makemigrations flagforge)
│       │   │   │   └── 0001_initial.py
│       │   │   ├── storage.py         DjangoStorage (implements StorageBackend)
│       │   │   ├── admin.py           PublicFlagAdmin, TenantFlagAdmin
│       │   │   ├── signals.py         post_save/post_delete → cache invalidation
│       │   │   ├── middleware.py      RequestCacheMiddleware (wipe thread-local per request)
│       │   │   ├── decorators.py      @flag_required("flag_name")
│       │   │   ├── serializers.py     DRF serializers
│       │   │   ├── views.py           FlagListView, AdminFlagListView, AdminFlagCRUDView
│       │   │   ├── urls.py            /api/feature-flags/ routes
│       │   │   ├── checks.py          Django system checks
│       │   │   └── management/commands/
│       │   │       ├── sync_feature_flags.py
│       │   │       ├── show_flag_status.py
│       │   │       ├── enable_flag_for_tenant.py
│       │   │       └── disable_flag_for_tenant.py
│       │   │
│       │   └── fastapi/
│       │       ├── models.py          SQLAlchemy ORM models (DeclarativeBase, 2.0 style)
│       │       ├── storage.py         AsyncSQLAlchemyStorage (implements AsyncStorageBackend)
│       │       ├── dependencies.py    feature_dependency("flag_name") factory
│       │       ├── context.py         context_factory: Callable[[Request], FeatureContext]
│       │       ├── middleware.py      Starlette middleware (populates FeatureContext via context_factory)
│       │       ├── lifespan.py        Lifespan handler — validates storage connectivity + settings on startup
│       │       └── router.py          APIRouter with /flags/, /admin/flags/, and CRUD routes
│       │
│       └── cli/
│           └── main.py                Click group: sync, status, enable, disable, clear-cache
│
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_resolver.py           Resolution order, all 5 priority levels, None override handling
    │   ├── test_hasher.py             Rollout determinism, boundary cases, percentage=100 shortcut, None user_id bucketing
    │   ├── test_engine.py             FlagEngine (sync, InMemoryStorage) + evaluate_many missing-key behavior
    │   ├── test_async_engine.py       AsyncFlagEngine (AsyncInMemoryStorage) + async evaluate_many
    │   └── test_yaml_loader.py
    ├── integration/
    │   ├── django/
    │   │   ├── test_models.py
    │   │   ├── test_storage.py        Tenant isolation enforcement
    │   │   ├── test_views.py          API auth behavior + CRUD endpoints
    │   │   ├── test_management.py     sync_feature_flags idempotency
    │   │   └── test_decorators.py     @flag_required behavior (enabled, disabled, missing flag)
    │   └── fastapi/
    │       ├── test_dependencies.py
    │       ├── test_router.py
    │       └── test_lifespan.py       Startup check raises on bad config / unreachable storage
    └── performance/
        └── test_throughput.py         ≥10k evaluations/sec benchmark
```

---

## Core Interfaces

### `FeatureContext` (`core/context.py`)
```python
@dataclass
class FeatureContext:
    tenant_id: str | None = None
    user_id: str | None = None
    group_ids: list[str] = field(default_factory=list)
    environment: str | None = None       # e.g. "production", "staging", "development"
    # Escape hatch for custom targeting dimensions (plan_tier, country, beta_opt_in, …)
    # Avoids a library version bump for every new targeting attribute.
    attributes: dict[str, Any] = field(default_factory=dict)
```

### Core Models (`core/models.py`)
All core dataclasses include timestamps for cache freshness and audit:
```python
@dataclass
class FlagDefinition:
    key: str
    name: str
    description: str = ""
    default_enabled: bool = False
    is_public: bool = False
    rollout_percentage: int = 0
    deprecated: bool = False              # governance marker for sync --remove-deprecated
    environments: list[str] | None = None # if set, flag is only active in these environments
    created_at: datetime | None = None
    updated_at: datetime | None = None

@dataclass
class TenantOverride:
    key: str
    tenant_id: str
    enabled: bool | None = None
    rollout_percentage: int | None = None  # 0–100; validated at API layer (same range as FlagDefinition)
    enabled_for_users: list[str] = field(default_factory=list)
    enabled_for_groups: list[str] = field(default_factory=list)
    updated_at: datetime | None = None
    updated_by: str | None = None         # user/actor who last changed this override
```

### `FlagEngine` public API (`core/engine.py`)

Two concrete classes are provided — one sync, one async — sharing a common base. There is no union-typed single class, as that would require sync methods to `await` async storage.

```python
class FlagEngine:
    """Sync engine. Accepts StorageBackend + CacheBackend."""
    def __init__(self, storage: StorageBackend, cache: CacheBackend = NullCache()):
        ...

    def is_enabled(self, key: str, context: FeatureContext) -> bool:
        """Evaluate a single flag."""
        ...

    def evaluate_many(self, keys: list[str], context: FeatureContext) -> dict[str, bool]:
        """Bulk evaluate multiple flags in a single storage round-trip.
        Uses get_all_definitions + get_all_tenant_overrides internally.
        Keys not found in storage are returned as False (not omitted, not raised)."""
        ...

    def evaluate_all(self, context: FeatureContext) -> dict[str, bool]:
        """Evaluate every defined flag. Convenience wrapper around evaluate_many."""
        ...


class AsyncFlagEngine:
    """Async engine. Accepts AsyncStorageBackend + AsyncCacheBackend. Use with FastAPI / asyncio."""
    def __init__(self, storage: AsyncStorageBackend, cache: AsyncCacheBackend = AsyncNullCache()):
        ...

    async def is_enabled(self, key: str, context: FeatureContext) -> bool: ...
    async def evaluate_many(self, keys: list[str], context: FeatureContext) -> dict[str, bool]:
        """Keys not found in storage are returned as False (not omitted, not raised)."""
        ...
    async def evaluate_all(self, context: FeatureContext) -> dict[str, bool]: ...
```

`__init__.py` re-exports: `FlagEngine`, `AsyncFlagEngine`, `FeatureContext`, `is_enabled`, `evaluate_many`, `request_context`, `async_request_context`.

### `StorageBackend` ABC (`storage/base.py`)
```python
class StorageBackend(ABC):
    def get_definition(self, key: str) -> FlagDefinition | None: ...
    def get_all_definitions(self) -> list[FlagDefinition]: ...
    def get_tenant_override(self, key: str, tenant_id: str) -> TenantOverride | None: ...
    def get_all_tenant_overrides(self, tenant_id: str) -> list[TenantOverride]: ...
    def upsert_definition(self, defn: FlagDefinition) -> None: ...
    def upsert_tenant_override(self, override: TenantOverride) -> None: ...
    def delete_tenant_override(self, key: str, tenant_id: str) -> None: ...
    # Contract: cascades and deletes all associated TenantOverrides for this key.
    def delete_definition(self, key: str) -> None: ...

class AsyncStorageBackend(ABC):
    """Async variant for use with FastAPI / asyncio frameworks."""
    async def get_definition(self, key: str) -> FlagDefinition | None: ...
    async def get_all_definitions(self) -> list[FlagDefinition]: ...
    async def get_tenant_override(self, key: str, tenant_id: str) -> TenantOverride | None: ...
    async def get_all_tenant_overrides(self, tenant_id: str) -> list[TenantOverride]: ...
    async def upsert_definition(self, defn: FlagDefinition) -> None: ...
    async def upsert_tenant_override(self, override: TenantOverride) -> None: ...
    async def delete_tenant_override(self, key: str, tenant_id: str) -> None: ...
    async def delete_definition(self, key: str) -> None: ...
```

`DjangoStorage` implements `StorageBackend` (sync) and is used with `FlagEngine`. `AsyncSQLAlchemyStorage` implements `AsyncStorageBackend` and is used with `AsyncFlagEngine`.

### `CacheBackend` ABC + `AsyncCacheBackend` ABC (`cache/base.py`)
```python
class CacheBackend(ABC):
    # Tristate contract: None = cache miss (not cached), False = cached as "disabled",
    # True = cached as "enabled". Callers MUST treat None and False as distinct.
    def get(self, key: str) -> bool | None: ...
    def set(self, key: str, value: bool, ttl: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def delete_for_flag(self, flag_key: str) -> None: ...        # invalidate all cache entries for a flag
    def delete_for_tenant(self, tenant_id: str) -> None: ...     # invalidate all cache entries for a tenant
    def clear_request_cache(self) -> None: ...

class AsyncCacheBackend(ABC):
    """Async variant for FastAPI / asyncio — uses redis.asyncio under the hood."""
    async def get(self, key: str) -> bool | None: ...
    async def set(self, key: str, value: bool, ttl: int | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def delete_for_flag(self, flag_key: str) -> None: ...
    async def delete_for_tenant(self, tenant_id: str) -> None: ...
    async def clear_request_cache(self) -> None: ...
```

---

## Resolution Order (`core/resolver.py`)

```
resolve(key, context, definition, override) → bool:
  # override is TenantOverride | None. If None, steps 1–3 are skipped entirely.
  0. definition.environments is set and context.environment ∉ definition.environments → False
  1. override is not None and override.enabled_for_users contains context.user_id  → True   # tenant-scoped user list
  2. override is not None and override.enabled_for_groups ∩ context.group_ids      → True   # tenant-scoped group list
  3. override is not None and override.enabled is not None                         → apply rollout if set, using override.rollout_percentage if present, else definition.rollout_percentage
  4. definition.default_enabled                                                    → apply rollout using definition.rollout_percentage
  5. fallback                                                                      → False
```

**Scoping note**: Step 0 is an environment gate — if a flag declares specific environments, it is hard-disabled outside them. Steps 1–3 operate on the `TenantOverride` for `(key, tenant_id)` and are skipped entirely when no override exists. Steps 4–5 use the global `FlagDefinition`. User/group targeting is always tenant-scoped; there is no global user/group list on `FlagDefinition`.

**Rollout precedence**: `override.rollout_percentage` (when set) replaces `definition.rollout_percentage` — it does not multiply. This lets a tenant opt into a higher or lower rollout than the global default without interaction effects.

**Rollout hashing** (`core/hasher.py`):
```python
# MurmurHash3 — ~10x faster than SHA-256 for non-cryptographic bucketing.
# Peppered with tenant_id to prevent cross-tenant collisions.
# Shortcut: if percentage >= 100 → return True immediately (skip hashing).
# Shortcut: if percentage <= 0  → return False immediately.
# user_id may be None (anonymous). When None, the bucket is deterministic per
# (tenant_id, key) — all anonymous users within a tenant hash identically,
# giving a consistent on/off per tenant rather than per-user. This is intentional.
mmh3.hash(f"{tenant_id}:{key}:{user_id}", signed=False) % 100 < percentage
```

---

## Caching Strategy

| Layer | Backend | Key Format | TTL | Notes |
|-------|---------|------------|-----|-------|
| Request-level | `LocalCache` (thread-local / contextvars) | `(tenant_id, user_id, feature_key)` | request lifetime | |
| Cross-request (resolved) | `RedisCache` / `AsyncRedisCache` | `ff:resolved:{tenant_id}:{feature_key}` | 300s | Used when flag has no user/group targeting |
| Cross-request (user-targeted) | `RedisCache` / `AsyncRedisCache` | `ff:user:{tenant_id}:{user_id}:{feature_key}` | 300s | Used only when override has user/group lists |
| Definitions | `RedisCache` / `AsyncRedisCache` | `ff:def:{feature_key}` | 3600s | |

Lookup chain: local → Redis → storage (write-back on miss). Invalidated on any save/delete signal.

**Smart cache key selection**: `keys.py` inspects the `TenantOverride` for the flag. If `enabled_for_users` and `enabled_for_groups` are both empty, the resolved key (`ff:resolved:…`) is used — this avoids creating per-user Redis entries for flags that don't need user-level targeting. When user/group targeting is active, the user-targeted key (`ff:user:…`) is used.

**Background Tasks Note**: `LocalCache` is request-scoped via middleware. For Celery, RQ, or any background task runner (including FastAPI `BackgroundTasks`), use the provided context manager:
```python
# Sync (Celery / RQ / Django management commands)
with flagforge.request_context():
    is_on = engine.is_enabled("my_flag", ctx)

# Async (FastAPI BackgroundTasks / asyncio jobs)
async with flagforge.async_request_context():
    is_on = await engine.is_enabled("my_flag", ctx)
```
This ensures the `LocalCache` is cleanly initialized and flushed before and after job execution. FastAPI `BackgroundTasks` run *after* the response and outside middleware scope, so this context manager is required to prevent stale reads.

---

## Multi-Tenancy Modes (Django)

Controlled by `FLAGFORGE_TENANCY_MODE` setting:

- **`"column"`** (default): `TenantFeatureFlag.tenant_id` on shared table. `DjangoStorage` filters every query by `tenant_id`.
- **`"schema"`**: `DjangoStorage` calls `connection.set_schema(tenant_id)` (compatible with django-tenants). `FeatureFlagDefinition` lives in public/shared schema.

**Async note**: `DjangoStorage` uses synchronous ORM calls. For async Django (ASGI/Channels), wrap with `sync_to_async`. The FastAPI integration uses `AsyncSQLAlchemyStorage` with native `AsyncSession`.

---

## API Endpoints

| Method | Path | Auth | Behavior |
|--------|------|------|----------|
| GET | `/api/feature-flags/flags/` | Optional | Authenticated → all resolved flags; Unauthenticated → `is_public=True` only |
| GET | `/api/feature-flags/admin/flags/` | Staff required | Raw definitions + tenant overrides (no merge) |
| POST | `/api/feature-flags/admin/flags/` | Staff required | Create a new flag definition |
| PUT | `/api/feature-flags/admin/flags/{key}/` | Staff required | Update a flag definition |
| DELETE | `/api/feature-flags/admin/flags/{key}/` | Staff required | Delete a flag definition (cascades tenant overrides) |
| PUT | `/api/feature-flags/admin/flags/{key}/tenants/{tenant_id}/` | Staff required | Upsert a tenant override |
| DELETE | `/api/feature-flags/admin/flags/{key}/tenants/{tenant_id}/` | Staff required | Delete a tenant override |

**Governance note**: Flag *definitions* are intended to be managed primarily via YAML sync in CI/CD. The admin CRUD endpoints above are provided for operational convenience (e.g., emergency toggles) but `flagforge sync` will overwrite definition fields on the next run. Tenant overrides are API-only and are never touched by sync.

---

## CLI Commands

```
# For Django, these are also exposed as management commands.
# --app accepts a Python dotted path to a module that exposes a `get_engine()` factory
# (e.g. "myproject.flags:get_engine"). Django auto-detects via DJANGO_SETTINGS_MODULE.
flagforge sync     --config PATH [--dry-run] [--remove-deprecated] [--app DOTTED_PATH]
flagforge status   --tenant TENANT_ID [--flag KEY] [--app DOTTED_PATH]
flagforge enable   --flag KEY --tenant TENANT_ID [--app DOTTED_PATH]
flagforge disable  --flag KEY --tenant TENANT_ID [--app DOTTED_PATH]
flagforge cache clear [--tenant TENANT_ID] [--flag KEY] [--app DOTTED_PATH]
```

**`--app` resolution**: If `DJANGO_SETTINGS_MODULE` is set, the CLI calls `django.setup()` and resolves the engine via the app's `FlagForgeDjangoConfig`. Otherwise, `--app` must be a dotted path to a module exposing a `get_engine() -> FlagEngine` factory (e.g. `"myproject.flags:get_engine"`). The CLI imports the module and calls `get_engine()`. If neither is available, the command exits with a descriptive error.

---

## `pyproject.toml` Dependencies

```toml
[project]
dependencies = [
    "mmh3>=4.0",       # core: rollout hashing (non-optional, used by resolver)
    "pydantic>=2.0",   # core: YAML schema validation in yaml_loader
]

[project.optional-dependencies]
django     = ["django>=4.2", "djangorestframework>=3.14", "psycopg>=3.1"]
# Note: django-tenants is NOT listed as a dep — schema mode calls connection.set_schema()
# which is compatible with django-tenants but does not require it. Users must install
# django-tenants separately if they use schema-per-tenant routing beyond FlagForge.
fastapi    = ["fastapi>=0.100", "sqlalchemy[asyncio]>=2.0"]
redis      = ["redis>=5.0"]
# Note: no standalone sqlalchemy extra — fastapi already pulls sqlalchemy[asyncio].
# Users needing SQLAlchemy without FastAPI should install sqlalchemy[asyncio] directly.
dev        = ["pytest", "pytest-django", "pytest-asyncio", "coverage", "mypy", "ruff"]
```

---

## `config/feature-flags.yaml` Schema

The YAML file is the governance source of truth. `yaml_loader.py` validates the schema using `pydantic` before deserializing into `FlagDefinition` objects. Invalid keys, missing required fields, or out-of-range `rollout_percentage` values raise a `StorageError` with a descriptive message. `flagforge sync --dry-run` runs validation without writing to the DB.

**Sync conflict strategy**: YAML always wins for fields it controls (`default_enabled`, `rollout_percentage`, `is_public`, `description`, `environments`, `deprecated`). Tenant overrides and user/group targeting are API-only and are never touched by sync. `flagforge sync --remove-deprecated` deletes flags marked `deprecated: true` and their tenant overrides.

```yaml
flags:
  - key: new_dashboard
    name: New Dashboard
    description: Redesigned dashboard UI
    default_enabled: false
    is_public: false          # false → only visible to authenticated users in GET /flags/
    rollout_percentage: 0     # 0–100; 0 = disabled for all, 100 = no hashing needed
    environments:             # optional; omit to enable in all environments
      - staging
      - production

  - key: beta_api
    name: Beta API
    description: Next-gen API endpoints
    default_enabled: true
    is_public: true
    rollout_percentage: 100
    deprecated: false         # set to true when ready for removal
```

`is_public` is exposed on `FlagDefinition` (`core/models.py`) and controls anonymous API visibility.
User/group targeting is configured via API/Admin only, not in YAML.

---

## Implementation Order

| Step | Area | What |
|------|------|------|
| 1 | Core | `context.py`, `models.py`, `exceptions.py`, `hasher.py`, `resolver.py`, `engine.py` |
| 2 | Storage | `base.py`, `memory.py` (`InMemoryStorage` + `AsyncInMemoryStorage`), `yaml_loader.py` (+ pydantic schema validation) |
| 3 | Cache | `base.py`, `null.py`, `local.py`, `keys.py`, `redis_cache.py`, `async_redis_cache.py` |
| 4 | Unit tests | resolver, hasher, engine (InMemory backend) |
| 5 | Django | `models.py`, `storage.py` (both tenancy modes), `migrations/0001_initial.py` |
| 6 | Django | `signals.py`, `middleware.py` (cache wiring) |
| 7 | Django | `admin.py`, management commands |
| 8 | Django | `views.py` (including admin CRUD), `serializers.py`, `urls.py` |
| 9 | Django | Integration tests (models, storage, views, management commands, `@flag_required` decorator) |
| 10 | FastAPI | `models.py`, `storage.py`, `context.py`, `dependencies.py`, `middleware.py`, `lifespan.py` (validates storage connectivity + settings on startup), `router.py` (including CRUD) |
| 11 | FastAPI | Integration tests |
| 12 | Packaging | `pyproject.toml`, `README.md`, `CHANGELOG.md`, `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` |
| 13 | CLI | `cli/main.py` (requires `[project.scripts]` entry point from step 12) |
| 14 | Performance | `tests/performance/test_throughput.py` |

---

## Future Considerations (v2)

The following are out of scope for v1 but the data model is designed to accommodate them:

- **Audit log**: Record who changed what flag and when (ORM models include `updated_at` / `updated_by`). In v1, `updated_by` is accepted as an optional request body field in the admin API but is not automatically populated from the authenticated user — callers must pass it explicitly.
- **Webhooks / Events**: Emit events on flag changes so downstream services can react without polling.
- **Scheduled flags**: Enable/disable flags at a future timestamp.
- **A/B experiment integration**: Tie flag variants to analytics events.

---

## Verification

- **Unit**: `pytest tests/unit/` — resolver order, rollout hashing stability, environment gating
- **Cache tristate**: assert `get()` returning `False` is treated as "cached disabled", not a miss
- **Django**: `pytest tests/integration/django/` with PostgreSQL via `pytest-django`
- **FastAPI**: `pytest tests/integration/fastapi/` with async SQLAlchemy (verify `AsyncSQLAlchemyStorage` works end-to-end)
- **Auth**: All 3 states (anonymous, authenticated, staff) against both API endpoints
- **Isolation**: Assert `tenant_a` storage queries never return `tenant_b` overrides
- **Cascade delete**: Assert `delete_definition(key)` removes all `TenantOverride` rows for that key
- **Upsert idempotency**: `sync_feature_flags` run twice produces the same DB state
- **YAML validation**: Confirm `pydantic` raises on missing `key`, `rollout_percentage > 100`, unknown fields
- **Sync conflict**: Verify YAML sync overwrites definition fields but preserves tenant overrides
- **Environment gate**: Flag with `environments: [staging]` returns `False` when `context.environment = "production"`
- **Determinism**: Same `(key, user_id)` → same bool across 1000 calls
- **Rollout shortcut**: `percentage=100` returns `True` without hashing; `percentage=0` returns `False`
- **Bulk evaluation**: `evaluate_many(["a", "b", "c"], ctx)` returns correct dict with single storage round-trip; unknown keys return `False` (not omitted, not raised)
- **None override**: Resolver skips steps 1–3 entirely when no `TenantOverride` exists for the `(key, tenant_id)` pair
- **None user_id rollout**: Anonymous users (`user_id=None`) hash consistently per `(tenant_id, key)` — same result across calls
- **Lifespan check**: FastAPI app raises on startup when storage is unreachable or settings are invalid
- **Smart cache keys**: Flags without user/group targeting use `ff:resolved:…` key; flags with targeting use `ff:user:…` key
- **Async cache**: `AsyncRedisCache` works end-to-end with `AsyncSQLAlchemyStorage` in FastAPI (no event loop blocking)
- **Background tasks**: `async_request_context()` properly initializes and flushes `LocalCache` for FastAPI `BackgroundTasks`
- **Performance**: ≥10k evaluations/sec with `NullCache + InMemoryStorage` (treated as a relative regression guard, not an absolute SLA — baseline is recorded in CI against a standard runner); separately benchmark `RedisCache` against local Redis
- **System checks**: `django.test.utils.call_command('check')` catches invalid `FLAGFORGE_TENANCY_MODE`
- **Types**: `mypy src/flagforge --strict`
- **Lint**: `ruff check src/ tests/`
