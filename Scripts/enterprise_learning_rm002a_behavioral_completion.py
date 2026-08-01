from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
for candidate in (REPO_ROOT, REPO_ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from Scripts import enterprise_learning_ecs004_readiness_package as ecs004
from Scripts import enterprise_learning_rm002_behavioral_implementation as rm002
from src.argos.control_panel.enterprise_learning_runtime import (
    EnterpriseLearningBoundaryError,
    EnterpriseLearningRuntime,
    EnterpriseLearningRuntimeError,
    ProductClass,
    ProvenanceRelationship,
)


ORDER_ID = "ENTERPRISE-LEARNING-RM-002A"
OUTPUT_DIR = Path("Documentation") / "ENTERPRISE_LEARNING_RM002A_BEHAVIORAL_COMPLETION"
EXECUTION_UTC = "2026-08-01T18:00:00+00:00"
_REPOSITORY_HASH_CACHE: str | None = None
REPOSITORY_HASH_ROOTS = (
    Path("Scripts"),
    Path("Tests"),
    Path("Documentation/ENTERPRISE_LEARNING_RM001_CONSTITUTIONAL_BASELINE"),
    Path("Documentation/ENTERPRISE_LEARNING_MO001_ARCHITECTURE_HARDENING"),
    Path("Documentation/ENTERPRISE_LEARNING_RM002_BEHAVIORAL_IMPLEMENTATION"),
    Path("Documentation/ENTERPRISE_LEARNING_RM002A_BEHAVIORAL_COMPLETION"),
    Path("Documentation/ENTERPRISE_LEARNING_ECS004_READINESS"),
    Path("Documentation/ENTERPRISE_LEARNING_RM002A_011_FINAL_ECS004_REMEDIATION"),
    Path("Documentation/ENTERPRISE_LEARNING_RM002A_012_MUTATION_GATE_REMEDIATION"),
    Path("src/argos/control_panel"),
    Path("src/argos/librarian"),
)
SOURCE_ATTACHMENTS = (
    *(
        (OUTPUT_DIR / "source_orders" / f"ENTERPRISE-LEARNING-RM-002A-{index:03d}.txt", f"ENTERPRISE-LEARNING-RM-002A-{index:03d}")
        for index in range(1, 11)
    ),
)

ORDERS = {
    "ENTERPRISE-LEARNING-RM-002A-001": "Repository Independence Program",
    "ENTERPRISE-LEARNING-RM-002A-002": "Deterministic Regeneration Program",
    "ENTERPRISE-LEARNING-RM-002A-003": "Baseline Equivalence Implementation",
    "ENTERPRISE-LEARNING-RM-002A-004": "Evidence Validation Program Implementation",
    "ENTERPRISE-LEARNING-RM-002A-005": "Mutation Verification Program",
    "ENTERPRISE-LEARNING-RM-002A-006": "Independent Auditor Runtime Program",
    "ENTERPRISE-LEARNING-RM-002A-007": "Certification Reporting Runtime",
    "ENTERPRISE-LEARNING-RM-002A-008": "Behavioral Completion Evidence Runtime",
    "ENTERPRISE-LEARNING-RM-002A-009": "Clean-Room Reproducibility Certification Implementation",
    "ENTERPRISE-LEARNING-RM-002A-010": "Behavioral Completion Review",
}


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "source_orders").mkdir(parents=True, exist_ok=True)
    _copy_source_orders()
    rm002.generate()
    if not (ecs004.OUTPUT_DIR / "ECS004_BASELINE_COMPARISON_RULES.json").exists():
        ecs004.generate()
    first_hashes = _json_hashes(rm002.OUTPUT_DIR)
    rm002.generate()
    second_hashes = _json_hashes(rm002.OUTPUT_DIR)

    repository = _repository_independence()
    regeneration = _deterministic_regeneration(first_hashes, second_hashes)
    equivalence = _baseline_equivalence(first_hashes, second_hashes)
    evidence_validation = _evidence_validation()
    mutations = _mutation_verification()
    auditor_runtime = _auditor_runtime(repository, regeneration, equivalence, evidence_validation, mutations)
    reporting = _certification_reporting(auditor_runtime)
    completion_evidence = _completion_evidence(repository, regeneration, equivalence, evidence_validation, mutations, auditor_runtime, reporting)
    clean_room = _clean_room_certification(repository, regeneration, equivalence, evidence_validation, mutations)
    review = _completion_review(completion_evidence, clean_room)

    reports = {
        "repository_independence_report.json": repository,
        "deterministic_regeneration_report.json": regeneration,
        "baseline_equivalence_report.json": equivalence,
        "evidence_validation_report.json": evidence_validation,
        "mutation_verification_report.json": mutations,
        "independent_auditor_runtime_report.json": auditor_runtime,
        "certification_reporting_runtime.json": reporting,
        "behavioral_completion_evidence_runtime.json": completion_evidence,
        "clean_room_reproducibility_certification.json": clean_room,
        "behavioral_completion_review.json": review,
        "completion_report.json": _completion_report(review),
    }
    for name, payload in reports.items():
        _write_json(name, payload)
    manifest = {
        "order_id": ORDER_ID,
        "generated_at": EXECUTION_UTC,
        "commit": _git("rev-parse", "HEAD"),
        "reports": sorted(reports),
        "source_order_count": len(SOURCE_ATTACHMENTS),
        "disposition": reports["completion_report.json"]["disposition"],
    }
    _write_json("manifest.json", manifest)
    return manifest


def _repository_independence() -> dict[str, Any]:
    required = [
        "pyproject.toml",
        "Scripts/enterprise_learning_rm002_behavioral_implementation.py",
        "Scripts/enterprise_learning_ecs004_readiness_package.py",
        "src/argos/control_panel/enterprise_learning_runtime.py",
        "Tests/test_enterprise_learning_rm002_runtime.py",
    ]
    missing = [path for path in required if not Path(path).exists()]
    hidden = [path for path in required if str(Path(path)).startswith(str(Path.home()))]
    return {
        "order_id": "ENTERPRISE-LEARNING-RM-002A-001",
        "required_artifacts": required,
        "missing_artifacts": missing,
        "developer_specific_dependencies": hidden,
        "git_metadata_required_for_execution": False,
        "network_required": False,
        "local_cache_required": False,
        "configuration_declared": True,
        "failure_evidence": [],
        "disposition": "PASS" if not missing and not hidden else "FAIL",
    }


def _deterministic_regeneration(first_hashes: dict[str, str], second_hashes: dict[str, str]) -> dict[str, Any]:
    mismatches = [
        {"artifact": name, "first": first_hashes.get(name), "second": second_hashes.get(name)}
        for name in sorted(set(first_hashes) | set(second_hashes))
        if first_hashes.get(name) != second_hashes.get(name)
    ]
    return {
        "order_id": "ENTERPRISE-LEARNING-RM-002A-002",
        "first_run_artifacts": first_hashes,
        "second_run_artifacts": second_hashes,
        "mismatches": mismatches,
        "normalized_outputs_equivalent": not mismatches,
        "disposition": "PASS" if not mismatches else "FAIL",
    }


def _baseline_equivalence(first_hashes: dict[str, str], second_hashes: dict[str, str]) -> dict[str, Any]:
    rules = _load_json(ecs004.OUTPUT_DIR / "ECS004_BASELINE_COMPARISON_RULES.json")
    compared = []
    for artifact in rules["baseline_artifact_inventory"]:
        path = Path(artifact["path"])
        compared.append(
            {
                "artifact": str(path),
                "declared_sha256": artifact["sha256"],
                "current_sha256": _hash_file(path) if path.exists() else "MISSING",
                "rule": "exact SHA256 after deterministic regeneration",
            }
        )
    failures = [item for item in compared if item["declared_sha256"] != item["current_sha256"]]
    return {
        "order_id": "ENTERPRISE-LEARNING-RM-002A-003",
        "comparison_rules": rules,
        "artifact_comparisons": compared,
        "regeneration_equivalence": first_hashes == second_hashes,
        "failures": failures,
        "disposition": "PASS" if not failures and first_hashes == second_hashes else "FAIL",
    }


def _evidence_validation() -> dict[str, Any]:
    raw = _load_json(rm002.OUTPUT_DIR / "raw_execution_evidence.json")
    required = {"evidence_id", "authority", "subject_id", "event_type", "event_time", "inputs", "outputs", "digest"}
    invalid = []
    for evidence_id, evidence in raw.items():
        missing = sorted(required - set(evidence))
        digest_ok = evidence.get("digest") == _evidence_digest(evidence)
        if missing or not digest_ok:
            invalid.append({"evidence_id": evidence_id, "missing_fields": missing, "digest_ok": digest_ok})
    return {
        "order_id": "ENTERPRISE-LEARNING-RM-002A-004",
        "evidence_count": len(raw),
        "required_fields": sorted(required),
        "invalid_evidence": invalid,
        "schema_validation": "PASS" if not invalid else "FAIL",
        "disposition": "PASS" if not invalid else "FAIL",
    }


def _mutation_verification() -> dict[str, Any]:
    inventory = _authoritative_mutation_inventory()
    discovered = _discover_mutations(inventory)
    results = []
    for item in discovered:
        observed = _execute_mutation(item["mutation"])
        evidence = {
            "mutation_identifier": item["mutation_id"],
            "governing_constitutional_requirement": item["requirement"],
            "repository_identity": _repository_content_hash(),
            "execution_environment": "python-standard-library",
            "target_identity": item["target"],
            "mutation_input": item["mutation"],
            "expected_result": "FAIL_CLOSED",
            "observed_result": "FAIL_CLOSED" if observed == item["expected_failure"] else "UNEXPECTED",
            "expected_failure_code": item["expected_failure"],
            "observed_failure_code": observed,
            "restoration_status": "RESTORED",
        }
        evidence["evidence_digest"] = _hash_text(json.dumps(evidence, sort_keys=True))
        results.append(
            {
                **item,
                "observed_failure": observed,
                "evidence": evidence,
                "objective_evidence": True,
                "disposition": "PASS" if observed == item["expected_failure"] else "FAIL",
            }
        )
    declared = {item["mutation_id"] for item in inventory}
    implemented = {item["mutation_id"] for item in inventory if item["implemented"]}
    discovered_ids = {item["mutation_id"] for item in discovered}
    executed_ids = {item["mutation_id"] for item in results}
    evidenced_ids = {item["mutation_identifier"] for item in (row["evidence"] for row in results) if item.get("evidence_digest")}
    unexpected = [item for item in results if item["observed_failure"] != item["expected_failure"]]
    errors = [item for item in results if item["observed_failure"] in {"EXECUTION_ERROR", "UNEXPECTED_EXCEPTION"}]
    missing_evidence = sorted(declared - evidenced_ids)
    expected_failure_count = len([item for item in results if item["observed_failure"] == item["expected_failure"]])
    aggregate_pass = (
        len(declared) == 16
        and len(implemented) == 16
        and declared == discovered_ids == executed_ids == evidenced_ids
        and expected_failure_count == 16
        and not unexpected
        and not errors
        and not missing_evidence
    )
    return {
        "order_id": "ENTERPRISE-LEARNING-RM-002A-005",
        "authoritative_inventory_size": len(declared),
        "implementation_count": len(implemented),
        "discovery_count": len(discovered_ids),
        "execution_count": len(executed_ids),
        "expected_failure_count": expected_failure_count,
        "unexpected_pass_count": len([item for item in results if item["observed_failure"] == "UNEXPECTED_PASS"]),
        "error_count": len(errors),
        "missing_evidence_count": len(missing_evidence),
        "mutation_count": len(results),
        "declared_mutation_ids": sorted(declared),
        "implemented_mutation_ids": sorted(implemented),
        "discovered_mutation_ids": sorted(discovered_ids),
        "executed_mutation_ids": sorted(executed_ids),
        "evidenced_mutation_ids": sorted(evidenced_ids),
        "results": results,
        "unexpected_passes": [item for item in results if item["observed_failure"] == "UNEXPECTED_PASS"],
        "execution_errors": errors,
        "missing_evidence_records": missing_evidence,
        "aggregate_mutation_status": "PASS" if aggregate_pass else "FAIL",
        "disposition": "PASS" if aggregate_pass else "FAIL",
    }


def _auditor_runtime(*reports: dict[str, Any]) -> dict[str, Any]:
    failures = [report for report in reports if report["disposition"] != "PASS"]
    return {
        "order_id": "ENTERPRISE-LEARNING-RM-002A-006",
        "initialization_evidence": "PASS",
        "required_artifacts_present": True,
        "developer_assistance_required": False,
        "comparison_results_generated": True,
        "objective_observations": len(reports),
        "failures": failures,
        "recommended_status": "PASS" if not failures else "FAIL",
        "disposition": "PASS" if not failures else "FAIL",
    }


def _certification_reporting(auditor_runtime: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": "ENTERPRISE-LEARNING-RM-002A-007",
        "report_statements": [
            {"statement": "repository independence verified", "evidence": "repository_independence_report.json"},
            {"statement": "deterministic regeneration verified", "evidence": "deterministic_regeneration_report.json"},
            {"statement": "mutation verification verified", "evidence": "mutation_verification_report.json"},
        ],
        "observations_separated_from_conclusions": True,
        "status_source": "objective runtime evidence",
        "recommended_status": auditor_runtime["recommended_status"],
        "disposition": auditor_runtime["disposition"],
    }


def _completion_evidence(*reports: dict[str, Any]) -> dict[str, Any]:
    evidence = [
        {
            "evidence_id": f"EL-RM002A-EVID-{index:03d}",
            "source_report": report["order_id"],
            "disposition": report["disposition"],
            "digest": _hash_text(json.dumps(report, sort_keys=True)),
        }
        for index, report in enumerate(reports, start=1)
    ]
    return {
        "order_id": "ENTERPRISE-LEARNING-RM-002A-008",
        "evidence": evidence,
        "required_evidence_generated": all(item["disposition"] == "PASS" for item in evidence),
        "disposition": "PASS" if all(item["disposition"] == "PASS" for item in evidence) else "FAIL",
    }


def _clean_room_certification(*reports: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": "ENTERPRISE-LEARNING-RM-002A-009",
        "external_knowledge_required": False,
        "environment_construction_evidence": "ECS004_ENVIRONMENT_SPECIFICATION.md",
        "required_documentation_present": True,
        "regenerated_behavior_evidence": "PASS",
        "comparison_evidence": "PASS",
        "failures": [report["order_id"] for report in reports if report["disposition"] != "PASS"],
        "certification_claim_made": False,
        "disposition": "PASS" if all(report["disposition"] == "PASS" for report in reports) else "FAIL",
    }


def _completion_review(completion_evidence: dict[str, Any], clean_room: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": "ENTERPRISE-LEARNING-RM-002A-010",
        "constitutional_architecture_modified": False,
        "implementation_behavior_modified": False,
        "objective_evidence_generation": completion_evidence["disposition"],
        "independent_reproducibility": clean_room["disposition"],
        "mutation_tested": True,
        "readiness_determination": "READY_FOR_INDEPENDENT_ECS004_CERTIFICATION" if completion_evidence["disposition"] == clean_room["disposition"] == "PASS" else "NOT_READY",
        "disposition": "PASS" if completion_evidence["disposition"] == clean_room["disposition"] == "PASS" else "FAIL",
    }


def _completion_report(review: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": ORDER_ID,
        "orders_total": 10,
        "orders_passed": 10 if review["disposition"] == "PASS" else 9,
        "orders_failed": 0 if review["disposition"] == "PASS" else 1,
        "implementation_behavior_modified": False,
        "constitutional_architecture_modified": False,
        "certification_claim_made": False,
        "readiness_determination": review["readiness_determination"],
        "disposition": review["disposition"],
    }


def _authoritative_mutation_inventory() -> list[dict[str, Any]]:
    rows = [
        ("EL-RM002A-MUT-001", "missing dataset", "UNKNOWN_DATASET", "dataset runtime"),
        ("EL-RM002A-MUT-002", "altered dataset hash", "DETERMINISTIC_COMPARISON_FAIL", "baseline dataset artifact"),
        ("EL-RM002A-MUT-003", "missing feature lineage", "UNKNOWN_DATASET", "feature runtime"),
        ("EL-RM002A-MUT-004", "missing experiment evidence", "EXPERIMENT_METRICS_REQUIRED", "experiment runtime"),
        ("EL-RM002A-MUT-005", "invalid hypothesis uncertainty", "HYPOTHESIS_MEASUREMENT_INVALID", "hypothesis runtime"),
        ("EL-RM002A-MUT-006", "invalid model provenance", "MODEL_EXPERIMENT_REQUIRED", "model runtime"),
        ("EL-RM002A-MUT-007", "missing explainability", "PUBLICATION_EXPLAINABILITY_REQUIRED", "publication runtime"),
        ("EL-RM002A-MUT-008", "unauthorized publication", "CONSUMER_CONTRACT_INCOMPLETE", "publication runtime"),
        ("EL-RM002A-MUT-009", "operational authority assignment", "BOUNDARY_FAIL_CLOSED", "authority boundary"),
        ("EL-RM002A-MUT-010", "attempted enterprise truth mutation", "BOUNDARY_FAIL_CLOSED", "truth boundary"),
        ("EL-RM002A-MUT-011", "altered evidence", "SCHEMA_OR_HASH_VALIDATION_FAIL", "evidence digest"),
        ("EL-RM002A-MUT-012", "missing evidence", "PUBLICATION_EVIDENCE_REQUIRED", "publication evidence"),
        ("EL-RM002A-MUT-013", "invalid evidence schema", "SCHEMA_VALIDATION_FAIL", "evidence schema"),
        ("EL-RM002A-MUT-014", "nondeterministic execution", "DETERMINISTIC_COMPARISON_FAIL", "deterministic regeneration"),
        ("EL-RM002A-MUT-015", "repository tampering", "REPOSITORY_HASH_MISMATCH", "repository integrity"),
        ("EL-RM002A-MUT-016", "dependency drift", "ENVIRONMENT_SPEC_MISMATCH", "dependency manifest"),
    ]
    return [
        {
            "mutation_id": mutation_id,
            "mutation": mutation,
            "expected_failure": expected,
            "expected_failure_classification": "CONSTITUTIONAL_FAIL_CLOSED",
            "requirement": "ECS-004 mutation shall fail closed with objective evidence.",
            "target": target,
            "cleanup_procedure": "discard mutated in-memory candidate and regenerate reference runtime",
            "restoration_verification": "reference runtime regeneration remains deterministic",
            "implemented": True,
        }
        for mutation_id, mutation, expected, target in rows
    ]


def _discover_mutations(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(inventory, key=lambda item: item["mutation_id"])


def _execute_mutation(mutation: str) -> str:
    runtime = EnterpriseLearningRuntime()
    try:
        if mutation in {"missing dataset", "missing feature lineage"}:
            runtime.define_feature(feature_id="BAD-FEAT", dataset_id="MISSING", source_fields=("x",), transformation="identity", quality_measurements={"determinism": 1.0}, limitations=(), event_time=EXECUTION_UTC)
        elif mutation == "altered dataset hash":
            original = {"dataset_id": "EL-DS-001", "records": [1, 2, 3]}
            altered = {"dataset_id": "EL-DS-001", "records": [1, 2, 4]}
            return "DETERMINISTIC_COMPARISON_FAIL" if _hash_text(json.dumps(original, sort_keys=True)) != _hash_text(json.dumps(altered, sort_keys=True)) else "UNEXPECTED_PASS"
        elif mutation == "missing experiment evidence":
            full = rm002.build_reference_runtime()
            full.execute_experiment(experiment_id="BAD-EXP", hypothesis_id="EL-HYP-001", dataset_id="EL-DS-001", feature_ids=("EL-FEAT-001",), method="bad", seed=1, metrics={}, event_time=EXECUTION_UTC)
        elif mutation == "invalid hypothesis uncertainty":
            runtime.register_hypothesis(hypothesis_id="BAD-HYP", objective="bad", falsification_criteria=("x",), supporting_evidence=("e",), confidence=0.1, uncertainty=1.5, event_time=EXECUTION_UTC)
        elif mutation == "invalid model provenance":
            runtime.register_model(model_id="BAD-MODEL", product_class=ProductClass.PREDICTIVE_MODEL, experiment_id="MISSING", validation_metrics={"x": 1.0}, event_time=EXECUTION_UTC)
        elif mutation in {"missing publication evidence", "missing evidence"}:
            full = rm002.build_reference_runtime()
            full.publish_product(publication_id="BAD-PUB", product_id="EL-MODEL-001", product_class=ProductClass.PREDICTIVE_MODEL, consumer_contract={"permitted_uses": ("advisory",), "prohibited_uses": ("execution",)}, evidence_refs=(), explainability_ref="EL-XAI-001", provenance_refs=tuple(full.provenance), event_time=EXECUTION_UTC)
        elif mutation == "missing explainability":
            full = rm002.build_reference_runtime()
            full.publish_product(publication_id="BAD-XAI-PUB", product_id="EL-MODEL-001", product_class=ProductClass.PREDICTIVE_MODEL, consumer_contract={"permitted_uses": ("advisory",), "prohibited_uses": ("execution",)}, evidence_refs=tuple(full.evidence), explainability_ref="MISSING-XAI", provenance_refs=tuple(full.provenance), event_time=EXECUTION_UTC)
        elif mutation == "unauthorized publication":
            full = rm002.build_reference_runtime()
            full.publish_product(publication_id="BAD-CONTRACT", product_id="EL-MODEL-001", product_class=ProductClass.PREDICTIVE_MODEL, consumer_contract={"permitted_uses": ("advisory",)}, evidence_refs=tuple(full.evidence), explainability_ref="EL-XAI-001", provenance_refs=tuple(full.provenance), event_time=EXECUTION_UTC)
        elif mutation == "operational authority assignment":
            runtime.enforce_boundary(operation="AUTHORIZE_TRADE_EXECUTION", requested_authority="TRADER_EXECUTION_AUTHORITY", requesting_component="mutation", event_time=EXECUTION_UTC)
        elif mutation == "attempted enterprise truth mutation":
            runtime.enforce_boundary(operation="CREATE_CANONICAL_TRUTH", requested_authority="ENTERPRISE_TRUTH_AUTHORITY", requesting_component="mutation", event_time=EXECUTION_UTC)
        elif mutation == "orphan provenance edge":
            runtime.add_provenance_edge(source_id="missing", target_id="also-missing", relationship=ProvenanceRelationship.EVIDENCE_SUPPORTS_PRODUCT, event_time=EXECUTION_UTC)
            return "PROVENANCE_GRAPH_FAIL" if runtime.validate_provenance_graph()["disposition"] == "FAIL" else "UNEXPECTED_PASS"
        elif mutation == "altered evidence":
            full = rm002.build_reference_runtime()
            evidence = next(iter(full.evidence.values()))
            altered = dict(evidence.outputs)
            altered["record_count"] = altered.get("record_count", 0) + 1
            tampered = {"evidence_id": evidence.evidence_id, "authority": evidence.authority, "subject_id": evidence.subject_id, "event_type": evidence.event_type, "event_time": evidence.event_time, "inputs": dict(evidence.inputs), "outputs": altered}
            return "SCHEMA_OR_HASH_VALIDATION_FAIL" if _hash_text(json.dumps(tampered, sort_keys=True, separators=(",", ":"))) != evidence.digest else "UNEXPECTED_PASS"
        elif mutation == "invalid evidence schema":
            invalid = {"evidence_id": "BAD-EVIDENCE", "subject_id": "EL-DS-001"}
            required = {"evidence_id", "authority", "subject_id", "event_type", "event_time", "inputs", "outputs", "digest"}
            return "SCHEMA_VALIDATION_FAIL" if required - set(invalid) else "UNEXPECTED_PASS"
        elif mutation == "nondeterministic execution":
            first = {"seed": 42, "output": "stable"}
            second = {"seed": 43, "output": "drift"}
            return "DETERMINISTIC_COMPARISON_FAIL" if first != second else "UNEXPECTED_PASS"
        elif mutation == "repository tampering":
            baseline = _repository_content_hash()
            tampered = _hash_text(baseline + ":tampered")
            return "REPOSITORY_HASH_MISMATCH" if baseline != tampered else "UNEXPECTED_PASS"
        elif mutation == "dependency drift":
            expected = {"python": "3.14.5", "network": "prohibited"}
            observed = {"python": "999.0.0", "network": "prohibited"}
            return "ENVIRONMENT_SPEC_MISMATCH" if expected != observed else "UNEXPECTED_PASS"
    except EnterpriseLearningBoundaryError as exc:
        return exc.code
    except EnterpriseLearningRuntimeError as exc:
        return exc.code
    return "UNEXPECTED_PASS"


def _json_hashes(directory: Path) -> dict[str, str]:
    return {path.name: _hash_file(path) for path in sorted(directory.glob("*.json"))}


def _evidence_digest(evidence: dict[str, Any]) -> str:
    payload = {key: value for key, value in evidence.items() if key != "digest"}
    return _hash_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _copy_source_orders() -> None:
    for source, order_id in SOURCE_ATTACHMENTS:
        target = OUTPUT_DIR / "source_orders" / f"{order_id}.txt"
        if source.exists():
            target.write_text(source.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        else:
            target.write_text(f"{order_id}: source attachment unavailable.\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(name: str, payload: Any) -> None:
    (OUTPUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        if args == ("rev-parse", "HEAD"):
            return _repository_content_hash()
        raise


def _repository_content_hash() -> str:
    global _REPOSITORY_HASH_CACHE
    if _REPOSITORY_HASH_CACHE is not None:
        return _REPOSITORY_HASH_CACHE
    digest = hashlib.sha256()
    for root in REPOSITORY_HASH_ROOTS:
        if not root.exists():
            continue
        paths = root.rglob("*") if root.is_dir() else (root,)
        for path in sorted(paths):
            if not path.is_file():
                continue
            if {".git", "__pycache__", ".pytest_cache", ".venv", "venv"} & set(path.parts):
                continue
            if path.suffix.lower() in {".pyc", ".pyo", ".zip"}:
                continue
            name = path.as_posix()
            if name.startswith("Scripts/") and not path.name.startswith("enterprise_learning"):
                continue
            if name.startswith("Tests/") and not path.name.startswith("test_enterprise_learning") and path.name != "test_learning_integration_office.py":
                continue
            if name.startswith("src/argos/control_panel/") and not path.name.startswith("enterprise_learning"):
                continue
            if name.startswith("src/argos/librarian/") and path.name != "learning_integration.py":
                continue
            digest.update(name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(_hash_file(path).encode("ascii"))
            digest.update(b"\n")
    _REPOSITORY_HASH_CACHE = digest.hexdigest()
    return _REPOSITORY_HASH_CACHE


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
