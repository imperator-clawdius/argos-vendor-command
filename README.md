# Vendor Risk Autopilot

**Enterprise multi-agent workflow for vendor onboarding, procurement risk, and third-party due diligence — designed for the same agent orchestration platform that runs the Trident Protocol.**

Operator: Teddy Alston · [teddyalston.com](https://teddyalston.com)

---

## 1. The brief

Vendor Risk Autopilot is a structured multi-agent workflow that handles the full vendor assessment lifecycle — intake, specialist investigation, risk scoring, control recommendation, and auditable closure. Three agents (one manager, two specialists) execute against a shared schema, a weighted risk policy, and a state machine that gates every transition.

It runs on the same Telegram-native agent platform as [Trident Protocol](https://github.com/imperator-clawdius/trident-protocol) — the same Clawdius, Poseidon, and Widowmaker agents that handle content and ops also handle vendor due diligence. The workflow is local-only: it produces structured `VendorRiskCase` records and leaves procurement approval to human operators.

## 2. The job it does

Third-party risk assessments are slow because they're manual — someone reads a vendor's SOC 2, checks for sanctions, Googles for breach history, asks about pricing, and writes a memo. Most small and mid-market companies skip the process entirely because they don't have a dedicated vendor risk team.

The requirement: give a solo operator or small procurement team a repeatable, auditable process that produces a documented risk decision in hours instead of weeks — without needing a security team to run it.

That is the same problem an enterprise vendor risk team has, compressed to operator scale. An intake comes in; agents research in parallel; the manager synthesizes a score, recommends controls, and closes with an audit trail. Every decision is grounded in a weighted risk policy, a control library with explicit owners and due-before dates, and hard stops that block auto-approval.

## 3. Constraints

**No ambient authority.** The workflow produces structured artifacts — `VendorRiskCase` JSON records — but never mutates procurement, payment, email, or contract systems directly. Every procurement action requires a human approval outside the agent plane.

**Schema-first: audit trail is a design requirement, not an afterthought.** Every case carries a full evidence register, risk assessment with domain scores, procurement decision, and audit closure. The schema is versioned. If it isn't in the record, it didn't happen.

**Weighted policy, not gut feel.** Nine risk domains (cybersecurity 18%, data privacy 16%, sanctions 14%, litigation 10%, financial stability 10%, operational dependency 10%, geographic 7%, commercial 8%, reputation 7%) are scored individually and aggregated into a decision: `approve`, `approve_with_controls`, `escalate`, or `reject`. Hard stops override all scoring.

**Peer review baked in.** Both specialists research independently and return evidence before the manager synthesizes. The manager cannot override missing evidence or a hard stop.

## 4. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Council Thread                       │
│  [INTAKE] → [D1 Poseidon] [D1 Widowmaker]               │
│         → [SYNTHESIS] → [RESOLVED]                      │
└─────────────────────────────────────────────────────────┘
```

| Component | Role |
|---|---|
| **Clawdius** | Manager — intake, dispatch, synthesis, decision, audit closure |
| **Widowmaker** | Specialist — OSINT, sanctions, litigation, breach, reputation, jurisdiction, stability signals |
| **Poseidon** | Specialist — pricing, commercial fit, alternatives, lock-in, negotiation leverage |
| **State machine** | 7 states: draft → intake → specialist_review → synthesis → resolved / escalated / rejected |
| **Risk policy** | Weighted 9-domain scoring matrix with control library and hard stops |
| **Schema** | Versioned `VendorRiskCase` record — evidence, scores, decisions, audit |

### Decision Model

| Decision | Condition |
|---|---|
| `approve` | All domains scored, no hard stops, residual risk low |
| `approve_with_controls` | Low-moderate risk with listed control requirements (DPA, SOC 2, insurance, etc.) |
| `escalate` | High risk, critical risk, missing critical evidence, or contract value above threshold |
| `reject` | Confirmed sanctions hit, active unresolved data breach, rejected legal/security control |

Control library items track to specific owners and due-before gates — `dpa_required` due before contract signature, `soc2_or_equivalent` due before production access, `insurance_certificate` due before first payment.

## 5. Failure log

**1. Manager short-circuited specialist review.** Early versions let Clawdius synthesize with partial evidence — it sometimes produced a recommendation before both specialists returned. Fix: the state machine now blocks the synthesis transition until each domain has an evidence entry or a deliberate missing-evidence marker. Lesson: lock the choreography in state transitions, not conventions.

**2. Over-engineered evidence register.** The initial evidence schema was too granular — source URL, capture method, timestamp, reviewer, confidence, extract, relevance — and agents spent more time structuring evidence than evaluating it. Fix: flattened to a `source`, `summary`, `domain` triple. Enough for audit; not so much that it crowds out judgment. Lesson: schema design is a UX problem for the agents, not just the database.

**3. Hard stops had no override path.** When a sanctions hit was a false positive (same name, different entity), the system had no way to document the override. Fix: added an `escalated` state with explicit human override fields — override reason, override authority, and override timestamp. Hard stops still block auto-approval; they just don't block the operator. Lesson: automation that cannot be overridden by a human will be bypassed by a human.

## 6. Gates

- **Dual-specialist requirement.** Clawdius cannot proceed to synthesis until both Poseidon and Widowmaker have posted `[D1]`. This prevents single-point-of-failure in research.
- **Marker ceiling.** `[D3]` is the maximum follow-up round before synthesis or escalation — no infinite loops.
- **Missing-evidence discipline.** Every risk domain must have either evidence or an explicit missing-evidence entry. Unscored domains block `approve`.
- **Hard stops win.** Confirmed sanctions, active breach, or rejected legal/security controls force `escalate` or `reject` regardless of other scores.
- **Static validation.** The `validate.py` script checks schema compliance, example cases, risk score math, control assignments, prompt contracts, and Council marker sequence — runnable offline, no agents required.

## 7. Files

```
validate.py                        — Schema and workflow validator
schema/vendor_risk_case.schema.json — Versioned case record schema
schema/risk_policy.json             — Weights, levels, control library, hard stops
examples/acme_payments_case.json    — Worked example
prompts/clawdius_manager.md         — Manager system prompt
prompts/widowmaker_osint.md         — OSINT specialist prompt
prompts/poseidon_commercial.md      — Commercial specialist prompt
workflows/state_machine.md          — State definitions and transition rules
```

### Run validation

```bash
python3 validate.py
```

## Integration

Vendor Risk Autopilot is designed to be wired into any agent orchestration platform that supports Telegram-native multi-agent workflows. It connects to [Trident Protocol](https://github.com/imperator-clawdius/trident-protocol) at the agent layer — the same Clawdius, Poseidon, and Widowmaker roles — and is independent of any specific gateway implementation.

The integration guardrail: produce a `VendorRiskCase` record first. Human approval second. Never mutate a procurement or payment surface directly from the agent plane.

---

Related public work: [trident-protocol](https://github.com/imperator-clawdius/trident-protocol) · [launchdesk](https://github.com/imperator-clawdius/launchdesk) · [daybreak](https://github.com/imperator-clawdius/daybreak)

— Teddy Alston, Orlando, FL
