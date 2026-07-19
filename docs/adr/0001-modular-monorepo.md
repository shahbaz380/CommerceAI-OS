# ADR 0001: Modular Monorepo, Microservice-Ready

## Status

Accepted

## Date

2026-07-16

## Context

CommerceAI OS needs rapid delivery of a multi-tenant SaaS with clear module boundaries (API, web, workers, AI, marketplace adapters) while remaining extractable into microservices later.

## Decision

1. Use a **single monorepo** (`CommerceAI-OS`).  
2. Organize as **apps + packages + services + ai + plugins**.  
3. Start runtime as a **modular monolith** (few deployables: api, web, worker, scheduler).  
4. Keep marketplace and optional capabilities **isolated** under `services/` and `plugins/` for future extraction.  
5. Enforce **dependency direction**: apps → packages/services/ai public APIs; no packages → apps.

## Consequences

### Positive
- Shared types, linting, and atomic cross-module refactors  
- Lower early ops cost than many services  
- Clear extraction seams  

### Negative
- Requires discipline to avoid a “distributed monolith in one process”  
- CI must evolve to path-filtered pipelines as the repo grows  

## Alternatives Considered

- Polyrepo microservices from day one — rejected for MVP velocity  
- Single unstructured app folder — rejected for maintainability  

## References

- `docs/architecture/REPOSITORY_STRUCTURE.md`  
- `docs/srs/10_Master_Roadmap.md`  
