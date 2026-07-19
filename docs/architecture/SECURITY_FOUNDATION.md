# Security Foundation (Repository)

**Version:** 1.0  

---

## Secrets

| Item | Location in repo | Production |
|------|------------------|------------|
| Templates | `secrets/templates/` | — |
| Policies | `secrets/policies/` | — |
| Real values | **Never in git** | Secret manager |

Developers use `.env` locally (gitignored).

---

## Certificates

| Item | Repo | Notes |
|------|------|-------|
| Placeholders | `security/certificates/` | `.gitkeep` only |
| TLS | Cloud ACM/managed certs | Not committed |
| mTLS client certs (future) | Secret manager | Partner APIs |

---

## Encryption Keys

| Key type | Handling |
|----------|----------|
| Data encryption keys | KMS CMK/provider-managed |
| Field encryption (tokens) | KMS + app envelope encryption later |
| JWT signing | Secret manager; rotate with dual-key window |
| Backup encryption | Backup service / KMS |

Repo: `security/keys/` placeholders only — **no real key material**.

---

## Permissions & Access Control

- Permission code catalog will live under `security/permissions/` and `packages/auth-contracts`.  
- Align with SRS RBAC (Owner, Manager, Staff/Operator, Viewer, Super Admin).  
- Enforcement points (future code): API middleware, domain services, AI tools.  

---

## Security Policies

Store written policies in `security/policies/`:

- Acceptable use for engineers  
- Secret handling  
- Vulnerability disclosure internal process  
- Dependency update expectations  
- Production access (JIT, MFA)  

---

## Threat Models

- High-risk features require a short threat model in `security/threat-models/` or an ADR.  
- Cover: tenancy, injection, privilege escalation, marketplace side effects, AI tool abuse.

---

## CI Guards (foundation)

- `.github/workflows/ci.yml` blocks obvious secret files.  
- Expand with SAST, dependency scan, container scan when stack lands.

---

**End of Security Foundation**
