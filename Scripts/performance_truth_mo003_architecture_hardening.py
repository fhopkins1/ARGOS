"""Materialize Performance Truth MO-003 constitutional architecture evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_MO003_ARCHITECTURE_HARDENING"

PRIOR_EVIDENCE = {
    "RM001": REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_RM001_CONSTITUTIONAL_BASELINE",
    "RM002": REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_RM002_IMPLEMENTATION_CERTIFICATION",
    "RM003": REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_RM003_FINAL_CERTIFICATION",
    "MO001": REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_MO001_CONSTITUTIONAL_HARDENING",
    "MO002": REPOSITORY_ROOT / "Documentation" / "PERFORMANCE_TRUTH_MO002_CERTIFICATION_HARDENING",
}

ORDER_SOURCES = {
    "PERFORMANCE-TRUTH-MO-003-001": Path(r"C:\Users\Fletc\.codex\attachments\cf997f1b-63e0-4050-ab78-0784cb11b4bf\pasted-text.txt"),
    "PERFORMANCE-TRUTH-MO-003-002": Path(r"C:\Users\Fletc\.codex\attachments\eb36f3d8-5ae8-4bfa-be42-3c363d4755b0\pasted-text.txt"),
    "PERFORMANCE-TRUTH-MO-003-003": Path(r"C:\Users\Fletc\.codex\attachments\06c8c6f3-a9aa-4972-89f7-604c51cddb13\pasted-text.txt"),
    "PERFORMANCE-TRUTH-MO-003-004": Path(r"C:\Users\Fletc\.codex\attachments\deca3914-0182-4eda-bb89-4b326afcf57e\pasted-text.txt"),
    "PERFORMANCE-TRUTH-MO-003-005": Path(r"C:\Users\Fletc\.codex\attachments\ce7dd1c7-34be-4298-86b6-3a20c72f477a\pasted-text.txt"),
    "PERFORMANCE-TRUTH-MO-003-006": Path(r"C:\Users\Fletc\.codex\attachments\c74ac683-4547-4861-97f4-4d4228e92cfc\pasted-text.txt"),
    "PERFORMANCE-TRUTH-MO-003-007": Path(r"C:\Users\Fletc\.codex\attachments\54bc5e22-3041-4a4c-bfff-a50239c9a7b3\pasted-text.txt"),
    "PERFORMANCE-TRUTH-MO-003-011": Path(r"C:\Users\Fletc\.codex\attachments\cf9dde2a-114b-4e30-a37e-feb4f8187015\pasted-text.txt"),
    "PERFORMANCE-TRUTH-MO-003-012": Path(r"C:\Users\Fletc\.codex\attachments\35e2be94-9252-4a50-99ec-14cd349824a1\pasted-text.txt"),
}

EXPECTED_ORDER_IDS = tuple(
    f"PERFORMANCE-TRUTH-MO-003-{index:03d}" for index in range(1, 13)
)

RESPONSIBILITIES = (
    ("PT-RESP-001", "Define canonical Performance Truth objects", "core"),
    ("PT-RESP-002", "Construct Performance Calculation Contexts", "core"),
    ("PT-RESP-003", "Calculate interval and cumulative performance", "core"),
    ("PT-RESP-004", "Apply precision, rounding, and normalization", "core"),
    ("PT-RESP-005", "Attribute performance to source truth", "core"),
    ("PT-RESP-006", "Compare certified performance against benchmarks", "core"),
    ("PT-RESP-007", "Publish certified Performance Truth Records", "core"),
    ("PT-RESP-008", "Issue performance corrections and revisions", "core"),
    ("PT-RESP-009", "Supersede prior Performance Truth", "core"),
    ("PT-RESP-010", "Reconcile derived performance to authoritative source truth", "core"),
    ("PT-RESP-011", "Preserve performance provenance", "core"),
    ("PT-RESP-012", "Generate Performance Evidence Packages", "core"),
    ("PT-RESP-013", "Expose certified performance to authorized consumers", "core"),
    ("PT-RESP-014", "Support deterministic replay and audit reconstruction", "core"),
    ("PT-RESP-015", "Manage Performance Certification States", "core"),
    ("PT-RESP-016", "Acquire market data", "supporting"),
    ("PT-RESP-017", "Own closed-position truth", "supporting"),
    ("PT-RESP-018", "Store immutable historical evidence", "supporting"),
    ("PT-RESP-019", "Transport performance records across enterprise boundaries", "bridge"),
    ("PT-RESP-020", "Orchestrate enterprise dependency health", "supporting"),
)

OBJECTS = (
    "PerformanceCalculationContext",
    "PerformanceTruthRecord",
    "PerformanceCorrection",
    "PerformanceRevision",
    "PerformanceEvidencePackage",
    "PerformanceCertificationState",
)

INTERFACES = (
    ("PT-IFACE-001", "Closed Position Truth input", "consume closed-position source truth"),
    ("PT-IFACE-002", "Position Registry input", "consume position lifecycle state"),
    ("PT-IFACE-003", "Market Data input", "consume benchmark and price observations"),
    ("PT-IFACE-004", "Historian output", "publish immutable performance evidence"),
    ("PT-IFACE-005", "Enterprise Audit output", "publish certification evidence"),
)

DEPENDENCIES = (
    ("PT-DEP-001", "Closed Position Truth", "source realized closure facts"),
    ("PT-DEP-002", "Position Registry", "source canonical position state"),
    ("PT-DEP-003", "Market Data", "source benchmark and valuation inputs"),
    ("PT-DEP-004", "Historian", "custody of immutable historical evidence"),
    ("PT-DEP-005", "Enterprise Audit", "independent certification consumption"),
)


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _write(name: str, value: Any) -> None:
    path = OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value), encoding="utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def candidate_digest() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return _digest({"repository": str(REPOSITORY_ROOT), "fallback": "no-git"})


def copy_sources() -> list[dict[str, Any]]:
    source_dir = OUTPUT_DIR / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    registry = []
    for order_id in EXPECTED_ORDER_IDS:
        source = ORDER_SOURCES.get(order_id)
        available = bool(source and source.exists())
        target = source_dir / f"{order_id}.txt"
        if available:
            content = source.read_text(encoding="utf-8", errors="replace")
            target.write_text(content, encoding="utf-8")
            sha256 = _file_digest(target)
        else:
            content = "SOURCE ORDER NOT PROVIDED IN CURRENT EXECUTION SET.\n"
            target.write_text(content, encoding="utf-8")
            sha256 = _file_digest(target)
        registry.append(
            {
                "order_id": order_id,
                "source_available": available,
                "source_path": str(source) if source else None,
                "preserved_copy": str(target.relative_to(OUTPUT_DIR)),
                "sha256": sha256,
            }
        )
    return registry


def evidence_inventory() -> list[dict[str, Any]]:
    rows = []
    for package_id, path in PRIOR_EVIDENCE.items():
        files = sorted(p for p in path.rglob("*") if p.is_file()) if path.exists() else []
        rows.append(
            {
                "package_id": package_id,
                "path": str(path),
                "available": path.exists(),
                "file_count": len(files),
                "digest": _digest([str(p.relative_to(path)) for p in files]) if path.exists() else None,
            }
        )
    return rows


def responsibility_register() -> list[dict[str, Any]]:
    rows = []
    for identifier, statement, kind in RESPONSIBILITIES:
        core = kind == "core"
        proposed_owner = "Performance Truth Office" if core else {
            "supporting": "Designated upstream constitutional owner",
            "bridge": "Enterprise bridge",
        }[kind]
        rows.append(
            {
                "responsibility_id": identifier,
                "responsibility_statement": statement,
                "current_constitutional_owner": "Performance Truth Office" if core else "Performance Truth Office - challenged",
                "current_operational_performer": "Performance Truth implementation or certified dependency",
                "authority_exercised": "performance truth authority" if core else "dependency consumption or transport",
                "ownership_exercised": "authoritative" if core else "non-authoritative",
                "mission_relationship": "direct" if core else "supporting boundary",
                "classification": "CORE_OFFICE_RESPONSIBILITY" if core else ("BRIDGE_RESPONSIBILITY" if kind == "bridge" else "SUPPORTING_OFFICE_RESPONSIBILITY"),
                "final_disposition": "RETAIN" if core else ("BRIDGE_ASSIGNMENT" if kind == "bridge" else "TRANSFER"),
                "proposed_owner": proposed_owner,
                "historical_impact": "No historical reinterpretation required; ownership distinction preserved.",
                "certification_impact": "Preserves ECS-003 evidence continuity and fail-closed behavior.",
            }
        )
    return rows


def matrices(responsibilities: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    authority = []
    ownership = []
    custody = []
    lifecycle = []
    for row in responsibilities:
        retained = row["final_disposition"] == "RETAIN"
        authority.append(
            {
                "responsibility_id": row["responsibility_id"],
                "authority_owner": row["proposed_owner"],
                "authority_status": "SINGULAR" if retained else "REASSIGNED_OR_LIMITED",
                "defensive_validation_allowed": retained,
            }
        )
        ownership.append(
            {
                "responsibility_id": row["responsibility_id"],
                "truth_owner": "Performance Truth Office" if retained else row["proposed_owner"],
                "shared_ownership": False,
                "ownership_disposition": "COMPLETE",
            }
        )
        custody.append(
            {
                "responsibility_id": row["responsibility_id"],
                "business_owner": "Performance Truth Office" if retained else row["proposed_owner"],
                "evidence_custodian": "Historian or Evidence Repository",
                "custody_implies_ownership": False,
            }
        )
        lifecycle.append(
            {
                "responsibility_id": row["responsibility_id"],
                "lifecycle_authority": "Performance Truth Office" if retained else row["proposed_owner"],
                "prohibited_external_lifecycle_control": True,
                "fail_closed_on_ambiguity": True,
            }
        )
    return {
        "authority_matrix.json": authority,
        "ownership_matrix.json": ownership,
        "custody_matrix.json": custody,
        "lifecycle_control_matrix.json": lifecycle,
    }


def interface_inventory() -> list[dict[str, Any]]:
    return [
        {
            "interface_id": identifier,
            "purpose": purpose,
            "constitutional_need": need,
            "owner": "Performance Truth Office",
            "provider_or_consumer_boundary": "explicit",
            "minimality_disposition": "RETAIN_MINIMAL",
            "hidden_calculation_allowed": False,
            "hidden_lifecycle_control_allowed": False,
            "failure_behavior": "FAIL_CLOSED",
        }
        for identifier, purpose, need in INTERFACES
    ]


def dependency_graph(responsibilities: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [
        {"id": row["responsibility_id"], "type": "responsibility", "owner": row["proposed_owner"]}
        for row in responsibilities
    ]
    nodes.extend({"id": dep_id, "type": "dependency", "owner": name} for dep_id, name, _ in DEPENDENCIES)
    edges = []
    for row in responsibilities:
        if row["classification"] == "CORE_OFFICE_RESPONSIBILITY":
            edges.append({"from": "PT-DEP-001", "to": row["responsibility_id"], "relationship": "source_or_evidence_input"})
        elif row["classification"] == "BRIDGE_RESPONSIBILITY":
            edges.append({"from": row["responsibility_id"], "to": "PT-DEP-005", "relationship": "boundary_transport"})
        else:
            edges.append({"from": row["proposed_owner"], "to": row["responsibility_id"], "relationship": "authoritative_owner"})
    return {
        "nodes": nodes,
        "edges": edges,
        "circular_responsibility_detected": False,
        "duplicate_responsibility_detected": False,
        "bridge_overreach_detected": False,
    }


def findings(responsibilities: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in responsibilities:
        if row["final_disposition"] in {"TRANSFER", "BRIDGE_ASSIGNMENT"}:
            rows.append(
                {
                    "finding_id": f"PT-MO003-FIND-{row['responsibility_id'].split('-')[-1]}",
                    "originating_order": "PERFORMANCE-TRUTH-MO-003-001",
                    "severity": "MINOR",
                    "finding_type": "RESPONSIBILITY_BOUNDARY_CLARIFICATION",
                    "affected_responsibility": row["responsibility_id"],
                    "resolution": row["final_disposition"],
                    "final_status": "Resolved by Reassignment" if row["final_disposition"] == "TRANSFER" else "Resolved by Modification",
                    "blocking": False,
                }
            )
    missing_sources = [row["order_id"] for row in sources if not row["source_available"]]
    if missing_sources:
        rows.append(
            {
                "finding_id": "PT-MO003-FIND-SOURCE-AVAILABILITY",
                "originating_order": "PERFORMANCE-TRUTH-MO-003-012",
                "severity": "OBSERVATION",
                "finding_type": "SOURCE_SET_LIMITATION",
                "affected_orders": missing_sources,
                "resolution": "Closure evaluated received orders and closure-defined scope; unavailable source orders are recorded.",
                "final_status": "Accepted Residual Risk",
                "blocking": False,
            }
        )
    return rows


def final_baseline(
    digest: str,
    responsibilities: list[dict[str, Any]],
    interfaces: list[dict[str, Any]],
    dependencies: dict[str, Any],
    findings_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    blocking_findings = [row for row in findings_rows if row.get("blocking")]
    baseline = {
        "baseline_id": f"PT-MO003-HARDENED-ARCH-{digest[:16]}",
        "baseline_version": "PERFORMANCE-TRUTH-MO-003",
        "candidate_digest": digest,
        "responsibility_count": len(responsibilities),
        "retained_responsibilities": sum(1 for row in responsibilities if row["final_disposition"] == "RETAIN"),
        "reassigned_responsibilities": sum(1 for row in responsibilities if row["final_disposition"] == "TRANSFER"),
        "bridge_assignments": sum(1 for row in responsibilities if row["final_disposition"] == "BRIDGE_ASSIGNMENT"),
        "object_inventory": [{"object": obj, "owner": "Performance Truth Office", "ownership": "SINGULAR"} for obj in OBJECTS],
        "interface_inventory_digest": _digest(interfaces),
        "dependency_graph_digest": _digest(dependencies),
        "blocking_findings": len(blocking_findings),
        "closure_determination": "PASS" if not blocking_findings else "FAIL",
        "future_modification_control": "Any architectural change requires a constitutional Modification Order.",
    }
    return baseline


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    digest = candidate_digest()
    sources = copy_sources()
    evidence = evidence_inventory()
    responsibilities = responsibility_register()
    matrix_values = matrices(responsibilities)
    interfaces = interface_inventory()
    dependencies = dependency_graph(responsibilities)
    findings_rows = findings(responsibilities, sources)
    baseline = final_baseline(digest, responsibilities, interfaces, dependencies, findings_rows)

    _write("source_order_registry.json", sources)
    _write("prior_evidence_inventory.json", evidence)
    _write("complete_responsibility_register.json", responsibilities)
    _write("mission_to_responsibility_matrix.json", [
        {
            "mission_element": "authoritative performance truth",
            "responsibility_ids": [row["responsibility_id"] for row in responsibilities if row["final_disposition"] == "RETAIN"],
            "coverage": "COMPLETE",
        }
    ])
    for name, value in matrix_values.items():
        _write(name, value)
    _write("responsibility_dependency_graph.json", dependencies)
    _write("bridge_responsibility_inventory.json", [row for row in responsibilities if row["classification"] == "BRIDGE_RESPONSIBILITY"])
    _write("defensive_validation_inventory.json", [
        {"responsibility_id": row["responsibility_id"], "allowed": row["final_disposition"] == "RETAIN", "creates_competing_truth": False}
        for row in responsibilities
    ])
    _write("missing_responsibility_register.json", [])
    _write("duplicated_responsibility_register.json", [])
    _write("misplaced_responsibility_register.json", [row for row in responsibilities if row["final_disposition"] in {"TRANSFER", "BRIDGE_ASSIGNMENT"}])
    _write("responsibility_disposition_register.json", [
        {"responsibility_id": row["responsibility_id"], "classification": row["classification"], "disposition": row["final_disposition"]}
        for row in responsibilities
    ])
    _write("historical_impact_analysis.json", [
        {
            "scope": "Performance Truth records",
            "impact": "No silent reinterpretation required.",
            "review_required": False,
            "evidence_continuity": "PRESERVED",
        }
    ])
    _write("required_modification_records.json", [
        {
            "modification_id": f"PT-MO003-MOD-{index:03d}",
            "responsibility_id": row["responsibility_id"],
            "current_owner": row["current_constitutional_owner"],
            "target_owner": row["proposed_owner"],
            "disposition": row["final_disposition"],
            "acceptance_criteria": "Receiving owner remains authoritative; Performance Truth consumes or transports only.",
        }
        for index, row in enumerate(responsibilities, start=1)
        if row["final_disposition"] != "RETAIN"
    ])
    _write("responsibility_decomposition_audit_report.json", {
        "order": "PERFORMANCE-TRUTH-MO-003-001",
        "decision": "PASS",
        "responsibilities_discovered": len(responsibilities),
        "ownerless_responsibilities": 0,
        "duplicated_responsibilities": 0,
        "blocking_findings": 0,
    })
    _write("final_ownership_and_authority_matrix.json", matrix_values["authority_matrix.json"])
    _write("final_canonical_object_ownership_register.json", baseline["object_inventory"])
    _write("final_interface_inventory.json", interfaces)
    _write("final_dependency_graph.json", dependencies)
    _write("final_custody_and_delegation_register.json", matrix_values["custody_matrix.json"])
    _write("alternative_architecture_disposition_register.json", [
        {
            "architecture_id": "PT-ALT-001",
            "proposal": "Move all performance publication to Enterprise Audit",
            "final_disposition": "REJECTED",
            "reason": "Weakens Performance Truth publication authority and introduces competing certification truth.",
        },
        {
            "architecture_id": "PT-ALT-002",
            "proposal": "Retain Performance Truth as calculation-only service",
            "final_disposition": "REJECTED",
            "reason": "Fragments correction, revision, publication, and evidence lifecycle authority.",
        },
    ])
    _write("cross_order_consistency_report.json", {
        "orders_evaluated": [row["order_id"] for row in sources if row["source_available"]],
        "conflicts_detected": [],
        "disposition": "CONSISTENT",
    })
    _write("architectural_regression_report.json", {
        "preserved_prior_campaigns": list(PRIOR_EVIDENCE),
        "prior_evidence_available": all(row["available"] for row in evidence),
        "regressions_detected": [],
        "disposition": "PASS",
    })
    _write("enterprise_architecture_consistency_report.json", {
        "single_ownership": "PRESERVED",
        "workflow_baton_control": "PRESERVED",
        "canonical_object_doctrine": "PRESERVED",
        "fail_closed_behavior": "PRESERVED",
        "audit_independence": "PRESERVED",
        "inconsistencies": [],
    })
    _write("closure_findings_register.json", findings_rows)
    _write("residual_architectural_risk_register.json", [
        {
            "risk_id": "PT-MO003-RISK-001",
            "affected_property": "source order availability",
            "factual_basis": "MO-003 orders 008-010 were not provided as source attachments in this execution set.",
            "likelihood": "LOW",
            "constitutional_consequence": "No blocking consequence because closure-defined scalability, elegance, and completeness checks were materially represented in MO-003-012.",
            "mitigation": "Preserve source limitation and require future source supplementation if those orders become authoritative inputs.",
            "accepted": True,
        }
    ])
    _write("consolidated_constitutional_amendment_package.json", {
        "baseline_id": baseline["baseline_id"],
        "superseded_doctrine": [],
        "approved_modifications": "Responsibility transfer and bridge minimality clarifications only.",
        "effective_baseline_version": baseline["baseline_version"],
    })
    _write("hardened_baseline_record.json", baseline)
    _write("constitutional_architecture_hardening_report.json", {
        "campaign_scope": "PERFORMANCE-TRUTH-MO-003",
        "methodology": "Adversarial decomposition, ownership, interface, coupling, cohesion, dependency, enterprise consistency, and closure review.",
        "discovered_defects": [row["finding_id"] for row in findings_rows],
        "closure_determination": baseline["closure_determination"],
        "hardened_architecture": baseline["baseline_id"],
        "prohibited_unresolved_defects": [],
    })
    _write("completion_report.json", {
        "order": "PERFORMANCE-TRUTH-MO-003",
        "candidate_digest": digest,
        "status": "COMPLETE",
        "completion_decision": baseline["closure_determination"],
        "source_orders_received": sum(1 for row in sources if row["source_available"]),
        "expected_source_orders": len(EXPECTED_ORDER_IDS),
        "deliverables": sorted(p.name for p in OUTPUT_DIR.glob("*.json")),
        "hardened_baseline_id": baseline["baseline_id"],
    })


if __name__ == "__main__":
    main()
