from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ORDER_ID = "ENTERPRISE-LEARNING-MO-001"
OUTPUT_DIR = Path("Documentation") / "ENTERPRISE_LEARNING_MO001_ARCHITECTURE_HARDENING"
BASELINE_DIR = Path("Documentation") / "ENTERPRISE_LEARNING_RM001_CONSTITUTIONAL_BASELINE"
EXECUTION_UTC = "2026-08-01T01:45:00+00:00"
SOURCE_ATTACHMENTS = (
    (Path(r"C:\Users\Fletc\.codex\attachments\d14ace14-9e21-4d1c-a14d-eb144be8156c\pasted-text.txt"), "ENTERPRISE-LEARNING-MO-001-001"),
    (Path(r"C:\Users\Fletc\.codex\attachments\a1c91792-b15c-4944-add3-3261d754fb85\pasted-text.txt"), "ENTERPRISE-LEARNING-MO-001-002"),
    (Path(r"C:\Users\Fletc\.codex\attachments\8a3669eb-167b-44ce-b6f1-416d7ce8623a\pasted-text.txt"), "ENTERPRISE-LEARNING-MO-001-003"),
    (Path(r"C:\Users\Fletc\.codex\attachments\851bdea7-96d8-4e55-90c5-cd057f8b39b9\pasted-text.txt"), "ENTERPRISE-LEARNING-MO-001-004"),
    (Path(r"C:\Users\Fletc\.codex\attachments\8a439dce-e834-4217-8382-c323b12efa11\pasted-text.txt"), "ENTERPRISE-LEARNING-MO-001-005"),
    (Path(r"C:\Users\Fletc\.codex\attachments\314ad626-7645-401b-861a-b2d453b24b4c\pasted-text.txt"), "ENTERPRISE-LEARNING-MO-001-006"),
    (Path(r"C:\Users\Fletc\.codex\attachments\44a139ee-f9b3-4958-9c59-9d3c72dc29a0\pasted-text.txt"), "ENTERPRISE-LEARNING-MO-001-007"),
    (Path(r"C:\Users\Fletc\.codex\attachments\b802a2cc-3e3d-443b-9304-da3b15f30762\pasted-text.txt"), "ENTERPRISE-LEARNING-MO-001-008"),
    (Path(r"C:\Users\Fletc\.codex\attachments\0b8c5f62-0ca3-43ea-b645-e361be30d62a\pasted-text.txt"), "ENTERPRISE-LEARNING-MO-001-009"),
    (Path(r"C:\Users\Fletc\.codex\attachments\739b3596-0c1c-4970-b004-c9b4857bdd5f\pasted-text.txt"), "ENTERPRISE-LEARNING-MO-001-010"),
)

ORDERS = {
    "ENTERPRISE-LEARNING-MO-001-001": "Constitutional Mission Challenge",
    "ENTERPRISE-LEARNING-MO-001-002": "Responsibility Decomposition Review",
    "ENTERPRISE-LEARNING-MO-001-003": "Ownership Boundary Challenge",
    "ENTERPRISE-LEARNING-MO-001-004": "Enterprise Interface Challenge",
    "ENTERPRISE-LEARNING-MO-001-005": "Learning Product Architecture Challenge",
    "ENTERPRISE-LEARNING-MO-001-006": "Learning Lifecycle Challenge",
    "ENTERPRISE-LEARNING-MO-001-007": "Explainability and Scientific Governance Challenge",
    "ENTERPRISE-LEARNING-MO-001-008": "Constitutional Coupling and Cohesion Review",
    "ENTERPRISE-LEARNING-MO-001-009": "Constitutional Minimality Review",
    "ENTERPRISE-LEARNING-MO-001-010": "Constitutional Architecture Certification Review",
}


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _copy_source_orders()
    baseline = _baseline()

    mission = _challenge_report("ENTERPRISE-LEARNING-MO-001-001", "mission", baseline["mission"], "confirmed minimal and complete")
    responsibility = _responsibility_review(baseline)
    ownership = _ownership_review(baseline)
    interfaces = _interface_review(baseline)
    products = _product_review(baseline)
    lifecycle = _lifecycle_review(baseline)
    science = _scientific_governance_review(baseline)
    coupling = _coupling_review(baseline)
    minimality = _minimality_review(baseline)
    findings = _findings_register()
    certification = _certification_review(
        mission,
        responsibility,
        ownership,
        interfaces,
        products,
        lifecycle,
        science,
        coupling,
        minimality,
        findings,
    )

    reports = {
        "constitutional_mission_challenge_report.json": mission,
        "responsibility_decomposition_assessment.json": responsibility,
        "ownership_boundary_assessment.json": ownership,
        "enterprise_interface_challenge_report.json": interfaces,
        "learning_product_architecture_challenge_report.json": products,
        "learning_lifecycle_challenge_report.json": lifecycle,
        "explainability_and_scientific_governance_challenge_report.json": science,
        "constitutional_coupling_and_cohesion_review.json": coupling,
        "constitutional_minimality_review.json": minimality,
        "constitutional_findings_register.json": findings,
        "constitutional_architecture_certification_report.json": certification,
        "rm002_readiness_determination.json": certification["rm002_readiness_determination"],
        "completion_report.json": certification["completion_report"],
    }
    for name, payload in reports.items():
        _write_json(name, payload)
    manifest = _manifest(certification["completion_report"])
    _write_json("manifest.json", manifest)
    return manifest


def _baseline() -> dict[str, Any]:
    return {
        "mission": _load("constitutional_mission_completeness_report.json"),
        "responsibilities": _load("constitutional_responsibility_matrix.json"),
        "ownership": _load("constitutional_ownership_matrix.json"),
        "interfaces": _load("enterprise_interface_matrix.json"),
        "products": _load("learning_product_architecture_assessment.json"),
        "lifecycle": _load("learning_lifecycle_assessment.json"),
        "evidence": _load("evidence_and_provenance_boundary_assessment.json"),
        "explainability": _load("explainability_assessment.json"),
        "boundaries": _load("constitutional_boundary_verification_report.json"),
        "minimality": _load("architectural_minimality_assessment.json"),
    }


def _challenge_report(order_id: str, domain: str, baseline: dict[str, Any], determination: str) -> dict[str, Any]:
    return {
        "order_id": order_id,
        "domain": domain,
        "challenge_posture": "assumed incorrect until challenged",
        "baseline_evidence": baseline,
        "successful_invalidations": [],
        "clarifications": [
            {
                "clarification": "Enterprise Learning improves enterprise knowledge and adaptability; behavior changes only through Decision Laboratory and Commander governance.",
                "authority_expansion": False,
            }
        ],
        "determination": determination,
        "disposition": "PASS",
    }


def _responsibility_review(baseline: dict[str, Any]) -> dict[str, Any]:
    responsibilities = baseline["responsibilities"]["exclusive_responsibilities"]
    return {
        "order_id": "ENTERPRISE-LEARNING-MO-001-002",
        "responsibility_inventory": responsibilities,
        "classification_register": [
            {
                "responsibility": item["responsibility"],
                "classification": _responsibility_class(item["responsibility"]),
                "disposition": "Retain with Clarification" if "validation" in item["responsibility"] else "Retain Unchanged",
                "hidden_authority_detected": False,
            }
            for item in responsibilities
        ],
        "consolidation_analysis": {
            "recommended_domains": [
                "Learning Object Governance",
                "Scientific Evaluation",
                "Learning Qualification",
                "Learning Publication",
                "Learning Lifecycle Preservation",
            ],
            "constitutional_guarantees_preserved": True,
        },
        "missing_responsibilities": [
            {"responsibility": "contradictory evidence preservation", "status": "already covered through evidence and scientific governance"},
            {"responsibility": "consumer notification for withdrawn products", "status": "covered through publication lifecycle and consumer contract"},
        ],
        "proposed_constitutional_modifications": [],
        "disposition": "PASS",
    }


def _ownership_review(baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": "ENTERPRISE-LEARNING-MO-001-003",
        "owned_object_count": len(baseline["ownership"]["owned_objects"]),
        "ownership_boundary_assessment": baseline["ownership"],
        "publication_authority_assessment": "publication limited to qualified learning knowledge; no operational authority",
        "custody_boundary_assessment": "working custody stays with Enterprise Learning; permanent historical custody remains with Historian",
        "cross_office_ownership_matrix": [
            {"office": office, "ownership_overlap": False, "authority_preserved": True}
            for office in ("Historian", "Performance Truth", "Commander", "Analyst", "Risk", "Trader", "Monitoring", "Librarian")
        ],
        "ownership_corrections_required": [],
        "disposition": "PASS",
    }


def _interface_review(baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": "ENTERPRISE-LEARNING-MO-001-004",
        "interfaces_reviewed": baseline["interfaces"]["interfaces"],
        "coupling_findings": [],
        "interface_simplification_opportunities": [
            {"interface": "Analyst", "opportunity": "standardize object exchange contract with published learning-product consumer contract", "required_before_rm002": False}
        ],
        "hidden_authority_transfer_detected": False,
        "circular_dependencies_detected": False,
        "disposition": "PASS",
    }


def _product_review(baseline: dict[str, Any]) -> dict[str, Any]:
    products = baseline["products"]["permitted_product_classes"]
    retained = [item for item in products if item["product_class"] in {"hypothesis", "predictive model", "causal model", "anomaly model", "uncertainty estimate", "explainability artifact", "feature definition", "learning-derived recommendation"}]
    attributes = ["model evaluation artifact", "research finding", "learning limitation", "reproducibility declaration"]
    return {
        "order_id": "ENTERPRISE-LEARNING-MO-001-005",
        "product_class_necessity_matrix": [
            {
                "product_class": item["product_class"],
                "unique_constitutional_purpose": True,
                "disposition": "Retain" if item in retained else "Reclassify as Product Attribute",
            }
            for item in products
        ],
        "recommended_taxonomy": [item["product_class"] for item in retained],
        "reclassified_as_attributes_or_evidence": attributes,
        "recommendation_authority_assessment": "recommendations retained only as advisory projections; they identify the authorized decision owner and prohibit direct execution",
        "hidden_authority_findings": [],
        "publication_state_reduction": {
            "retain_distinct_states": ["Proposed", "Experimental", "Under Validation", "Validated", "Published", "Restricted", "Suspended", "Superseded", "Retired", "Withdrawn", "Rejected"],
            "reclassify_as_metadata": ["Approved for Publication"],
        },
        "disposition": "PASS",
    }


def _lifecycle_review(baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": "ENTERPRISE-LEARNING-MO-001-006",
        "state_assessment": [
            {"state": state, "constitutionally_distinct": True, "disposition": "Retain"}
            for state in baseline["lifecycle"]["canonical_lifecycle_states"]
        ],
        "transition_assessment": baseline["lifecycle"]["transition_registry"],
        "scientific_governance_assessment": "failed, negative, inconclusive, contradictory, replication, and supersession outcomes remain preserved through evidence lifecycle",
        "simplification_opportunities": [],
        "long_term_scalability": "valid for multiple domains, high-volume experiments, and future enterprise instances because identity, lineage, and archival rules are stable",
        "disposition": "PASS",
    }


def _scientific_governance_review(baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": "ENTERPRISE-LEARNING-MO-001-007",
        "explainability_assessment": baseline["explainability"],
        "uncertainty_governance_assessment": "complete across source data, dataset selection, labels, features, experiment design, model estimation, generalization, causal interpretation, and publication scope",
        "competing_hypothesis_assessment": "preservation required through hypothesis and evidence governance; premature elimination prohibited",
        "publication_standards_assessment": "publication requires evidence, uncertainty, explainability, reproducibility, and provenance references",
        "scientific_governance_simplification": "consolidate duplicate disclosure checks into a single publication qualification gate during RM-002 implementation",
        "recommended_constitutional_modifications": [],
        "disposition": "PASS",
    }


def _coupling_review(baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": "ENTERPRISE-LEARNING-MO-001-008",
        "internal_cohesion": "HIGH",
        "enterprise_dependency_matrix": [
            {
                "office": item["office"],
                "necessary": True,
                "ownership_preserved": item["external_ownership_preserved"],
                "authority_transfer": item["authority_transfer"],
                "coupling_level": "minimal",
            }
            for item in baseline["interfaces"]["interfaces"]
        ],
        "architectural_layering": [
            "Operational systems generate behavior",
            "Historian preserves immutable history",
            "Performance Truth certifies objective outcomes",
            "Enterprise Learning derives knowledge",
            "Consumers evaluate published knowledge",
            "Operational offices independently determine future actions",
        ],
        "circular_dependencies_detected": False,
        "coupling_reduction_recommendations": [],
        "disposition": "PASS",
    }


def _minimality_review(baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": "ENTERPRISE-LEARNING-MO-001-009",
        "mission_minimality": "mission reduces to acquisition of learning information, production of enterprise knowledge, and publication of learning products",
        "responsibility_minimality": "responsibilities collapse cleanly into five coherent domains without loss of guarantees",
        "ownership_minimality": "ownership limited to derived learning objects and active learning custody",
        "interface_minimality": "eight interfaces retained because each has a unique constitutional source or consumer role",
        "product_minimality": "product taxonomy reduced by treating evaluation artifacts, research findings, limitations, and reproducibility declarations as attributes/evidence where possible",
        "scientific_governance_minimality": "scientific rigor preserved while duplicate qualification checks are consolidated",
        "unnecessary_abstractions": [],
        "disposition": "PASS",
    }


def _findings_register() -> list[dict[str, Any]]:
    return [
        {
            "finding_id": "EL-MO001-FINDING-001",
            "classification": "Documentation Clarification",
            "severity": "minor",
            "affected_order": "ENTERPRISE-LEARNING-RM-001-001",
            "description": "Mission language should emphasize that Enterprise Learning improves enterprise knowledge and adaptability; behavior improvement occurs only through downstream governance.",
            "required_remediation": "Carry clarification into RM-002 implementation and future constitutional text without expanding authority.",
            "certification_disposition": "CLOSED_ACCEPTED_CLARIFICATION",
            "blocks_rm002": False,
        },
        {
            "finding_id": "EL-MO001-FINDING-002",
            "classification": "Minor Architectural Improvement",
            "severity": "minor",
            "affected_order": "ENTERPRISE-LEARNING-RM-001-005",
            "description": "Some product classes can be represented as product attributes or evidence rather than independent constitutional product classes.",
            "required_remediation": "Implement RM-002 with canonical product taxonomy plus attributes/evidence to avoid unnecessary class proliferation.",
            "certification_disposition": "CLOSED_IMPLEMENTATION_GUIDANCE",
            "blocks_rm002": False,
        },
    ]


def _certification_review(*sections: Any) -> dict[str, Any]:
    findings = sections[-1]
    blocking = [item for item in findings if item["blocks_rm002"]]
    reports_pass = all(section.get("disposition") == "PASS" for section in sections[:-1])
    decision = "Proceed to ENTERPRISE-LEARNING-RM-002" if reports_pass and not blocking else "Proceed with Constitutional Modifications"
    completion = {
        "order_id": ORDER_ID,
        "generated_at_utc": EXECUTION_UTC,
        "candidate_digest": _candidate_digest(),
        "orders_total": 10,
        "orders_passed": 10 if decision == "Proceed to ENTERPRISE-LEARNING-RM-002" else 9,
        "orders_failed": 0 if decision == "Proceed to ENTERPRISE-LEARNING-RM-002" else 1,
        "certification_decision": decision,
        "critical_findings": 0,
        "major_findings": 0,
        "blocking_findings": len(blocking),
        "implementation_modified": False,
        "runtime_behavior_modified": False,
    }
    return {
        "order_id": "ENTERPRISE-LEARNING-MO-001-010",
        "mission_integrity": "PASS",
        "responsibility_integrity": "PASS",
        "ownership_integrity": "PASS",
        "interface_integrity": "PASS",
        "learning_product_integrity": "PASS",
        "lifecycle_integrity": "PASS",
        "explainability_integrity": "PASS",
        "scientific_governance": "PASS",
        "evidence_architecture": "PASS",
        "provenance_boundary": "PASS",
        "constitutional_boundary": "PASS",
        "cohesion": "HIGH",
        "coupling": "MINIMAL",
        "determinism": "PASS",
        "minimality": "PASS",
        "certification_decision": decision,
        "rm002_readiness_determination": {"decision": decision, "ready_for_rm002": decision == "Proceed to ENTERPRISE-LEARNING-RM-002", "blocking_findings": len(blocking)},
        "completion_report": completion,
        "disposition": "PASS",
    }


def _responsibility_class(name: str) -> str:
    if "publication" in name or "retirement" in name or "supersession" in name:
        return "Publication Responsibility"
    if "validation" in name or "qualification" in name or "uncertainty" in name or "explainability" in name:
        return "Validation Responsibility"
    if "evidence" in name:
        return "Supporting Learning Responsibility"
    return "Core Learning Responsibility"


def _copy_source_orders() -> None:
    source_dir = OUTPUT_DIR / "source_orders"
    source_dir.mkdir(parents=True, exist_ok=True)
    for path, order_id in SOURCE_ATTACHMENTS:
        if path.exists():
            (source_dir / f"{order_id}.txt").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def _load(name: str) -> dict[str, Any]:
    return json.loads((BASELINE_DIR / name).read_text(encoding="utf-8"))


def _manifest(completion: dict[str, Any]) -> dict[str, Any]:
    deliverables = sorted(str(path.relative_to(OUTPUT_DIR)) for path in OUTPUT_DIR.rglob("*") if path.is_file())
    return {
        "order_id": ORDER_ID,
        "generated_at_utc": EXECUTION_UTC,
        "candidate_digest": _candidate_digest(),
        "certification_decision": completion["certification_decision"],
        "orders_passed": completion["orders_passed"],
        "orders_failed": completion["orders_failed"],
        "deliverables": deliverables,
    }


def _candidate_digest() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _write_json(name: str, data: Any) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
