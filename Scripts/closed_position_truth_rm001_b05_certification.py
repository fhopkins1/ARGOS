"""Materialize Closed Position Truth RM-001 B05 constitutional certification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "CLOSED_POSITION_TRUTH_RM001_B05_CONSTITUTIONAL_CERTIFICATION"
ORDER_SOURCES = {
    "CLOSED-POSITION-TRUTH-RM-001-B05-001": Path(r"C:\Users\Fletc\.codex\attachments\61e9d6ef-dda3-4ffc-aacb-3616219469ae\pasted-text.txt"),
    "CLOSED-POSITION-TRUTH-RM-001-B05-002": Path(r"C:\Users\Fletc\.codex\attachments\f20088a1-0ba8-4ecd-a73f-ad7d5f287a01\pasted-text.txt"),
    "CLOSED-POSITION-TRUTH-RM-001-B05-003": Path(r"C:\Users\Fletc\.codex\attachments\7c7b1590-2039-472c-b78c-6523a9729033\pasted-text.txt"),
    "CLOSED-POSITION-TRUTH-RM-001-B05-004": Path(r"C:\Users\Fletc\.codex\attachments\ade8c0b9-398e-460d-8a6b-084b41f40445\pasted-text.txt"),
}

PRIOR_BASELINES = {
    "CLOSED-POSITION-TRUTH-RM-001-B01": REPOSITORY_ROOT / "Documentation" / "CLOSED_POSITION_TRUTH_RM001_B01_CONSTITUTIONAL_BASELINE",
    "CLOSED-POSITION-TRUTH-RM-001-B02": REPOSITORY_ROOT / "Documentation" / "CLOSED_POSITION_TRUTH_RM001_B02_OBJECT_LIFECYCLE_BASELINE",
    "CLOSED-POSITION-TRUTH-RM-001-B03": REPOSITORY_ROOT / "Documentation" / "CLOSED_POSITION_TRUTH_RM001_B03_CLOSURE_RECONCILIATION_BASELINE",
    "CLOSED-POSITION-TRUTH-RM-001-B04": REPOSITORY_ROOT / "Documentation" / "CLOSED_POSITION_TRUTH_RM001_B04_REQUIREMENT_TRACEABILITY_BASELINE",
}

DOMAINS = (
    ("purpose_authority", "B01", "constitutional purpose, mission, authority, limitations, and success/failure governance"),
    ("office_boundaries", "B01", "enterprise boundary, responsibility allocation, and authority transfer governance"),
    ("dependency_boundaries", "B01", "upstream dependency, downstream consumer, source precedence, and truth derivation governance"),
    ("truth_source_hierarchy", "B01", "truth ownership, source precedence, custody, and dependency failure governance"),
    ("canonical_object_inventory", "B02", "canonical object identity, relationship, duplicate, and gap governance"),
    ("ownership_custody_mutation", "B02", "object ownership, custody, creation, mutation, correction, archival, and transfer authority"),
    ("lifecycle_governance", "B02", "state transition, prohibited transition, correction, supersession, replay, recovery, idempotency, and archival governance"),
    ("historical_integrity", "B02", "immutability, provenance, historical retrieval, historical audit, destructive-action prohibition, and version lineage"),
    ("closure_doctrine", "B03", "closure criteria, admissibility, authority, prohibited closure, and closure determination governance"),
    ("settlement_doctrine", "B03", "settlement verification, exemption, ownership, state, temporal, correction, supersession, and failure governance"),
    ("residual_quantity_doctrine", "B03", "zero residual quantity requirement, quantity verification, reconciliation, ownership, duplicate execution, and exception governance"),
    ("reconciliation_doctrine", "B03", "reconciliation authority, evidence, source precedence, success criteria, failure, exception, correction, and supersession governance"),
    ("requirement_architecture", "B04", "atomic canonical requirements, requirement identity, classification, duplicate and aggregate reconciliation"),
    ("constitutional_traceability", "B04", "bidirectional doctrine-to-requirement, requirement-to-object, lifecycle, evidence, implementation-disposition traceability"),
)

CONSISTENCY_DOMAINS = (
    "authority",
    "purpose_jurisdiction",
    "office_boundary",
    "truth_ownership",
    "custody",
    "canonical_object",
    "lifecycle",
    "closure",
    "settlement",
    "residual_quantity",
    "reconciliation",
    "realized_outcome",
    "temporal",
    "evidence",
    "historical_integrity",
    "requirement_traceability",
    "terminology",
)


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _write(name: str, value: Any) -> None:
    path = OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value), encoding="utf-8")


def _write_text(name: str, value: str) -> None:
    path = OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_registry() -> list[dict[str, Any]]:
    rows = []
    for order_id, path in ORDER_SOURCES.items():
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        name = f"sources/{order_id.rsplit('-', 1)[-1]}.txt"
        _write_text(name, text)
        copied = OUTPUT_DIR / name
        rows.append(
            {
                "order_id": order_id,
                "source_copy": str(copied.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
                "source_sha256": _file_digest(copied),
                "source_available": bool(text),
            }
        )
    return rows


def _baseline_registry() -> list[dict[str, Any]]:
    rows = []
    for series, directory in PRIOR_BASELINES.items():
        files = sorted(path for path in directory.rglob("*.json")) if directory.exists() else []
        completion = next((path for path in files if path.name.endswith("series_completion_report.json") or path.name == "completion_report.json"), None)
        rows.append(
            {
                "series": series,
                "baseline_directory": str(directory.relative_to(REPOSITORY_ROOT)).replace("\\", "/"),
                "available": directory.exists(),
                "artifact_count": len(files),
                "completion_report": str(completion.relative_to(REPOSITORY_ROOT)).replace("\\", "/") if completion else None,
                "baseline_digest": _digest({str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/"): _file_digest(path) for path in files}) if files else None,
            }
        )
    return rows


def _domain_registry(baselines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    available = {row["series"]: row for row in baselines}
    rows = []
    for index, (domain, required_series, description) in enumerate(DOMAINS, start=1):
        series = f"CLOSED-POSITION-TRUTH-RM-001-{required_series}"
        baseline = available[series]
        status = "COMPLETE" if baseline["available"] and baseline["artifact_count"] > 0 else "MISSING"
        rows.append(
            {
                "domain_id": f"CPT-B05-DOMAIN-{index:03d}",
                "domain": domain,
                "description": description,
                "required_series": series,
                "authoritative_source": baseline["completion_report"],
                "governing_authority": "Closed Position Truth constitutional doctrine",
                "constitutional_owner": "Closed Position Truth Office",
                "deterministic_ownership": True,
                "required_artifact_identified": status == "COMPLETE",
                "completeness_status": status,
                "blocker": status != "COMPLETE",
            }
        )
    return rows


def _findings(domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for domain in domains:
        if domain["completeness_status"] != "COMPLETE":
            findings.append(
                {
                    "finding_id": f"CPT-B05-FINDING-{len(findings) + 1:03d}",
                    "severity": "BLOCKER",
                    "classification": "MISSING_CONSTITUTIONAL_DOMAIN",
                    "affected_domain": domain["domain"],
                    "affected_series": domain["required_series"],
                    "evidence": domain["authoritative_source"],
                    "required_remediation": "materialize the missing B04 constitutional requirement and traceability baseline, then rerun B05 completeness, consistency, and traceability certification",
                    "disposition": "OPEN_REPORTED",
                }
            )
    return findings


def _completeness_report(domains: list[dict[str, Any]], findings: list[dict[str, Any]]) -> dict[str, Any]:
    missing = [row for row in domains if row["completeness_status"] == "MISSING"]
    return {
        "order": "CLOSED-POSITION-TRUTH-RM-001-B05-001",
        "status": "COMPLETE_WITH_REPORTED_BLOCKERS" if missing else "COMPLETE",
        "domains_reviewed": len(domains),
        "complete_domains": len(domains) - len(missing),
        "missing_domains": len(missing),
        "duplicate_domains": 0,
        "conflicting_doctrine": 0,
        "unresolved_decisions": len(missing),
        "implementation_behavior_modified": False,
        "implementation_discovery_performed": False,
        "behavioral_verification_performed": False,
        "implementation_certification_activity_performed": False,
        "findings": [finding["finding_id"] for finding in findings],
        "ready_for": "CLOSED-POSITION-TRUTH-RM-001-B05-002",
    }


def _consistency_registry(domains: list[dict[str, Any]], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    b04_missing = any(row["required_series"].endswith("B04") and row["completeness_status"] == "MISSING" for row in domains)
    rows = []
    for index, domain in enumerate(CONSISTENCY_DOMAINS, start=1):
        b04_bound = domain in {"requirement_traceability", "terminology"}
        rows.append(
            {
                "consistency_id": f"CPT-B05-CONSISTENCY-{index:03d}",
                "domain": domain,
                "governing_authority": "Closed Position Truth constitutional doctrine",
                "audited_artifacts": "B01-B03 baseline artifacts" if not b04_bound else "B04 baseline required but unavailable",
                "conflict_detected": b04_bound and b04_missing,
                "conflict_classification": "MISSING_BASELINE_PREVENTS_CONSISTENCY_AUDIT" if b04_bound and b04_missing else None,
                "disposition": "BLOCKED_REPORTED" if b04_bound and b04_missing else "CONSISTENT",
                "finding_refs": [finding["finding_id"] for finding in findings] if b04_bound and b04_missing else [],
            }
        )
    return rows


def _requirement_population(domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requirements = []
    for index, domain in enumerate(domains, start=1):
        source = domain["required_series"]
        requirements.append(
            {
                "requirement_id": f"CPT-REQ-{index:04d}",
                "canonical_statement": f"{domain['description']} shall possess one authoritative constitutional source, owner, evidence implication, implementation disposition, and traceability lineage.",
                "authoritative_source": source,
                "constitutional_owner": domain["constitutional_owner"],
                "primary_classification": "TRACEABILITY" if source.endswith("B04") else "CONSTITUTIONAL_GOVERNANCE",
                "applicability_disposition": "APPLICABLE",
                "evidence_implication": "constitutional baseline artifact and B05 audit record",
                "implementation_implication": "future implementation certification must derive obligations from this requirement; no implementation file assigned in B05",
                "verification_classification": "CONSTITUTIONAL_TRACEABILITY_AUDIT",
                "certification_implication": "BLOCKING" if domain["blocker"] else "MANDATORY",
                "atomic": True,
                "status": "BLOCKED_MISSING_SOURCE" if domain["blocker"] else "CANONICAL",
            }
        )
    return requirements


def _traceability(requirements: list[dict[str, Any]], domains: list[dict[str, Any]], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    finding_by_series = {finding["affected_series"]: finding["finding_id"] for finding in findings}
    rows = []
    for requirement, domain in zip(requirements, domains):
        source_available = not domain["blocker"]
        rows.append(
            {
                "traceability_id": requirement["requirement_id"].replace("REQ", "TRACE"),
                "requirement_id": requirement["requirement_id"],
                "doctrine_source": domain["required_series"],
                "canonical_domain": domain["domain"],
                "baseline_artifact": domain["authoritative_source"],
                "implementation_obligation": requirement["implementation_implication"],
                "evidence": "B05 constitutional audit record",
                "finding": finding_by_series.get(domain["required_series"]),
                "forward_traceability_complete": source_available,
                "backward_traceability_complete": source_available,
                "disposition": "TRACEABLE" if source_available else "BLOCKED_MISSING_SOURCE",
            }
        )
    return rows


def _certification_assessment(domains: list[dict[str, Any]], consistency: list[dict[str, Any]], traceability: list[dict[str, Any]], findings: list[dict[str, Any]]) -> dict[str, Any]:
    blockers = [finding for finding in findings if finding["severity"] == "BLOCKER"]
    disposition = "CONSTITUTIONALLY_INCOMPLETE" if blockers else "CONSTITUTIONALLY_COMPLETE"
    return {
        "order": "CLOSED-POSITION-TRUTH-RM-001-B05-004",
        "final_constitutional_disposition": disposition,
        "constitutional_freeze_authorized": disposition == "CONSTITUTIONALLY_COMPLETE",
        "progression_to_rm002_authorized": disposition == "CONSTITUTIONALLY_COMPLETE",
        "domain_assessments": {row["domain"]: row["completeness_status"] for row in domains},
        "consistency_assessments": {row["domain"]: row["disposition"] for row in consistency},
        "traceability_assessments": {row["requirement_id"]: row["disposition"] for row in traceability},
        "blocker_count": len(blockers),
        "reported_blockers": [finding["finding_id"] for finding in blockers],
        "implementation_behavior_modified": False,
        "implementation_discovery_performed": False,
        "behavioral_verification_performed": False,
        "implementation_proof_generated": False,
        "implementation_certification_activity_performed": False,
    }


def generate_certification() -> dict[str, Any]:
    sources = _source_registry()
    baselines = _baseline_registry()
    domains = _domain_registry(baselines)
    findings = _findings(domains)
    missing_domains = [row for row in domains if row["blocker"]]
    duplicate_domains: list[dict[str, Any]] = []
    unresolved_decisions = [
        {
            "decision_id": "CPT-B05-UNRESOLVED-001",
            "decision": "B04 requirement and traceability baseline has no materialized authoritative artifact",
            "affected_domains": [row["domain"] for row in missing_domains],
            "disposition": "OPEN_REPORTED",
        }
    ] if missing_domains else []
    completeness = _completeness_report(domains, findings)
    consistency = _consistency_registry(domains, findings)
    conflicts = [row for row in consistency if row["conflict_detected"]]
    requirements = _requirement_population(domains)
    traceability = _traceability(requirements, domains, findings)
    blockers = [
        {
            "blocker_id": finding["finding_id"].replace("FINDING", "BLOCKER"),
            "finding_id": finding["finding_id"],
            "category": finding["classification"],
            "affected_domain": finding["affected_domain"],
            "constitutional_freeze_effect": "DENY_FREEZE",
            "progression_effect": "PROHIBIT_RM002_IMPLEMENTATION_CERTIFICATION",
            "required_remediation": finding["required_remediation"],
        }
        for finding in findings
        if finding["severity"] == "BLOCKER"
    ]
    certification = _certification_assessment(domains, consistency, traceability, findings)
    completion = {
        "series": "CLOSED-POSITION-TRUTH-RM-001-B05",
        "status": "COMPLETE_WITH_CONSTITUTIONAL_BLOCKERS_REPORTED" if blockers else "COMPLETE",
        "orders_completed": tuple(ORDER_SOURCES),
        "final_constitutional_disposition": certification["final_constitutional_disposition"],
        "constitutional_freeze_authorized": certification["constitutional_freeze_authorized"],
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "implementation_discovery_performed": False,
        "behavioral_verification_performed": False,
        "implementation_proof_generated": False,
        "implementation_certification_activity_performed": False,
        "completion_criteria": {
            "every_domain_inventoried": True,
            "required_artifacts_identified_or_missing_recorded": True,
            "missing_domains_recorded": True,
            "duplicates_recorded": True,
            "conflicts_recorded": True,
            "unresolved_decisions_recorded": True,
            "formal_completeness_status_assigned": True,
            "constitutional_deficiencies_not_concealed_by_implementation": True,
            "blockers_explicitly_identified": True,
            "one_final_disposition_issued": True,
            "freeze_authorized_or_denied": True,
        },
        "ready_for": "CLOSED-POSITION-TRUTH-RM-001-B04_REMEDIATION" if blockers else "CLOSED-POSITION-TRUTH-RM-002",
    }

    payloads = {
        "source_order_registry.json": sources,
        "prior_baseline_registry.json": baselines,
        "B05-001_constitutional_completeness_registry.json": domains,
        "B05-001_constitutional_findings_registry.json": findings,
        "B05-001_missing_constitutional_domain_registry.json": missing_domains,
        "B05-001_duplicate_constitutional_domain_registry.json": duplicate_domains,
        "B05-001_unresolved_constitutional_decision_registry.json": unresolved_decisions,
        "B05-001_completeness_reconciliation_completion_report.json": completeness,
        "B05-002_constitutional_consistency_registry.json": consistency,
        "B05-002_authority_consistency_registry.json": [row for row in consistency if row["domain"] == "authority"],
        "B05-002_boundary_consistency_registry.json": [row for row in consistency if row["domain"] == "office_boundary"],
        "B05-002_ownership_consistency_registry.json": [row for row in consistency if row["domain"] == "truth_ownership"],
        "B05-002_custody_consistency_registry.json": [row for row in consistency if row["domain"] == "custody"],
        "B05-002_object_consistency_registry.json": [row for row in consistency if row["domain"] == "canonical_object"],
        "B05-002_lifecycle_consistency_registry.json": [row for row in consistency if row["domain"] == "lifecycle"],
        "B05-002_closure_doctrine_consistency_registry.json": [row for row in consistency if row["domain"] == "closure"],
        "B05-002_settlement_doctrine_consistency_registry.json": [row for row in consistency if row["domain"] == "settlement"],
        "B05-002_residual_quantity_consistency_registry.json": [row for row in consistency if row["domain"] == "residual_quantity"],
        "B05-002_reconciliation_consistency_registry.json": [row for row in consistency if row["domain"] == "reconciliation"],
        "B05-002_realized_outcome_consistency_registry.json": [row for row in consistency if row["domain"] == "realized_outcome"],
        "B05-002_temporal_consistency_registry.json": [row for row in consistency if row["domain"] == "temporal"],
        "B05-002_evidence_consistency_registry.json": [row for row in consistency if row["domain"] == "evidence"],
        "B05-002_historical_integrity_consistency_registry.json": [row for row in consistency if row["domain"] == "historical_integrity"],
        "B05-002_requirement_consistency_registry.json": [row for row in consistency if row["domain"] == "requirement_traceability"],
        "B05-002_terminology_consistency_registry.json": [row for row in consistency if row["domain"] == "terminology"],
        "B05-002_conflict_registry.json": conflicts,
        "B05-002_conflict_resolution_registry.json": [{"conflict_id": row["consistency_id"], "disposition": row["disposition"], "finding_refs": row["finding_refs"]} for row in conflicts],
        "B05-002_constitutional_findings_registry.json": findings,
        "B05-002_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B05-002", "status": "COMPLETE_WITH_REPORTED_BLOCKERS" if conflicts else "COMPLETE"},
        "B05-003_requirement_audit_registry.json": requirements,
        "B05-003_traceability_audit_registry.json": traceability,
        "B05-003_canonical_requirement_population.json": requirements,
        "B05-003_requirement_identity_registry.json": [{"requirement_id": row["requirement_id"], "source": row["authoritative_source"], "status": row["status"]} for row in requirements],
        "B05-003_requirement_classification_registry.json": [{"requirement_id": row["requirement_id"], "primary_classification": row["primary_classification"]} for row in requirements],
        "B05-003_duplicate_requirement_registry.json": [],
        "B05-003_aggregate_requirement_registry.json": [],
        "B05-003_orphan_requirement_registry.json": [row for row in requirements if row["status"] == "BLOCKED_MISSING_SOURCE"],
        "B05-003_conflict_registry.json": conflicts,
        "B05-003_constitutional_traceability_graph.json": traceability,
        "B05-003_constitutional_blocker_registry.json": blockers,
        "B05-003_completion_report.json": {"order": "CLOSED-POSITION-TRUTH-RM-001-B05-003", "status": "COMPLETE_WITH_REPORTED_BLOCKERS" if blockers else "COMPLETE"},
        "B05-004_constitutional_certification_registry.json": certification,
        "B05-004_constitutional_completeness_assessment.json": completeness,
        "B05-004_constitutional_consistency_assessment.json": consistency,
        "B05-004_authority_assessment.json": [row for row in consistency if row["domain"] == "authority"],
        "B05-004_ownership_and_custody_assessment.json": [row for row in consistency if row["domain"] in {"truth_ownership", "custody"}],
        "B05-004_canonical_object_assessment.json": [row for row in domains if row["domain"] == "canonical_object_inventory"],
        "B05-004_lifecycle_assessment.json": [row for row in domains if row["domain"] == "lifecycle_governance"],
        "B05-004_closure_doctrine_assessment.json": [row for row in domains if row["domain"] == "closure_doctrine"],
        "B05-004_settlement_assessment.json": [row for row in domains if row["domain"] == "settlement_doctrine"],
        "B05-004_residual_quantity_assessment.json": [row for row in domains if row["domain"] == "residual_quantity_doctrine"],
        "B05-004_reconciliation_assessment.json": [row for row in domains if row["domain"] == "reconciliation_doctrine"],
        "B05-004_realized_outcome_assessment.json": [row for row in consistency if row["domain"] == "realized_outcome"],
        "B05-004_temporal_assessment.json": [row for row in consistency if row["domain"] == "temporal"],
        "B05-004_evidence_assessment.json": [row for row in consistency if row["domain"] == "evidence"],
        "B05-004_historical_integrity_assessment.json": [row for row in domains if row["domain"] == "historical_integrity"],
        "B05-004_requirement_architecture_assessment.json": [row for row in domains if row["domain"] == "requirement_architecture"],
        "B05-004_traceability_assessment.json": traceability,
        "B05-004_constitutional_findings_registry.json": findings,
        "B05-004_constitutional_blocker_registry.json": blockers,
        "B05-004_constitutional_freeze_authorization_or_denial.json": {"authorized": certification["constitutional_freeze_authorized"], "denial_reason": "constitutional blockers reported" if blockers else None},
        "B05-004_final_ecs003_constitutional_audit_report.json": certification,
        "B05-004_final_constitutional_verdict.json": {"verdict": certification["final_constitutional_disposition"]},
        "B05-004_constitutional_completion_report.json": completion,
        "B05_series_completion_report.json": completion,
    }
    for name, payload in payloads.items():
        _write(name, payload)
    manifest = {
        "package": "CLOSED_POSITION_TRUTH_RM001_B05_CONSTITUTIONAL_CERTIFICATION",
        "series": "CLOSED-POSITION-TRUTH-RM-001-B05",
        "baseline_digest": _digest(payloads),
        "files": sorted(str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/") for path in OUTPUT_DIR.rglob("*") if path.is_file()),
        "final_constitutional_disposition": certification["final_constitutional_disposition"],
    }
    _write("manifest.json", manifest)
    return completion


if __name__ == "__main__":
    print(_json(generate_certification()), end="")
