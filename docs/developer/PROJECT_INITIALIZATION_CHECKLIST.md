# Project Initialization Checklist

Complete **before** feature coding (auth, eBay, AI agents, business APIs).

---

## A. Repository & Governance

- [x] Monorepo folder structure created  
- [x] Root README and architecture docs  
- [x] `.gitignore`, `.editorconfig`, `.env.example`  
- [x] Development standards documented  
- [x] Git strategy documented  
- [x] PR/issue templates  
- [x] Foundation CI workflow  
- [ ] GitHub/GitLab remote created and `main`/`develop` protected  
- [ ] CODEOWNERS file with real teams  
- [ ] Branch protection rules enabled in VCS  
- [ ] License/confidentiality header decision  

---

## B. Phase 0 Product/Architecture Decisions (from SRS Part 10)

- [ ] MVP scope cut signed by Product  
- [ ] Role Catalog v1 frozen  
- [ ] API conventions frozen (money, IDs, JSON casing, error envelope)  
- [ ] Primary language/runtime stack ADR (`docs/adr/`)  
- [ ] Modular monolith confirmed as starting stance (ADR)  
- [ ] Billing provider confirmed (Stripe recommended)  
- [ ] Data retention draft (logs, AI traces, PII)  
- [ ] Legal AI disclosure / privacy outline reviewed  

---

## C. Tooling Bootstrap (next engineering steps — not done in this prompt)

- [ ] Package manager workspace (npm/pnpm/yarn or language equivalent)  
- [ ] Root build orchestration (turbo/nx/make)  
- [ ] Shared lint/format config wired to CI  
- [ ] Pre-commit hooks (husky/pre-commit)  
- [ ] Editor settings committed under `.vscode/`  
- [ ] Devcontainer definition (optional but recommended)  

---

## D. Environments & Secrets

- [x] Environment strategy documented  
- [x] Config/feature-flag templates  
- [ ] Cloud accounts/projects for staging/prod  
- [ ] Secret manager namespaces created  
- [ ] Local docker-compose for Postgres/Redis (when stack chosen)  
- [ ] Naming convention for secrets verified with DevOps  

---

## E. Quality & Security Baseline

- [x] Test folder structure  
- [x] Logging/error/monitoring strategies documented  
- [ ] SAST/dependency scanning jobs in CI  
- [ ] Secret scanning (gitleaks/trufflehog class) in CI  
- [ ] First threat model for tenancy/auth (before auth coding)  
- [ ] Pen-test vendor shortlist for pre-GA  

---

## F. Integration Prerequisites

- [ ] eBay developer program access / sandbox apps  
- [ ] LLM provider account (sandbox/dev keys in secret manager only)  
- [ ] Stripe test account  
- [ ] Email provider test credentials  

---

## G. Documentation Completeness

- [x] SRS Parts 1–10 in `docs/srs/`  
- [x] Repository structure guide  
- [x] Getting started guide  
- [ ] ADR-0001 Modular monorepo  
- [ ] ADR-0002 Language/runtime selection  
- [ ] On-call & SEV process owners named  

---

## H. Team Readiness

- [ ] Delivery roles staffed (or vendor contracted)  
- [ ] Access control to repo/cloud granted  
- [ ] Definition of Done agreed with QA  
- [ ] Communication channels (standup, incident) established  

---

## Exit Criteria for “Foundation Complete → Backend Foundation”

All **A** items done in-repo; **B** decisions signed; remote protection on; stack ADR accepted; checklist owners assigned for remaining C–H items.

---

**End of Checklist**
