# Quick Start

Get FlagForge running in 5 minutes.

---

## Install

```bash
pip install flagforge
```

---

## 1. Standalone (no framework)

```python
from flagforge import FlagEngine, FeatureContext
from flagforge.storage.memory import InMemoryStorage
from flagforge.cache import LocalCache
from flagforge.core.models import FlagDefinition, TenantOverride

# Create storage and engine
storage = InMemoryStorage()
engine = FlagEngine(storage=storage, cache=LocalCache())

# Define flags
storage.upsert_definition(FlagDefinition(
    key="new_dashboard",
    name="New Dashboard",
    default_enabled=False,
))
storage.upsert_definition(FlagDefinition(
    key="dark_mode",
    name="Dark Mode",
    default_enabled=True,
))

# Add a tenant-specific override
storage.upsert_tenant_override(TenantOverride(
    key="new_dashboard",
    tenant_id="acme",
    enabled=True,
))

# Evaluate flags
ctx = FeatureContext(tenant_id="acme", user_id="user_42", environment="production")

print(engine.is_enabled("new_dashboard", ctx))  # True (overridden for acme)
print(engine.is_enabled("dark_mode", ctx))      # True (default_enabled)

# Evaluate many at once
results = engine.evaluate_many(["new_dashboard", "dark_mode"], ctx)
# {"new_dashboard": True, "dark_mode": True}
```

---

## 2. Load flags from YAML

```python
from flagforge.storage.memory import InMemoryStorage
from flagforge.storage.yaml_loader import sync_from_yaml
from flagforge import FlagEngine, FeatureContext
from pathlib import Path

storage = InMemoryStorage()
sync_from_yaml(storage, Path("config/feature-flags.yaml"))

engine = FlagEngine(storage=storage)
ctx = FeatureContext(tenant_id="acme", environment="production")
print(engine.is_enabled("beta_dashboard", ctx))
```

---

## 3. Django (5-minute setup)

```bash
pip install flagforge[django]
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    "rest_framework",
    "flagforge.contrib.django",
]
MIDDLEWARE = [
    ...
    "flagforge.contrib.django.middleware.RequestCacheMiddleware",
]
```

```bash
python manage.py migrate
python manage.py sync_feature_flags --config config/feature-flags.yaml
```

```python
# views.py
from flagforge.contrib.django.engine import flag_enabled

def home(request):
    if flag_enabled("new_dashboard", request):
        return render(request, "home_v2.html")
    return render(request, "home.html")
```

---

## 4. FastAPI (5-minute setup)

```bash
pip install flagforge[fastapi]
```

```python
from fastapi import FastAPI, Depends
from flagforge.contrib.fastapi import create_flagforge_lifespan
from flagforge.contrib.fastapi.router import router as flags_router
from flagforge.contrib.fastapi.dependencies import feature_flag_dependency

app = FastAPI(
    lifespan=create_flagforge_lifespan("postgresql+asyncpg://user:pass@localhost/mydb")
)
app.include_router(flags_router, prefix="/api")

@app.get("/beta")
async def beta(_=Depends(feature_flag_dependency("beta_feature"))):
    return {"message": "You have access!"}
```

---

## 5. Gradual rollout

```python
from flagforge.core.models import FlagDefinition, TenantOverride

# Enable for 20% of users in the "acme" tenant
storage.upsert_definition(FlagDefinition(
    key="new_checkout",
    name="New Checkout",
    default_enabled=False,
))
storage.upsert_tenant_override(TenantOverride(
    key="new_checkout",
    tenant_id="acme",
    enabled=True,
    rollout_percentage=20,
))

# Evaluation is deterministic per user_id
ctx_a = FeatureContext(tenant_id="acme", user_id="user_001")
ctx_b = FeatureContext(tenant_id="acme", user_id="user_002")
# Some users get True, some get False — same user always gets the same result
```

---

## 6. User/group targeting

```python
from flagforge.core.models import TenantOverride

# Enable only for specific users and the "beta_testers" group
storage.upsert_tenant_override(TenantOverride(
    key="new_dashboard",
    tenant_id="acme",
    enabled=False,                         # off by default for this tenant
    enabled_for_users=["user_42", "user_99"],
    enabled_for_groups=["beta_testers"],
))

ctx = FeatureContext(
    tenant_id="acme",
    user_id="user_42",         # explicitly enabled
    group_ids=["standard"],
)
engine.is_enabled("new_dashboard", ctx)  # True
```

---

## Next Steps

- [Django Integration Guide](django.md)
- [FastAPI Integration Guide](fastapi.md)
- [React Frontend Guide](react.md)
- [Configuration Reference](configuration.md)
