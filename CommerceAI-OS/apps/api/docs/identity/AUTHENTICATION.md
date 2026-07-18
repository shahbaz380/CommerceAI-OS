# Authentication Guide

## Endpoints

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/auth/register` | Public |
| POST | `/api/v1/auth/login` | Public |
| POST | `/api/v1/auth/refresh` | Public (refresh token) |
| POST | `/api/v1/auth/logout` | Bearer |
| GET | `/api/v1/auth/me` | Bearer |
| POST | `/api/v1/auth/change-password` | Bearer |
| POST | `/api/v1/auth/password-reset/request` | Public (placeholder) |
| POST | `/api/v1/auth/email-verification/request` | Bearer (placeholder) |
| GET | `/api/v1/auth/sessions` | Bearer |
| DELETE | `/api/v1/auth/sessions/{id}` | Bearer |

## Token model

- **Access JWT** — short-lived; carries `sub`, `roles`, `permissions`, `sid`, `jti`, `type=access`  
- **Refresh JWT** — longer-lived; `type=refresh`; stored hashed in DB; rotated on use  
- **Session** — device row; revoked on logout / password change  

## Login hardening

- Generic invalid credential errors  
- Failed attempt counter + 15m lockout after 5 failures  
- Login history + security events  

## Example

```http
POST /api/v1/auth/login
{"email":"owner@example.com","password":"Str0ng!Passw0rd","remember_me":true}

Authorization: Bearer <access_token>
```
