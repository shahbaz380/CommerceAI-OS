# Identity & Access Management (IAM)

Enterprise identity platform for CommerceAI OS.

## Capabilities

| Area | Status |
|------|--------|
| Registration / Login / Logout | Implemented |
| JWT access + refresh (rotation) | Implemented |
| Session tracking & revocation | Implemented |
| Argon2 password hashing | Implemented |
| Account lockout | Implemented |
| RBAC roles & permissions | Implemented + seeded |
| AuthZ dependencies | Implemented |
| OAuth provider framework | Structure only (no live IdPs) |
| Email verification / reset email | Placeholder (no mailer) |

## Default roles

`super_admin`, `organization_owner`, `manager`, `staff`, `support`, `read_only`, `ai_agent`, `marketplace_service`

## Key packages

- `domain/identity` — policies, role/permission catalog  
- `application/identity` — AuthService, AuthorizationService, seed  
- `infrastructure/security` — JWT, Argon2, OAuth registry  
- `infrastructure/persistence/models/identity.py` — tables  
- `presentation/api/v1/routes/auth.py` — HTTP API  

## Guides

- [Authentication Guide](AUTHENTICATION.md)  
- [Authorization / RBAC](RBAC.md)  
- [Security Guide](SECURITY.md)  
- [Developer Guide](DEVELOPER.md)  
