#!/usr/bin/env python3
"""Local validator for Vendor Risk Autopilot. No external side effects."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FAILURES: list[str] = []


def ok(msg: str) -> None:
    print(f"PASS {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")
    FAILURES.append(msg)


def load_json(rel: str):
    path = ROOT / rel
    try:
        data = json.load(path.open())
        ok(f"JSON parses: {rel}")
        return data
    except Exception as exc:
        fail(f"JSON parse failed {rel}: {exc}")
        return {}


def risk_level(score: float, policy: dict) -> str | None:
    for name, bounds in policy["risk_levels"].items():
        if bounds["min"] <= score <= bounds["max"]:
            return name
    return None


def main() -> int:
    schema = load_json("schema/vendor_risk_case.schema.json")
    policy = load_json("schema/risk_policy.json")
    case = load_json("examples/acme_payments_case.json")

    required = set(schema.get("required", []))
    for key in ["case_id", "intake", "council_thread", "evidence_register", "risk_assessment", "procurement_decision", "audit"]:
        if key in required and key in case:
            ok(f"required top-level field present: {key}")
        else:
            fail(f"missing required top-level field: {key}")

    weights = policy.get("domain_weights", {})
    if round(sum(weights.values()), 8) == 1.0:
        ok("risk weights sum to 1.0")
    else:
        fail("risk weights do not sum to 1.0")

    evidence_ids = {e["evidence_id"] for e in case["evidence_register"]}
    if len(evidence_ids) == len(case["evidence_register"]):
        ok("evidence IDs unique")
    else:
        fail("evidence IDs duplicated")

    domain_scores = case["risk_assessment"]["domain_scores"]
    if set(domain_scores) == set(weights):
        ok("all risk domains scored")
    else:
        fail(f"risk domain mismatch: {sorted(set(weights) ^ set(domain_scores))}")

    weighted = round(sum(domain_scores[d]["score"] * weights[d] for d in weights), 2)
    if weighted == round(case["risk_assessment"]["weighted_score"], 2):
        ok(f"weighted score matches policy: {weighted}")
    else:
        fail(f"weighted score mismatch: calculated {weighted}, recorded {case['risk_assessment']['weighted_score']}")

    level = risk_level(weighted, policy)
    if level == case["risk_assessment"]["risk_level"]:
        ok(f"risk level matches score: {level}")
    else:
        fail(f"risk level mismatch: calculated {level}, recorded {case['risk_assessment']['risk_level']}")

    confidence = round(sum(e["confidence"] for e in case["evidence_register"]) / len(case["evidence_register"]), 2)
    if confidence == round(case["risk_assessment"]["confidence_score"], 2):
        ok(f"confidence score matches evidence average: {confidence}")
    else:
        fail("confidence score mismatch")

    for domain, score in domain_scores.items():
        missing = [eid for eid in score["evidence_ids"] if eid not in evidence_ids]
        if missing:
            fail(f"{domain} references missing evidence: {missing}")
        else:
            ok(f"{domain} evidence links resolve")

    controls = {c["control_id"] for c in case["procurement_decision"]["required_controls"]}
    library = set(policy["control_library"])
    if controls <= library:
        ok("all decision controls exist in policy library")
    else:
        fail(f"unknown controls: {sorted(controls - library)}")

    missing_map = {
        "dpa": "dpa_required",
        "completed_security_questionnaire": "security_questionnaire",
        "soc2_or_equivalent": "soc2_or_equivalent",
        "price_benchmark": "price_benchmark"
    }
    missing_evidence = set(case["risk_assessment"]["missing_evidence"])
    for missing, control in missing_map.items():
        if missing in missing_evidence and control in controls:
            ok(f"missing evidence maps to control: {missing} -> {control}")
        elif missing in missing_evidence:
            fail(f"missing evidence lacks control: {missing} -> {control}")

    markers = [(m["agent"], m["marker"]) for m in case["council_thread"]["markers"]]
    if markers[0] == ("clawdius", "INTAKE"):
        ok("first marker is Clawdius INTAKE")
    else:
        fail("first marker is not Clawdius INTAKE")
    if {"poseidon", "widowmaker"} <= {agent for agent, marker in markers if marker == "D1"}:
        ok("both specialists posted D1")
    else:
        fail("missing specialist D1")
    if ("clawdius", "SYNTHESIS") in markers and markers[-1] == ("clawdius", "RESOLVED"):
        ok("Clawdius synthesis and resolved markers present")
    else:
        fail("manager closeout markers invalid")

    for rel in ["prompts/clawdius_manager.md", "prompts/widowmaker_osint.md", "prompts/poseidon_commercial.md", "workflows/state_machine.md", "README.md"]:
        text = (ROOT / rel).read_text()
        if len(text) > 300:
            ok(f"artifact present: {rel}")
        else:
            fail(f"artifact too small: {rel}")

    print("\n== Result ==")
    if FAILURES:
        print(f"FAIL {len(FAILURES)} failure(s)")
        return 1
    print("PASS vendor risk package is internally consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
