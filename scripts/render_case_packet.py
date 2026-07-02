#!/usr/bin/env python3
"""Render a VendorRiskCase JSON file into a Markdown decision packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def bullet(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- None"


def render(case: dict) -> str:
    intake = case["intake"]
    assessment = case["risk_assessment"]
    decision = case["procurement_decision"]
    lines = [
        f"# Vendor Risk Decision Packet: {intake['vendor_name']}",
        "",
        "## Intake",
        "",
        f"- Vendor: {intake['vendor_name']}",
        f"- Domain: {intake['vendor_domain']}",
        f"- Business unit: {intake['business_unit']}",
        f"- Requested service: {intake['requested_service']}",
        f"- Contract value: ${intake['contract_value_usd']:,.0f}",
        f"- Data access: {intake['data_access_level']}",
        f"- Urgency: {intake['urgency_level']}",
        "",
        "## Recommendation",
        "",
        f"- Recommendation: `{decision['recommendation']}`",
        f"- Weighted risk score: {assessment['weighted_score']}",
        f"- Risk level: `{assessment['risk_level']}`",
        f"- Confidence: {assessment['confidence_score']}",
        f"- Residual risk: `{decision['residual_risk']}`",
        "",
        "## Rationale",
        "",
        decision["rationale"],
        "",
        "## Domain Scores",
        "",
        "| Domain | Score | Rationale | Evidence |",
        "| --- | ---: | --- | --- |",
    ]
    for domain, value in assessment["domain_scores"].items():
        evidence = ", ".join(value.get("evidence_ids", []))
        lines.append(f"| {domain} | {value['score']} | {value['rationale']} | {evidence} |")

    lines += [
        "",
        "## Missing Evidence",
        "",
        bullet(assessment.get("missing_evidence", [])),
        "",
        "## Required Controls",
        "",
        "| Control | Owner | Due Before | Status |",
        "| --- | --- | --- | --- |",
    ]
    for control in decision["required_controls"]:
        lines.append(f"| {control['title']} | {control['owner']} | {control['due_before']} | {control['status']} |")

    lines += [
        "",
        "## Negotiation Points",
        "",
        bullet(decision.get("negotiation_points", [])),
        "",
        "## Evidence Register",
        "",
        "| ID | Domain | Source | Confidence | Summary |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for evidence in case["evidence_register"]:
        lines.append(
            f"| {evidence['evidence_id']} | {evidence['domain']} | {evidence['source_ref']} | "
            f"{evidence['confidence']} | {evidence['summary']} |"
        )

    lines += [
        "",
        "## Approval Chain",
        "",
        "| Role | Required | Status |",
        "| --- | --- | --- |",
    ]
    for approver in decision["approver_chain"]:
        lines.append(f"| {approver['role']} | {approver['required']} | {approver['status']} |")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_json", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    case = json.load(args.case_json.open())
    packet = render(case)
    if args.out:
        args.out.write_text(packet)
    else:
        print(packet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
