# HANDOFF — argos-vendor-command

**One-liner:** A schema-first, multi-agent vendor-risk / third-party due-diligence workflow (one manager + two specialists) shipped as prompts, a versioned case schema, a weighted 9-domain risk policy, a state machine, and an offline validator/packet renderer.
**Status:** prototype / reference architecture — ~40% to a standalone product (the artifacts + validator run today; the agent orchestration runtime is NOT in this repo)
**Monetization:** Done-for-you vendor due-diligence service billed per decision packet (the sample PDF is the deliverable); secondarily a paid template/prompt-pack for procurement teams, or SaaS once wired to orchestration.

## What it is
A reference workflow that takes a vendor intake and produces an auditable risk decision. Clawdius (manager) dispatches research to Poseidon (commercial) and Widowmaker (OSINT), then synthesizes a weighted 9-domain score, recommends controls, and closes with an audit trail. This repo holds the contracts and local tooling; the actual Telegram-native agent execution lives on the separate `trident-protocol` platform.

## Who pays & why
Solo operators and small/mid-market procurement teams with no dedicated vendor-risk function. Pain: due diligence is manual and slow (read SOC 2, check sanctions, Google breach history, write a memo), so most skip it. They pay for a repeatable, documented, auditable risk decision delivered in hours instead of weeks.

## Stack
Python 3.10+ (stdlib + `jsonschema` 4.26 only). JSON Schema Draft 2022-12 for the case + policy. Markdown prompts and state-machine spec. GitHub Actions (`.github/workflows/validate.yml`, `gitleaks.yml`). No server/runtime; external hard dependency on the `trident-protocol` Telegram multi-agent platform.

## Architecture
Input: intake JSON (`examples/intake_template.json`) -> agents defined by `prompts/clawdius_manager.md`, `poseidon_commercial.md`, `widowmaker_osint.md` research in parallel -> synthesis scores nine weighted domains against `schema/risk_policy.json` and applies hard stops -> Output: a versioned `VendorRiskCase` record (`schema/vendor_risk_case.schema.json`) rendered to a decision packet by `scripts/render_case_packet.py`. `validate.py` enforces schema/score/control/marker consistency offline; `workflows/state_machine.md` gates every transition. Open first: `README.md`, `validate.py`, `schema/*.json`, `prompts/*.md`.

## What works today
- `validate.py`: checks schema compliance, risk-score math, control assignments, prompt contracts, and Council marker sequence — fully offline, no agents.
- `scripts/render_case_packet.py`: Markdown decision-packet export from a case.
- Bundled worked example (`examples/acme_payments_case.json`) + fictional sample PDFs/ZIP with SHA-256 manifest.
- `unittest` suite (`tests/test_case_workflow.py`); CI runs validation + gitleaks.

## Gaps to ship (ranked)
1. No runnable orchestration — agent dispatch/synthesis depends on the external `trident-protocol` platform; nothing here executes the workflow end to end.
2. No intake UI/API/persistence — cases are hand-authored JSON; a customer can't submit a vendor or receive a packet without an operator.
3. Renderer exports Markdown only (the sample PDFs were prepared separately); no automated PDF delivery and no billing.

## Run it
```bash
python3 -m pip install -r requirements.txt
python3 validate.py                                  # validates the bundled fictional example
python3 validate.py /path/to/completed-case.json     # validate a real case vs schema + policy
python3 scripts/render_case_packet.py /path/to/completed-case.json --out decision-packet.md
python3 -m unittest discover -s tests -v
```

## Risks / unknowns
- The "product" half (orchestration) is in a different repo; this alone cannot run the workflow.
- Validation is local consistency only, not evidence verification — a passing case still requires human review; liability risk if sold as "risk decisions."
- Marketed as "enterprise" but is operator-scale; the only sample is explicitly fictional/placeholder, so there is no proof of real customer work.
- By design it never mutates procurement/payment systems (good), which means a human operator is always in the loop.
- No secrets in repo (gitleaks configured); MIT-style `LICENSE` present.

## Fastest path to revenue
1. Sell vendor due-diligence as a service: operator runs the workflow on `trident-protocol` and delivers the decision-packet PDF per vendor at a fixed price.
2. Automate PDF export from the renderer + a one-field intake form to cut operator time per assessment.
3. Package the schema + policy + prompts as a paid playbook/template for procurement teams who want to self-run.
