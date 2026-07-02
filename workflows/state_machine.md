# Vendor Risk Autopilot State Machine

## States

| State | Owner | Exit |
| --- | --- | --- |
| `draft` | Requester or Clawdius | Required intake fields present |
| `intake` | Clawdius | `[INTAKE]` posted and specialists mentioned |
| `specialist_review` | Poseidon and Widowmaker | Both specialists post `[D1]` |
| `synthesis` | Clawdius | Score, controls, and decision complete |
| `resolved` | Clawdius | `[RESOLVED]` posted |
| `escalated` | Human approver | Human approves, rejects, or waives |
| `rejected` | Human approver | Case closed |

## Marker Rules

```text
INTAKE -> D1+ -> optional D2/D3 -> SYNTHESIS -> RESOLVED
```

- `[INTAKE]`, `[SYNTHESIS]`, and `[RESOLVED]` belong to Clawdius.
- `[D1]`, `[D2]`, and `[D3]` belong to specialists.
- Both specialists may use `[D1]`.
- `[D3]` is the ceiling before synthesis or escalation.

## Hard Gates

The system must not produce plain `approve` unless every risk domain has evidence or a missing-evidence entry, no hard stop exists, and residual risk is low.

Escalate or reject on confirmed sanctions, active unresolved customer data breach, rejected legal/security control, high-risk missing evidence, or contract value above approval authority.
