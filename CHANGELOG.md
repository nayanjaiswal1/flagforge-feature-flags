# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-02

### Added

- Core `FlagEngine` and `AsyncFlagEngine` for sync/async flag evaluation
- Multi-tenant flag resolution with per-tenant overrides
- Gradual rollout with deterministic MurmurHash3 bucketing
- User-level and group-level flag targeting
- Environment gating (`environments: [staging, production]`)
- `FeatureContext` dataclass for structured evaluation context
- **Django integration** (`flagforge.contrib.django`):
  - Django ORM models (`FeatureFlagDefinition`, `TenantFeatureFlag`) with migrations
  - DRF REST API endpoints for flag management and evaluation
  - `RequestCacheMiddleware` for request-scoped caching
  - `@flag_required` view decorator
  - `{% flag %}` template tag
  - Django Admin integration
  - Management commands: `sync_feature_flags`, `show_flag_status`, `enable_flag_for_tenant`, `disable_flag_for_tenant`
  - Django system checks
- **FastAPI integration** (`flagforge.contrib.fastapi`):
  - `AsyncSQLAlchemyStorage` with async SQLAlchemy 2.0
  - `create_flagforge_lifespan` factory for easy setup
  - `flagforge_lifespan` composable context manager
  - APIRouter with full CRUD + evaluation endpoints
  - `feature_flag_dependency` for route-level flag guards
  - `get_engine` / `get_context` dependency injection helpers
- **Storage backends**:
  - `InMemoryStorage` / `AsyncInMemoryStorage` for testing
  - `DjangoStorageAdapter` for Django ORM
  - `AsyncSQLAlchemyStorage` for async SQLAlchemy
  - YAML file loader (`load_flags`, `sync_from_yaml`)
- **Cache backends**:
  - `LocalCache` / `AsyncLocalCache` (request-scoped in-memory)
  - `RedisCache` / `AsyncRedisCache` (distributed Redis)
  - `NullCache` / `AsyncNullCache` (no-op for testing)
- Global engine pattern (`configure_engine`, `get_engine`, `is_enabled`, `evaluate_many`)
- CLI commands: `flagforge sync`, `flagforge status`, `flagforge enable`, `flagforge disable`
- Full type hints and `py.typed` marker
- Python 3.10, 3.11, 3.12, 3.13 support
