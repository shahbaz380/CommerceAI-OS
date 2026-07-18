# Getting Started — CommerceAI OS

**Audience:** Engineers joining the monorepo  
**Phase:** Foundation (no application runtime yet)

---

## 1. Prerequisites

- Git  
- A code editor (VS Code recommended; `.vscode/` reserved for shared settings)  
- Access to this repository  
- Ability to create local env files from templates (never commit secrets)

Optional later: Node.js/Python/Docker — installed when stack ADRs land.

---

## 2. Clone & Orient

```bash
git clone <repository-url> CommerceAI-OS
cd CommerceAI-OS
```

Read in order:

1. Root [README.md](../../README.md)  
2. [REPOSITORY_STRUCTURE.md](../architecture/REPOSITORY_STRUCTURE.md)  
3. [DEVELOPMENT_STANDARDS.md](../standards/DEVELOPMENT_STANDARDS.md)  
4. [GIT_STRATEGY.md](../standards/GIT_STRATEGY.md)  
5. SRS index: [docs/srs/INDEX.md](../srs/INDEX.md)  

---

## 3. Local Environment Template

```bash
cp .env.example .env
# Edit .env with local placeholders only
```

Do **not** place production credentials in `.env`.

---

## 4. What Exists Today

| Area | Status |
|------|--------|
| Folder monorepo layout | ✅ |
| Engineering standards | ✅ |
| CI foundation checks | ✅ |
| SRS documentation | ✅ in `docs/srs/` |
| Business features | ❌ not started |
| Auth / DB tables / APIs / AI logic | ❌ not started |

---

## 5. Branch Workflow (summary)

```text
main ← release-ready
  ↑
develop ← integration
  ↑
feature/<ticket>-short-name
```

See [GIT_STRATEGY.md](../standards/GIT_STRATEGY.md).

---

## 6. Before You Write Feature Code

Complete the [Project Initialization Checklist](../developer/PROJECT_INITIALIZATION_CHECKLIST.md) items assigned to you, and confirm Phase 0 decisions in [10_Master_Roadmap.md](../srs/10_Master_Roadmap.md).

---

## 7. Where New Code Will Go (preview)

| Work | Location |
|------|----------|
| HTTP API | `apps/api` |
| Web UI | `apps/web` |
| Background jobs | `apps/worker` |
| Shared types | `packages/types` |
| eBay adapter | `services/integration-ebay` |
| AI orchestrator | `ai/orchestrator` |
| Migrations | `database/migrations` |

---

## 8. Help

- Architecture questions → Lead Architect / ADRs in `docs/adr/`  
- Process → TPM / `docs/standards/`  
- Product scope → Product Owner + `docs/srs/`
