# AI Foundation (Repository)

**Version:** 1.0  
**Note:** Structure and contracts only — **no agent business logic** in this phase.

---

## Directory Map

```text
ai/
├── orchestrator/          # Plan, delegate, synthesize
├── agents/
│   ├── product-research/
│   ├── listing-optimization/
│   ├── inventory-monitoring/
│   ├── pricing-intelligence/
│   ├── order-processing/
│   ├── customer-support/
│   ├── analytics/
│   ├── seo-blog/
│   ├── guest-posting-crm/
│   └── executive-assistant/
├── prompts/
│   ├── library/           # Catalog metadata
│   └── templates/         # Versioned templates
├── memory/                # Ports for short/long/task/business memory
├── knowledge-base/        # Grounding docs (non-secret)
├── models/config/         # Provider/model routing templates
├── evaluation/
│   ├── datasets/          # Golden sets (non-PII)
│   └── harness/           # Eval runner (later)
├── tools/                 # Tool registry schemas (later)
└── logs/                  # Local AI log sink
```

---

## Architectural Layers

```text
Executive Assistant / API
        ↓
   Orchestrator
        ↓
  Agent Dispatcher + Task Queue (apps/worker later)
        ↓
     Agents  ↔  Tools (domain APIs)
        ↓
 Model Integration (provider adapters)
        ↓
 Memory / Knowledge / Prompt templates
```

---

## Prompt Library & Templates

- Templates are versioned artifacts.  
- Breaking changes require eval suite run.  
- Library holds index of intents → template versions.  
- No production secrets inside prompts.

---

## Memory

Logical classes (SRS Part 3): short-term, conversation, task, business, long-term, knowledge.  
`ai/memory` holds **interfaces and docs** until implementation.

---

## Knowledge Base

- Tenant-safe grounding documents.  
- Global playbooks without PII.  
- Vector DB optional later — not required for foundation.

---

## Model Configuration

- `config/ai` + `ai/models/config` for provider routing, timeouts, budgets.  
- Multi-provider ready; single provider OK for MVP.

---

## Evaluation

- Golden datasets per agent in `evaluation/datasets`.  
- Harness runs offline in CI later (`ai-eval` job).  
- Production sampling metrics separate from offline eval.

---

## AI Logs

- Follow LOGGING_STRATEGY.md.  
- Local directory for dev only.  
- Decisions/executions ultimately durable in DB (Part 4) when built.

---

## Safety Defaults (config)

- `FEATURE_AI_WRITES_ENABLED=false`  
- Approval matrix enforced when write path implemented  
- Kill switch supported via flag + runtime config  

---

**End of AI Foundation**
