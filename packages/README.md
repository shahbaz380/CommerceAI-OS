# Shared Packages

Internal libraries for CommerceAI OS (`@commerceai/*` naming when package manifests are added).

| Package | Role |
|---------|------|
| shared | Cross-cutting primitives |
| types | Domain types / DTOs |
| config | Config loading |
| utils | Pure helpers |
| ui | Design system |
| sdk | API client SDK |
| events | Domain events |
| logging | Logger facade |
| errors | Error taxonomy |
| auth-contracts | Permission/claim constants |
| validation | Shared schemas |

**Rule:** Packages must not import from `apps/`.
