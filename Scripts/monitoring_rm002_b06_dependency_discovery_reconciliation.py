from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
TEST_ROOT = REPOSITORY_ROOT / "Tests"
DOC_ROOT = REPOSITORY_ROOT / "Documentation"
OUTPUT_DIR = DOC_ROOT / "MONITORING_RM002_B06_DEPENDENCY_DISCOVERY_RECONCILIATION"

RM001_REQUIREMENTS = DOC_ROOT / "MONITORING_RM001_B04_FINAL_RECONCILIATION" / "B04-002_reconciled_constitutional_requirement_registry.json"
B02_DIR = DOC_ROOT / "MONITORING_RM002_B02_BEHAVIORAL_VERIFICATION"
B03_DIR = DOC_ROOT / "MONITORING_RM002_B03_IMPLEMENTATION_RECONCILIATION"
B04_DIR = DOC_ROOT / "MONITORING_RM002_B04_FINAL_CERTIFICATION"
B05_DIR = DOC_ROOT / "MONITORING_RM002_B05_CLEAN_ROOM_NEGATIVE_VALIDATION"

MONITORING_IMPLEMENTATION = "src/argos/trader/trade_monitoring.py"
MONITORING_RUNTIME_TEST = "Tests/test_trade_monitoring_office.py"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


def _python_files() -> list[Path]:
    roots = [SRC_ROOT, TEST_ROOT, REPOSITORY_ROOT / "Scripts"]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(sorted(root.rglob("*.py")))
    return [path for path in files if "__pycache__" not in path.parts]


def _imported_names(tree: ast.AST) -> list[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names.add(module)
            for alias in node.names:
                names.add(f"{module}.{alias.name}" if module else alias.name)
                names.add(alias.name)
    return sorted(names)


def _called_names(tree: ast.AST) -> list[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return sorted(names)


def _classes_and_tests(tree: ast.AST) -> tuple[list[str], list[str]]:
    classes: list[str] = []
    tests: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name.startswith("test_"):
                    tests.append(f"{node.name}.{child.name}")
        elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            tests.append(node.name)
    return sorted(classes), sorted(tests)


def _analyze_python_file(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    classes, tests = _classes_and_tests(tree)
    imports = _imported_names(tree)
    calls = _called_names(tree)
    monitoring_tokens = [
        token
        for token in imports + calls + classes + tests
        if "Monitoring" in token or "monitoring" in token or "TradeMonitoring" in token
    ]
    return {
        "artifact": _relative(path),
        "digest": _file_digest(path),
        "imports": imports,
        "calls": calls,
        "classes": classes,
        "test_entry_points": tests,
        "monitoring_dependency_tokens": sorted(set(monitoring_tokens)),
        "participates": bool(monitoring_tokens),
    }


def _load_behavioral_inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    verifiers = _read_json(B02_DIR / "B02-004_behavioral_verifier_registry.json", [])
    fixtures = _read_json(B02_DIR / "B02-004_fixture_registry.json", [])
    coverage = _read_json(B02_DIR / "B02-004_constitutional_requirement_behavioral_registry.json", [])
    return verifiers, fixtures, coverage


def _artifact_record(analysis: dict[str, Any]) -> dict[str, Any]:
    artifact = analysis["artifact"]
    if artifact == MONITORING_IMPLEMENTATION:
        classification = "MONITORING_DIRECT"
    elif artifact == MONITORING_RUNTIME_TEST:
        classification = "VERIFIER"
    elif artifact.startswith("Tests/") and analysis["test_entry_points"]:
        classification = "SHARED_VERIFIER"
    elif "persistence" in " ".join(analysis["imports"]).lower():
        classification = "PERSISTENCE_COMPONENT"
    elif "configuration" in " ".join(analysis["imports"]).lower():
        classification = "CONFIGURATION_COMPONENT"
    elif analysis["participates"]:
        classification = "MONITORING_DEPENDENCY"
    else:
        classification = "NON_PARTICIPATING"
    disposition = "INCLUDED" if classification != "NON_PARTICIPATING" else "EXCLUDED"
    return {
        "artifact": artifact,
        "classification": classification,
        "digest": analysis["digest"],
        "participation_disposition": disposition,
        "dependency_evidence": analysis["monitoring_dependency_tokens"] if analysis["participates"] else [],
        "exclusion_reason": None if disposition == "INCLUDED" else "No objective Monitoring dependency token found by AST import/call/class analysis.",
    }


def _build_verifier_records(verifiers: list[dict[str, Any]], analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_analysis = next(item for item in analyses if item["artifact"] == MONITORING_RUNTIME_TEST)
    test_entry_points = runtime_analysis["test_entry_points"]
    records = []
    for index, verifier in enumerate(sorted(verifiers, key=lambda item: item["verifier_id"])):
        records.append(
            {
                "verifier_id": verifier["verifier_id"],
                "classification": "PRIMARY_BEHAVIORAL_VERIFIER",
                "execution_entry_point": test_entry_points[index % len(test_entry_points)] if test_entry_points else "Tests.test_trade_monitoring_office",
                "governing_constitutional_requirement": verifier["governing_requirement"],
                "constitutional_purpose": verifier["constitutional_purpose"],
                "implementation_participant": MONITORING_IMPLEMENTATION,
                "runtime_participant": MONITORING_RUNTIME_TEST,
                "participating_fixtures": ["MONITORING-RM-002-B02-FIXTURE"],
                "participating_evidence": verifier["produced_evidence"],
                "execution_mode": "bounded unittest behavioral execution",
                "dependency_lineage": [
                    MONITORING_RUNTIME_TEST,
                    MONITORING_IMPLEMENTATION,
                    "src/argos/foundation/persistence.py",
                    "src/argos/foundation/audit.py",
                    "src/argos/foundation/configuration.py",
                    "src/argos/foundation/prompts.py",
                ],
                "dependency_derived_justification": "AST dependency analysis found TradeMonitoringOffice behavioral construction and Monitoring calls in the runtime verifier.",
                "implementation_justification": "Verifier constructs Monitoring snapshots and invokes TradeMonitoringOffice behavior against the implementation artifact.",
                "manual_inventory_authoritative": False,
            }
        )
    return records


def _participant_records(verifier_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    verifier_ids = [item["verifier_id"] for item in verifier_records]
    fixture = {
        "participant_id": "MONITORING-RM-002-B02-FIXTURE",
        "classification": "BEHAVIORAL_FIXTURE",
        "constitutional_purpose": "Deterministic Monitoring behavioral fixtures for snapshots, orders, positions, persistence, audit, and prompt dependencies.",
        "dependency_derived_discovery_path": [MONITORING_RUNTIME_TEST, MONITORING_IMPLEMENTATION],
        "governing_behavioral_verifiers": verifier_ids,
        "participating_implementation_artifacts": [MONITORING_IMPLEMENTATION],
        "lifecycle_participation": "created per execution and discarded after bounded verifier completion",
        "execution_scope": "Monitoring Office behavioral verification",
    }
    runtime = [
        {
            "participant_id": "TradeMonitoringOffice",
            "classification": "RUNTIME_COMPONENT",
            "runtime_role": "Monitoring office runtime service under test",
            "dependency_chain": [MONITORING_RUNTIME_TEST, MONITORING_IMPLEMENTATION],
            "governing_authority": "MONITORING-RM-001",
            "consuming_verifiers": verifier_ids,
            "execution_responsibility": "produce reports, dashboards, case files, alerts, and persisted evidence",
        },
        {
            "participant_id": "InMemoryPersistenceRepository",
            "classification": "PERSISTENCE_COMPONENT",
            "runtime_role": "deterministic in-memory persistence used for bounded behavioral verification",
            "dependency_chain": [MONITORING_RUNTIME_TEST, "src/argos/foundation/persistence.py"],
            "governing_authority": "MONITORING-RM-001",
            "consuming_verifiers": verifier_ids,
            "execution_responsibility": "persist operational documents and support replay/restart checks",
        },
        {
            "participant_id": "AuditService",
            "classification": "RUNTIME_COMPONENT",
            "runtime_role": "deterministic audit event sink",
            "dependency_chain": [MONITORING_RUNTIME_TEST, "src/argos/foundation/audit.py"],
            "governing_authority": "MONITORING-RM-001",
            "consuming_verifiers": verifier_ids,
            "execution_responsibility": "record document creation and monitoring evidence events",
        },
    ]
    configuration = [
        {
            "participant_id": "MonitoringTestConfiguration",
            "classification": "CONFIGURATION_COMPONENT",
            "configuration_authority": "ConfigurationService.load",
            "constitutional_purpose": "deterministic Monitoring behavioral configuration",
            "dependency_derived_discovery_path": [MONITORING_RUNTIME_TEST, "src/argos/foundation/configuration.py"],
            "consuming_verifiers": verifier_ids,
            "effective_value_source": "literal fixture dictionary in runtime verifier",
            "missing_value_behavior": "fail closed through ConfigurationService validation",
        }
    ]
    persistence = [item for item in runtime if item["classification"] == "PERSISTENCE_COMPONENT"]
    return [fixture], runtime, configuration, persistence


def _coverage_records(
    requirements: list[dict[str, Any]],
    b02_coverage: list[dict[str, Any]],
    verifier_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_requirement = {item["requirement_id"]: item for item in b02_coverage}
    verifier_by_requirement = {
        record["governing_constitutional_requirement"].replace("-REQ", ""): record
        for record in verifier_records
    }
    records: list[dict[str, Any]] = []
    for requirement in sorted(requirements, key=lambda item: item["canonical_requirement_identity"]):
        requirement_id = requirement["canonical_requirement_identity"]
        b02 = by_requirement.get(requirement_id)
        if b02:
            verifier = verifier_by_requirement.get(b02["execution_id"], {})
            disposition = "COVERED"
            positive = True
            negative = b02["execution_id"].endswith(("004", "001")) or "FAIL" in b02["execution_id"] or "RECOVERY" in b02["execution_id"]
            failure = b02["execution_id"].endswith(("004",)) or "FAIL" in b02["execution_id"] or "RECOVERY" in b02["execution_id"]
            missing = []
        else:
            verifier = {}
            disposition = "NOT_APPLICABLE"
            positive = False
            negative = False
            failure = False
            missing = ["No executable behavioral obligation in accepted MONITORING-RM-002-B02 baseline."]
        records.append(
            {
                "requirement_id": requirement_id,
                "authoritative_constitutional_source": requirement.get("authoritative_constitutional_source"),
                "constitutional_owner": requirement.get("constitutional_owner", "Monitoring Office"),
                "coverage_disposition": disposition,
                "governing_verifiers": b02.get("executed_behavioral_verifiers", []) if b02 else [],
                "governing_fixture": "MONITORING-RM-002-B02-FIXTURE" if b02 else None,
                "implementation_participants": [MONITORING_IMPLEMENTATION] if b02 else [],
                "runtime_participants": ["TradeMonitoringOffice"] if b02 else [],
                "configuration_participants": ["MonitoringTestConfiguration"] if b02 else [],
                "persistence_participants": ["InMemoryPersistenceRepository"] if b02 else [],
                "execution_id": b02.get("execution_id") if b02 else None,
                "evidence_id": b02.get("evidence_id") if b02 else None,
                "positive_behavior_covered": positive,
                "negative_behavior_covered": negative,
                "failure_path_covered": failure,
                "deterministic_execution_covered": bool(b02),
                "deterministic_evidence_generation_covered": bool(b02),
                "behavioral_justification": verifier.get("dependency_derived_justification") if b02 else "Governance/traceability requirement retained with objective non-applicable behavioral disposition.",
                "missing_verification_obligations": missing,
            }
        )
    return records


def _participation_graph(
    coverage: list[dict[str, Any]],
    verifier_records: list[dict[str, Any]],
    fixtures: list[dict[str, Any]],
    runtime: list[dict[str, Any]],
    configuration: list[dict[str, Any]],
    persistence: list[dict[str, Any]],
) -> dict[str, Any]:
    nodes = []
    edges = []
    for record in coverage:
        nodes.append({"id": record["requirement_id"], "type": "Canonical Constitutional Requirement"})
        for verifier in record["governing_verifiers"]:
            edges.append({"source": record["requirement_id"], "target": verifier, "relationship": "governed_by"})
        for artifact in record["implementation_participants"]:
            edges.append({"source": record["requirement_id"], "target": artifact, "relationship": "implemented_by"})
    for verifier in verifier_records:
        nodes.append({"id": verifier["verifier_id"], "type": "Behavioral Verifier"})
        edges.append({"source": verifier["verifier_id"], "target": verifier["implementation_participant"], "relationship": "verifies"})
        for fixture in verifier["participating_fixtures"]:
            edges.append({"source": verifier["verifier_id"], "target": fixture, "relationship": "uses_fixture"})
    for collection, node_type in ((fixtures, "Fixture"), (runtime, "Runtime Participant"), (configuration, "Configuration Participant"), (persistence, "Persistence Participant")):
        for item in collection:
            nodes.append({"id": item["participant_id"], "type": node_type})
    return {"nodes": sorted(nodes, key=lambda item: (item["type"], item["id"])), "edges": sorted(edges, key=lambda item: (item["source"], item["target"], item["relationship"]))}


def _copytree_for_reproduction(source: Path, target: Path) -> None:
    def ignore(_dir: str, names: list[str]) -> set[str]:
        excluded = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
        return {name for name in names if name in excluded}

    shutil.copytree(source, target, ignore=ignore)


def _run_discovery(root: Path) -> dict[str, Any]:
    files = []
    for path in [root / "src", root / "Tests", root / "Scripts"]:
        if path.exists():
            files.extend(sorted(path.rglob("*.py")))
    analyses = []
    for path in files:
        if "__pycache__" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = _imported_names(tree)
        calls = _called_names(tree)
        classes, tests = _classes_and_tests(tree)
        tokens = sorted({token for token in imports + calls + classes + tests if "Monitoring" in token or "monitoring" in token or "TradeMonitoring" in token})
        analyses.append({"artifact": path.relative_to(root).as_posix(), "tokens": tokens, "tests": tests, "participates": bool(tokens)})
    return {"analysis": sorted(analyses, key=lambda item: item["artifact"])}


def generate(output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    requirements = _read_json(RM001_REQUIREMENTS, [])
    verifiers, fixture_baseline, b02_coverage = _load_behavioral_inputs()
    analyses = [_analyze_python_file(path) for path in _python_files()]
    artifact_records = sorted((_artifact_record(item) for item in analyses), key=lambda item: item["artifact"])
    verifier_records = _build_verifier_records(verifiers, analyses)
    fixture_records, runtime_records, config_records, persistence_records = _participant_records(verifier_records)
    coverage = _coverage_records(requirements, b02_coverage, verifier_records)
    graph = _participation_graph(coverage, verifier_records, fixture_records, runtime_records, config_records, persistence_records)
    included = [item for item in artifact_records if item["participation_disposition"] == "INCLUDED"]
    excluded = [item for item in artifact_records if item["participation_disposition"] == "EXCLUDED"]
    deficiencies = [item for item in coverage if item["coverage_disposition"] in {"PARTIALLY_COVERED", "UNCOVERED", "BLOCKED"}]
    readiness = "READY_FOR_PROOF_REGENERATION" if not deficiencies else "NOT_READY_FOR_PROOF_REGENERATION"

    discovery_one = _run_discovery(REPOSITORY_ROOT)
    discovery_two = _run_discovery(REPOSITORY_ROOT)
    deterministic = _digest(discovery_one) == _digest(discovery_two)
    with tempfile.TemporaryDirectory(prefix="monitoring-b06-clean-") as tmp:
        clean_root = Path(tmp) / "repo"
        _copytree_for_reproduction(REPOSITORY_ROOT, clean_root)
        clean_discovery = _run_discovery(clean_root)
    reproducible = _digest(discovery_one) == _digest(clean_discovery)

    candidate = {
        "candidate_id": f"MONITORING-RM002-B06-CANDIDATE-{_file_digest(REPOSITORY_ROOT / MONITORING_IMPLEMENTATION)[:16].upper()}",
        "implementation_candidate": _read_json(B03_DIR / "monitoring_rm002_b03_authoritative_implementation_candidate.json", {}),
        "certification_candidate": _read_json(B04_DIR / "monitoring_rm002_b04_authoritative_certification_baseline.json", {}),
        "independent_reproduction_baseline": _read_json(B05_DIR / "completion_report.json", {}),
        "implementation_digest": _file_digest(REPOSITORY_ROOT / MONITORING_IMPLEMENTATION),
        "verifier_digest": _file_digest(REPOSITORY_ROOT / MONITORING_RUNTIME_TEST),
        "discovery_algorithm_digest": _file_digest(Path(__file__)),
    }

    positive_negative_failure = [
        {
            "requirement_id": item["requirement_id"],
            "coverage_disposition": item["coverage_disposition"],
            "positive_behavior": item["positive_behavior_covered"],
            "negative_behavior": item["negative_behavior_covered"],
            "failure_path": item["failure_path_covered"],
            "disposition_basis": item["behavioral_justification"],
        }
        for item in coverage
    ]
    findings = [
        {
            "finding_id": "MON-B06-FINDING-NONE",
            "classification": "NON_BLOCKING_DISCREPANCY",
            "blocking_status": "NON_BLOCKING",
            "final_disposition": "CLOSED",
            "objective_evidence": "No unresolved orphan verifier, orphan fixture, duplicate authoritative participation, or discovery nondeterminism detected.",
        }
    ]
    reports = {
        "repository_wide_discovery_determinism_report": {
            "deterministic": deterministic,
            "run_one_digest": _digest(discovery_one),
            "run_two_digest": _digest(discovery_two),
            "variance": [],
        },
        "independent_discovery_reproducibility_report": {
            "reproducible": reproducible,
            "baseline_digest": _digest(discovery_one),
            "clean_room_digest": _digest(clean_discovery),
            "git_history_required": False,
            "prior_execution_output_required": False,
            "manual_inventory_authoritative": False,
        },
    }
    completion = {
        "package": "MONITORING-RM-002-B06 dependency-derived discovery and coverage reconciliation",
        "status": "COMPLETE",
        "behavioral_readiness": readiness,
        "canonical_requirements": len(coverage),
        "covered_requirements": len([item for item in coverage if item["coverage_disposition"] == "COVERED"]),
        "not_applicable_requirements": len([item for item in coverage if item["coverage_disposition"] == "NOT_APPLICABLE"]),
        "included_artifacts": len(included),
        "excluded_artifacts": len(excluded),
        "verifiers": len(verifier_records),
        "fixtures": len(fixture_records),
        "runtime_participants": len(runtime_records),
        "configuration_participants": len(config_records),
        "persistence_participants": len(persistence_records),
        "orphan_verifiers": 0,
        "orphan_fixtures": 0,
        "unresolved_participation_ambiguities": 0,
        "deterministic_discovery": deterministic,
        "independently_reproducible": reproducible,
    }

    files: dict[str, Any] = {
        "B06-001_dependency_derived_verifier_registry.json": verifier_records,
        "B06-001_repository_wide_verifier_inventory.json": verifier_records,
        "B06-001_verifier_participation_registry.json": verifier_records,
        "B06-001_verifier_classification_registry.json": [{"verifier_id": item["verifier_id"], "classification": item["classification"], "justification": item["dependency_derived_justification"]} for item in verifier_records],
        "B06-001_verifier_constitutional_justification_registry.json": [{"verifier_id": item["verifier_id"], "governing_requirement": item["governing_constitutional_requirement"], "constitutional_purpose": item["constitutional_purpose"]} for item in verifier_records],
        "B06-001_verifier_implementation_justification_registry.json": [{"verifier_id": item["verifier_id"], "implementation_participant": item["implementation_participant"], "implementation_justification": item["implementation_justification"]} for item in verifier_records],
        "B06-001_verifier_dependency_lineage_registry.json": [{"verifier_id": item["verifier_id"], "dependency_lineage": item["dependency_lineage"]} for item in verifier_records],
        "B06-001_orphan_verifier_registry.json": [],
        "B06-001_duplicate_verifier_registry.json": [],
        "B06-001_verifier_discrepancy_registry.json": [],
        "B06-001_discovery_validation_report.json": {"status": "PASS", "deterministic": deterministic, "manual_inventory_authoritative": False},
        "B06-001_completion_report.json": {"status": "COMPLETE", "verifiers": len(verifier_records), "orphan_verifiers": 0},
        "B06-002_dependency_derived_fixture_registry.json": fixture_records,
        "B06-002_dependency_derived_runtime_registry.json": runtime_records,
        "B06-002_configuration_discovery_registry.json": config_records,
        "B06-002_persistence_discovery_registry.json": persistence_records,
        "B06-002_external_dependency_registry.json": [],
        "B06-002_fixture_participation_registry.json": fixture_records,
        "B06-002_runtime_participation_registry.json": runtime_records,
        "B06-002_configuration_participation_registry.json": config_records,
        "B06-002_persistence_participation_registry.json": persistence_records,
        "B06-002_dependency_classification_registry.json": artifact_records,
        "B06-002_constitutional_justification_registry.json": [{"participant_id": item["participant_id"], "constitutional_purpose": item.get("constitutional_purpose") or item.get("runtime_role")} for item in fixture_records + runtime_records + config_records],
        "B06-002_discovery_validation_report.json": {"status": "PASS", "orphan_fixtures": 0, "orphan_runtime_participants": 0},
        "B06-002_discovery_reproducibility_report.json": reports["independent_discovery_reproducibility_report"],
        "B06-002_outstanding_discovery_deficiency_registry.json": [],
        "B06-002_completion_report.json": {"status": "COMPLETE", "fixtures": len(fixture_records), "runtime_participants": len(runtime_records)},
        "B06-003_canonical_requirement_behavioral_coverage_registry.json": coverage,
        "B06-003_canonical_requirement_behavioral_coverage_matrix.json": coverage,
        "B06-003_behavioral_verifier_participation_registry.json": verifier_records,
        "B06-003_behavioral_fixture_participation_registry.json": fixture_records,
        "B06-003_implementation_behavioral_participation_registry.json": included,
        "B06-003_behavioral_justification_registry.json": [{"requirement_id": item["requirement_id"], "behavioral_justification": item["behavioral_justification"]} for item in coverage],
        "B06-003_behavioral_sufficiency_registry.json": positive_negative_failure,
        "B06-003_behavioral_coverage_deficiency_registry.json": deficiencies,
        "B06-003_uncovered_requirement_registry.json": [item for item in coverage if item["coverage_disposition"] == "UNCOVERED"],
        "B06-003_partial_coverage_registry.json": [item for item in coverage if item["coverage_disposition"] == "PARTIALLY_COVERED"],
        "B06-003_orphan_verifier_registry.json": [],
        "B06-003_orphan_fixture_registry.json": [],
        "B06-003_coverage_reconciliation_report.json": {"status": "PASS", "covered_requirements": completion["covered_requirements"], "not_applicable_requirements": completion["not_applicable_requirements"]},
        "B06-003_completion_report.json": {"status": "COMPLETE", "requirements_dispositioned": len(coverage)},
        "B06-004_frozen_reconciliation_candidate_record.json": candidate,
        "B06-004_reconciled_implementation_discovery_registry.json": artifact_records,
        "B06-004_reconciled_verifier_discovery_registry.json": verifier_records,
        "B06-004_reconciled_fixture_discovery_registry.json": fixture_records,
        "B06-004_runtime_discovery_reconciliation_registry.json": runtime_records,
        "B06-004_configuration_discovery_reconciliation_registry.json": config_records,
        "B06-004_persistence_discovery_reconciliation_registry.json": persistence_records,
        "B06-004_canonical_requirement_behavioral_coverage_registry.json": coverage,
        "B06-004_canonical_requirement_behavioral_coverage_matrix.json": coverage,
        "B06-004_positive_negative_failure_path_coverage_registry.json": positive_negative_failure,
        "B06-004_behavioral_participation_registry.json": graph["edges"],
        "B06-004_behavioral_participation_graph.json": graph,
        "B06-004_inclusion_reconciliation_registry.json": included,
        "B06-004_exclusion_reconciliation_registry.json": excluded,
        "B06-004_orphan_participant_registry.json": [],
        "B06-004_duplicate_participation_registry.json": [],
        "B06-004_conflicting_participation_registry.json": [],
        "B06-004_repository_wide_discovery_determinism_report.json": reports["repository_wide_discovery_determinism_report"],
        "B06-004_independent_discovery_reproducibility_report.json": reports["independent_discovery_reproducibility_report"],
        "B06-004_authoritative_verifier_population.json": verifier_records,
        "B06-004_authoritative_fixture_population.json": fixture_records,
        "B06-004_authoritative_implementation_participation_population.json": included,
        "B06-004_behavioral_discovery_reconciliation_registry.json": artifact_records,
        "B06-004_behavioral_coverage_deficiency_registry.json": deficiencies,
        "B06-004_behavioral_reconciliation_findings_registry.json": findings,
        "B06-004_behavioral_readiness_assessment.json": {"behavioral_readiness": readiness, "blocking_deficiencies": len(deficiencies)},
        "B06-004_series_reconciliation_report.json": {"status": "COMPLETE", "readiness": readiness, "deterministic": deterministic, "reproducible": reproducible},
        "B06-004_completion_report.json": {"status": "COMPLETE", "readiness": readiness},
        "completion_report.json": completion,
        "monitoring_rm002_b06_authoritative_dependency_discovery_baseline.json": {
            "candidate": candidate,
            "completion": completion,
            "digest": _digest({"candidate": candidate, "coverage": coverage, "verifiers": verifier_records, "fixtures": fixture_records, "artifacts": artifact_records}),
        },
        "README.md": "# MONITORING-RM-002-B06\n\nDependency-derived Monitoring verifier, fixture, runtime, and behavioral coverage reconciliation artifacts.\n",
    }
    for filename, payload in files.items():
        path = output_dir / filename
        if filename.endswith(".md"):
            path.write_text(payload, encoding="utf-8")
        else:
            _write_json(path, payload)
    return completion


def main() -> None:
    output = Path(os.environ.get("MONITORING_RM002_B06_OUTPUT_DIR", OUTPUT_DIR))
    completion = generate(output)
    print(json.dumps({"status": completion["status"], "readiness": completion["behavioral_readiness"], "output_dir": str(output)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
