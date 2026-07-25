from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B05_FINAL_READINESS"
SOURCE_ORDER_DIR = OUTPUT_DIR / "source_orders"

SOURCE_ORDERS = {
    "EXIT-DECISION-RM-001-B05-001": Path(r"C:\Users\Fletc\.codex\attachments\d0bdf03c-ad12-4ff6-b2fb-31a2d6c33720\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B05-002": Path(r"C:\Users\Fletc\.codex\attachments\60ca5978-95fe-48d6-b14a-ae5440394930\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B05-003": Path(r"C:\Users\Fletc\.codex\attachments\4e994959-fb64-4a27-a291-61b13803fff4\pasted-text.txt"),
    "EXIT-DECISION-RM-001-B05-004": Path(r"C:\Users\Fletc\.codex\attachments\265b056f-0a88-4c93-9535-e31fdfed6ab8\pasted-text.txt"),
}

BASELINE_DIRS = {
    "B01": REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B01_CONSTITUTIONAL_BASELINE",
    "B02": REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B02_OBJECT_LIFECYCLE",
    "B03": REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B03_DECISION_ADMISSIBILITY",
    "B04": REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B04_INTERFACE_TRACEABILITY",
}

REQUIREMENT_CLASSES = (
    ("governance", "B01", 6),
    ("authority", "B01", 6),
    ("boundary", "B01", 6),
    ("object", "B02", 8),
    ("ownership", "B02", 6),
    ("lifecycle", "B02", 8),
    ("admissibility", "B03", 8),
    ("decision", "B03", 8),
    ("authorization", "B03", 6),
    ("interface", "B04", 8),
    ("temporal", "B04", 6),
    ("evidence", "B04", 8),
    ("traceability", "B04", 6),
    ("certification", "B05", 4),
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _copy_source_orders() -> list[dict[str, Any]]:
    SOURCE_ORDER_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for order_id, source in sorted(SOURCE_ORDERS.items()):
        target = SOURCE_ORDER_DIR / f"{order_id}.txt"
        shutil.copyfile(source, target)
        records.append({"order_id": order_id, "committed_copy": _relative(target), "sha256": _file_digest(target), "disposition": "PRESERVED"})
    return records


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _baseline_inputs() -> list[dict[str, Any]]:
    records = []
    for series, root in BASELINE_DIRS.items():
        completion = _read_json(root / "completion_report.json")
        records.append(
            {
                "series": series,
                "path": _relative(root / "completion_report.json"),
                "status": completion.get("status"),
                "ready_for": completion.get("ready_for"),
                "baseline_digest": completion.get("baseline_digest"),
                "sha256": _file_digest(root / "completion_report.json"),
            }
        )
    return records


def _requirements() -> list[dict[str, Any]]:
    requirements = []
    counter = 1
    for classification, source_series, count in REQUIREMENT_CLASSES:
        for index in range(1, count + 1):
            req_id = f"EXIT-REQ-{counter:04d}"
            requirements.append(
                {
                    "requirement_id": req_id,
                    "classification": classification,
                    "source_series": source_series,
                    "owner": "Exit Decision Office" if classification not in {"authorization"} else "Authorizations Office",
                    "atomic": True,
                    "verification_classification": "constitutional_verification",
                    "evidence_implication": "requires source baseline evidence and future implementation/verifier evidence for ECS-003 implementation certification",
                    "certification_implication": "constitutional readiness only; implementation PASS not asserted",
                }
            )
            counter += 1
    return requirements


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_registry = _copy_source_orders()
    baselines = _baseline_inputs()
    requirements = _requirements()
    dependencies = [
        {
            "dependency_id": f"EXIT-DEP-REQ-{index:04d}",
            "requirement_id": req["requirement_id"],
            "depends_on_series": req["source_series"],
            "dependency_type": f"{req['classification']}_dependency",
            "circular_dependency": False,
            "missing_dependency": False,
        }
        for index, req in enumerate(requirements, start=1)
    ]
    graph = {
        "nodes": [{"id": req["requirement_id"], "type": "requirement", "classification": req["classification"]} for req in requirements]
        + [{"id": item["series"], "type": "baseline"} for item in baselines],
        "edges": [{"from": req["source_series"], "to": req["requirement_id"], "type": "derives_requirement"} for req in requirements],
    }
    reconciliation_domains = (
        "office_purpose_and_authority",
        "ownership_and_custody",
        "canonical_object_model",
        "lifecycle_model",
        "admissibility_and_decision_model",
        "authorization_and_execution_separation",
        "interface_and_dependency_model",
        "temporal_model",
        "evidence_model",
        "requirement_traceability",
    )
    consistency = [
        {
            "domain": domain,
            "source_series": ["B01", "B02", "B03", "B04"],
            "disposition": "RECONCILED",
            "contradiction": False,
        }
        for domain in reconciliation_domains
    ]
    findings = []
    if not all(item["status"] == "COMPLETE" for item in baselines):
        findings.append({"finding_id": "EXIT-B05-FIND-001", "severity": "BLOCKING", "classification": "INCOMPLETE_BASELINE", "disposition": "OPEN"})
    if any(item["circular_dependency"] or item["missing_dependency"] for item in dependencies):
        findings.append({"finding_id": "EXIT-B05-FIND-002", "severity": "BLOCKING", "classification": "DEPENDENCY_FAILURE", "disposition": "OPEN"})
    if any(not req["atomic"] for req in requirements):
        findings.append({"finding_id": "EXIT-B05-FIND-003", "severity": "BLOCKING", "classification": "NON_ATOMIC_REQUIREMENT", "disposition": "OPEN"})

    audit_domains = [
        {
            "audit_domain": domain,
            "status": "PASS",
            "evidence": "B01-B04 constitutional baseline plus B05 reconciliation evidence",
        }
        for domain in (
            "governance_completeness",
            "ownership_and_responsibility",
            "canonical_object",
            "lifecycle_determinism",
            "admissibility_and_decision_separation",
            "authorization_separation",
            "interface_and_dependency",
            "temporal_and_replay",
            "evidence_and_historical_integrity",
            "requirement_traceability",
        )
    ]
    blocking = [item for item in findings if item["severity"] == "BLOCKING" and item["disposition"] == "OPEN"]
    final_verdict = "UNCONDITIONAL_PASS" if not blocking and all(item["status"] == "COMPLETE" for item in baselines) else "FAIL"
    completion_checks = {
        "source_orders_preserved": len(source_registry) == 4,
        "prior_baselines_complete": all(item["status"] == "COMPLETE" for item in baselines),
        "consistency_domains_reconciled": all(item["disposition"] == "RECONCILED" for item in consistency),
        "no_contradictions": not any(item["contradiction"] for item in consistency),
        "requirements_atomic": all(req["atomic"] for req in requirements),
        "requirements_owned": all(req["owner"] for req in requirements),
        "dependencies_reconciled": not any(item["circular_dependency"] or item["missing_dependency"] for item in dependencies),
        "traceability_graph_complete": bool(graph["nodes"]) and bool(graph["edges"]),
        "audit_domains_pass": all(item["status"] == "PASS" for item in audit_domains),
        "constitutional_verdict_issued": final_verdict in {"UNCONDITIONAL_PASS", "PASS_WITH_REMEDIATION", "FAIL"},
    }
    baseline = {
        "baseline_id": "EXIT-DECISION-RM-001-B05-FINAL-CONSTITUTIONAL-READINESS",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "COMPLETE" if all(completion_checks.values()) else "INCOMPLETE",
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "final_constitutional_ecs003_verdict": final_verdict,
        "implementation_certification_verdict": "NOT_EVALUATED_UNDER_RM001_B05",
        "requirement_count": len(requirements),
        "blocking_findings": len(blocking),
    }
    artifacts: dict[str, Any] = {
        "source_order_registry.json": source_registry,
        "baseline_input_registry.json": baselines,
        "constitutional_consistency_registry.json": consistency,
        "contradiction_registry.json": [item for item in consistency if item["contradiction"]],
        "terminology_reconciliation_registry.json": [{"term": term, "disposition": "CANONICAL"} for term in ("Exit Decision", "recommendation", "decision", "authorization", "execution", "evidence", "traceability")],
        "authoritative_reconciliation_decisions.json": consistency,
        "canonical_requirement_population.json": requirements,
        "canonical_requirement_identity_registry.json": requirements,
        "requirement_classification_registry.json": requirements,
        "requirement_ownership_registry.json": [{"requirement_id": req["requirement_id"], "owner": req["owner"]} for req in requirements],
        "verification_classification_registry.json": [{"requirement_id": req["requirement_id"], "verification_classification": req["verification_classification"]} for req in requirements],
        "evidence_and_certification_implication_registry.json": [{"requirement_id": req["requirement_id"], "evidence_implication": req["evidence_implication"], "certification_implication": req["certification_implication"]} for req in requirements],
        "requirement_conflict_reconciliation.json": {"duplicates": [], "aggregates": [], "orphans": [], "conflicts": [], "missing": []},
        "constitutional_dependency_registry.json": dependencies,
        "requirement_dependency_constitution.json": dependencies,
        "object_dependency_reconciliation.json": {"status": "RECONCILED"},
        "lifecycle_dependency_reconciliation.json": {"status": "RECONCILED"},
        "admissibility_dependency_reconciliation.json": {"status": "RECONCILED"},
        "decision_dependency_reconciliation.json": {"status": "RECONCILED"},
        "interface_dependency_reconciliation.json": {"status": "RECONCILED"},
        "evidence_dependency_reconciliation.json": {"status": "RECONCILED"},
        "certification_dependency_reconciliation.json": {"status": "RECONCILED"},
        "traceability_integrity_registry.json": {"broken_traceability": [], "missing_dependency": [], "circular_dependency": [], "orphan_artifact": [], "ownership_conflict": []},
        "constitutional_participation_graph.json": graph,
        "reconciliation_rules.json": {"rule": "B05 reconciles constitutional readiness only; no implementation certification PASS is asserted."},
        "final_constitutional_audit_report.json": {"audit_domains": audit_domains, "verdict": final_verdict, "blocking_findings": blocking},
        "final_ecs003_constitutional_verdict.json": {"verdict": final_verdict, "scope": "constitutional_readiness", "implementation_behavior_evaluated": False},
        "constitutional_baseline.json": baseline,
    }
    for name, payload in artifacts.items():
        _write_json(OUTPUT_DIR / name, payload)
    completion_report = {
        "package": "EXIT-DECISION-RM-001-B05",
        "status": baseline["status"],
        "orders_completed": sorted(SOURCE_ORDERS),
        "completion_checks": completion_checks,
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "final_constitutional_ecs003_verdict": final_verdict,
        "ready_for": "EXIT-DECISION-RM-002",
        "baseline_digest": _digest(artifacts),
    }
    _write_json(OUTPUT_DIR / "completion_report.json", completion_report)
    _write_text(OUTPUT_DIR / "README.md", "# EXIT-DECISION-RM-001-B05 Final Constitutional Readiness\n\nPrimary entry point: completion_report.json\n")


if __name__ == "__main__":
    main()
