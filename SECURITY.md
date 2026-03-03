# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Send a private report to **security@flagforge.dev** with:

- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Your suggested fix (if any)

We will respond within 48 hours and aim to release a patch within 7 days for critical issues.

## Security Considerations

- Feature flags are **not** an access control mechanism. Always enforce permissions on the backend.
- The `/api/flags/` endpoint returns only `is_public=True` flags to unauthenticated callers.
- Tenant isolation is enforced at the storage level — each evaluation requires a `tenant_id`.
- Redis cache keys include the tenant ID to prevent cross-tenant data leakage.
