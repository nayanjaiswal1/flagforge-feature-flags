# Django Integration Guide

FlagForge ships a full Django app (`flagforge.contrib.django`) that provides:

- Django ORM models with migrations
- Django REST Framework API endpoints
- Middleware for request-scoped caching
- View decorators (`@flag_required`)
- Template tags (`{% flag %}`)
- Django Admin panel
- Management commands (`sync_feature_flags`, `show_flag_status`, etc.)
- System checks

---

## Requirements

- Python 3.10+
- Django 4.2+
- djangorestframework 3.14+
- PostgreSQL recommended (uses `JSONField`)

---

## Installation

```bash
pip install flagforge[django]
```

---

## Setup

### 1. Add to `INSTALLED_APPS`

```python
# settings.py
INSTALLED_APPS = [
    ...
    "rest_framework",
    "flagforge.contrib.django",
]
```

### 2. Add middleware

Add the request-scoped cache middleware. It should come **after** session/auth middleware so `request.user` is populated.

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    ...
    "flagforge.contrib.django.middleware.RequestCacheMiddleware",  # <-- add here
]
```

### 3. Run migrations

```bash
python manage.py migrate
```

This creates two tables:

| Table | Description |
|-------|-------------|
| `feature_flag_definition` | Global flag definitions |
| `tenant_feature_flag` | Per-tenant overrides |

### 4. Include the REST API (optional)

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    ...
    path("api/flags/", include("flagforge.contrib.django.urls")),
]
```

---

## Multi-Tenancy Setup

FlagForge needs to know the current tenant. The simplest approach is a custom middleware that sets `request.tenant_id`:

```python
# myapp/middleware.py
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Example: read tenant from subdomain
        host = request.get_host().split(".")[0]
        request.tenant_id = host  # e.g. "acme" from acme.example.com
        return self.get_response(request)
```

Or from a JWT claim, session, header — whatever suits your architecture.

---

## Evaluating Flags in Views

### Using the helper function

```python
# views.py
from flagforge.contrib.django.engine import flag_enabled

def checkout_view(request):
    if flag_enabled("new_checkout", request):
        return render(request, "checkout_v2.html")
    return render(request, "checkout_v1.html")
```

`flag_enabled(key, request)` automatically builds a `FeatureContext` from `request.tenant_id`, `request.user`, and `request.environment` (optional).

### Using the engine directly

```python
from flagforge.contrib.django.storage import DjangoStorageAdapter
from flagforge.cache import LocalCache
from flagforge.core.engine import FlagEngine
from flagforge.core.context import FeatureContext

def my_view(request):
    storage = DjangoStorageAdapter()
    engine = FlagEngine(storage=storage, cache=LocalCache())

    context = FeatureContext(
        tenant_id=getattr(request, "tenant_id", None),
        user_id=str(request.user.pk) if request.user.is_authenticated else None,
        group_ids=[str(g.pk) for g in request.user.groups.all()],
        environment="production",
    )

    enabled = engine.is_enabled("new_dashboard", context)
    ...
```

### Evaluate multiple flags at once

```python
flags = engine.evaluate_many(
    ["new_dashboard", "beta_checkout", "dark_mode"],
    context
)
# flags = {"new_dashboard": True, "beta_checkout": False, "dark_mode": True}
```

---

## View Decorator

Protect a view so it only renders when a flag is enabled:

```python
from flagforge.contrib.django.decorators import flag_required

# Raise Http404 if flag is off
@flag_required("beta_dashboard")
def beta_dashboard(request):
    return render(request, "beta_dashboard.html")

# Redirect to "/" if flag is off
@flag_required("beta_dashboard", redirect_to="/")
def beta_dashboard_safe(request):
    return render(request, "beta_dashboard.html")
```

---

## Template Tags

Load the `flagforge` template tag library:

```django
{% load flagforge %}

{% flag "new_dashboard" request %}
  {# This block renders only when the flag is enabled #}
  <div class="new-dashboard">
    <h1>Welcome to the new dashboard!</h1>
  </div>
{% endflag %}
```

The `{% flag %}` tag requires the `request` object to resolve the current tenant and user.

---

## Django Admin

FlagForge automatically registers `FeatureFlagDefinition` and `TenantFeatureFlag` in the Django Admin. Navigate to `/admin/` to manage flags and per-tenant overrides through the UI.

---

## REST API

When you include `flagforge.contrib.django.urls`, the following endpoints are available:

### `GET /api/flags/` — Evaluate all flags

Returns resolved flag values for the current request. Authenticated users see all flags; anonymous users see only `is_public=True` flags.

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

### Admin endpoints (require admin/staff user)

```
GET    /api/flags/admin/                           List all definitions
POST   /api/flags/admin/                           Create a definition
GET    /api/flags/admin/{key}/                     Get a definition
PUT    /api/flags/admin/{key}/                     Update a definition
DELETE /api/flags/admin/{key}/                     Delete a definition
PUT    /api/flags/admin/{key}/tenants/{tenant_id}/ Upsert tenant override
DELETE /api/flags/admin/{key}/tenants/{tenant_id}/ Delete tenant override
```

### Upsert tenant override — example

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

## Management Commands

### Sync flags from YAML

```bash
python manage.py sync_feature_flags --config config/feature-flags.yaml
# With --remove-deprecated to delete flags not in the YAML:
python manage.py sync_feature_flags --config config/feature-flags.yaml --remove-deprecated
```

### Show flag status for a tenant

```bash
python manage.py show_flag_status --tenant acme_corp
```

### Enable / disable a flag for a tenant

```bash
python manage.py enable_flag_for_tenant --flag new_dashboard --tenant acme_corp
python manage.py disable_flag_for_tenant --flag new_dashboard --tenant acme_corp
```

---

## YAML Configuration File

```yaml
# config/feature-flags.yaml
flags:
  new_dashboard:
    name: New Dashboard
    description: Redesigned main dashboard
    default_enabled: false
    is_public: true
    rollout_percentage: 0
    environments:
      - staging
      - production

  beta_checkout:
    name: Beta Checkout
    description: One-page checkout flow
    default_enabled: false
    is_public: false
    rollout_percentage: 20

  dark_mode:
    name: Dark Mode
    description: Dark theme UI
    default_enabled: true
    is_public: true
```

---

## Using Redis Cache (Production)

Replace `LocalCache` with `RedisCache` for multi-process deployments:

```python
# settings.py
FLAGFORGE_REDIS_URL = "redis://localhost:6379/0"
FLAGFORGE_CACHE_TTL = 300  # seconds
```

```python
# views.py or engine setup
from flagforge.cache import RedisCache
from flagforge.contrib.django.storage import DjangoStorageAdapter
from flagforge.core.engine import FlagEngine

def get_engine():
    storage = DjangoStorageAdapter()
    cache = RedisCache.from_url("redis://localhost:6379/0", ttl=300)
    return FlagEngine(storage=storage, cache=cache)
```

---

## System Checks

FlagForge registers Django system checks. Run `python manage.py check` to verify your configuration is valid.

---

## Complete Example Project

```
myproject/
├── myproject/
│   ├── settings.py
│   ├── urls.py
│   └── middleware.py       # TenantMiddleware
├── myapp/
│   ├── views.py
│   └── templates/
│       └── dashboard.html
└── config/
    └── feature-flags.yaml
```

**`settings.py`**

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "flagforge.contrib.django",
    "myapp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "myproject.middleware.TenantMiddleware",
    "flagforge.contrib.django.middleware.RequestCacheMiddleware",
]
```

**`views.py`**

```python
from django.shortcuts import render
from flagforge.contrib.django.engine import flag_enabled
from flagforge.contrib.django.decorators import flag_required

def home(request):
    return render(request, "home.html", {
        "show_new_dashboard": flag_enabled("new_dashboard", request),
    })

@flag_required("beta_feature", redirect_to="/")
def beta_feature(request):
    return render(request, "beta.html")
```

**`dashboard.html`**

```django
{% load flagforge %}

{% flag "new_dashboard" request %}
  <div id="new-dashboard">...</div>
{% endflag %}
```
