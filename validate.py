#!/usr/bin/env python3
"""Local validator for Vendor Risk Autopilot. No external side effects."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
FAILURES: list[str] = []


def ok(msg: str) -> None:
    print(f"PASS {msg}")


def fail(msg: str) -> None:
    print(f"FAIL {msg}")
    FAILURES.append(msg)


def load_json(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        ok(f"JSON parses: {path.name}")
        return data
    except (OSError, UnicodeError, ValueError) as exc:
        fail(f"Cannot read JSON {path.name}: {exc}")
        return None


def risk_level(score: float, policy: dict) -> str | None:
    for name, bounds in policy["risk_levels"].items():
        if bounds["min"] <= score <= bounds["max"]:
            return name
    return None


def check_case(case: dict, policy: dict) -> None:
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
        text = (ROOT / rel).read_text(encoding="utf-8")
        if len(text) > 300:
            ok(f"artifact present: {rel}")
        else:
            fail(f"artifact too small: {rel}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a local VendorRiskCase against the bundled schema and risk policy.")
    parser.add_argument("case_json", nargs="?", type=Path, default=ROOT / "examples/acme_payments_case.json",
                        help="case JSON path (default: bundled fictional example)")
    args = parser.parse_args(argv)
    FAILURES.clear()
    schema = load_json(ROOT / "schema/vendor_risk_case.schema.json")
    policy = load_json(ROOT / "schema/risk_policy.json")
    case = load_json(args.case_json)
    if FAILURES:
        return 1

    Draft202012Validator.check_schema(schema)
    for error in Draft202012Validator(schema).iter_errors(case):
        location = "/" + "/".join(str(part) for part in error.absolute_path)
        fail(f"Schema {location}: {error.message}")
    if not FAILURES:
        ok("case matches bundled JSON schema")
        try:
            check_case(case, policy)
        except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError) as exc:
            # The existing schema leaves the assessment/decision internals open.
            # An incomplete record must fail rather than crash or pass unchecked.
            fail(f"Incomplete or invalid case data for policy checks: {exc}")

    print("\n== Result ==")
    if FAILURES:
        print(f"FAIL {len(FAILURES)} failure(s)")
        return 1
    print("PASS case matches the bundled schema and implemented consistency checks")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
