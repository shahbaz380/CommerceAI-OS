# Monitoring Foundation

**Version:** 1.0  

---

## Health Checks

| Check | Path (future) | Meaning |
|-------|---------------|---------|
| Liveness | `/health/live` | Process up |
| Readiness | `/health/ready` | Can accept traffic (DB/pool) |
| Dependencies | internal | eBay/LLM/Stripe degraded flags (may not fail readiness) |

Foundation: document contracts now; implement with Backend Foundation phase.

---

## Performance Monitoring

- RED: Rate, Errors, Duration per route class  
- USE: Utilization, Saturation, Errors for workers  
- Queue age and depth  
- DB pool wait, replica lag  

---

## AI Monitoring

- Tasks by agent/status  
- Latency and estimated cost per tenant  
- Approval funnel rates  
- Safety filter hits  
- Budget exhaustion  
- Abnormal tool-call graphs  

---

## Infrastructure Monitoring

- CPU, memory, disk, network  
- LB 5xx, target health  
- NAT/egress anomalies  
- Certificate expiry  

---

## Business Metrics

- Workspaces created  
- Connections healthy vs reauth_required  
- Time-to-first-sync  
- Orders processed in-app  
- AI recommendation accept/edit/reject (privacy-safe aggregates)  

---

## Alert Strategy

| Severity | Response |
|----------|----------|
| Critical | Page on-call |
| High | Same-day ticket + notify |
| Medium | Backlog triage |
| Low | Weekly review |

Every critical alert must reference a runbook under `monitoring/runbooks/` or `docs/runbooks/`.

---

## Dashboards (as-code folders)

Populate `monitoring/dashboards/` when stack chosen (CloudWatch/Grafana/etc.).

---

**End of Monitoring Foundation**
