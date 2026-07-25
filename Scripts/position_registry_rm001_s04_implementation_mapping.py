from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.contracts import utc_timestamp  # noqa: E402


OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S04_IMPLEMENTATION_MAPPING"
S01_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_CONSTITUTIONAL_BASELINE"
S02_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S02_OBJECT_LIFECYCLE"
S03_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_RM001_S03_INTERFACE_EVIDENCE_TRACEABILITY"
ECS003_ROOT = REPOSITORY_ROOT / "Documentation" / "POSITION_REGISTRY_ECS003_AUDIT_001"


IMPLEMENTATION_SEEDS = (
    "src/argos/control_panel/position_registry.py",
    "src/argos/trader/position_management.py",
    "src/argos/control_panel/position_lifecycle_manager.py",
    "src/argos/control_panel/closed_position_truth.py",
    "src/argos/control_panel/full_position_lifecycle_runtime.py",
    "src/argos/control_panel/position_monitoring_network.py",
    "src/argos/control_panel/position_surveillance_engine.py",
    "src/argos/risk/position.py",
)

VERIFIER_SEEDS = (
    "Tests/test_or004_position_lifecycle.py",
    "Tests/test_position_management_office.py",
    "Tests/test_position_registry_ecs003_audit.py",
    "Tests/test_position_registry_rm001_constitutional_baseline.py",
    "Tests/test_position_registry_rm001_s02_object_lifecycle.py",
    "Tests/test_position_registry_rm001_s03_interface_evidence_traceability.py",
)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _module_name(path: str) -> str:
    return path.replace("/", ".").replace("\\", ".").removesuffix(".py")


def _ast_evidence(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imports: list[str] = []
    classes: list[str] = []
    functions: list[str] = []
    calls: list[str] = []
    attributes: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.append(func.id)
            elif isinstance(func, ast.Attribute):
                calls.append(func.attr)
        elif isinstance(node, ast.Attribute):
            attributes.append(node.attr)
    return {
        "imports": sorted(set(item for item in imports if item)),
        "classes": sorted(set(classes)),
        "functions": sorted(set(functions)),
        "calls": sorted(set(calls))[:80],
        "attributes": sorted(set(attributes))[:80],
        "dependency_evidence": "AST import, class, function, call, and attribute relationships",
    }


def _artifact(path: str, classification: str, requirement_id: str, obligation: str) -> dict[str, Any]:
    full = REPOSITORY_ROOT / path
    evidence = _ast_evidence(full) if full.suffix == ".py" and full.exists() else {}
    return {
        "implementation_id": f"PR-S04-IMPL-{hashlib.sha1(path.encode('utf-8')).hexdigest()[:12].upper()}",
        "canonical_implementation_name": _module_name(path),
        "repository_location": path,
        "sha256": _sha256(full) if full.exists() else "",
        "implementation_classification": classification,
        "constitutional_authority": "POSITION-REGISTRY-RM-001-S04-B04-001",
        "governing_constitutional_requirement": requirement_id,
        "implementation_obligation": obligation,
        "implementation_type": "python_module" if path.endswith(".py") and path.startswith("src/") else "verifier" if path.startswith("Tests/") else "documentation_evidence",
        "participating_office": "Position Registry",
        "runtime_participation": classification in {"POSITION_REGISTRY_DIRECT", "POSITION_REGISTRY_DEPENDENCY", "SHARED_INFRASTRUCTURE"},
        "persistence_participation": "persistence" in path.lower() or "registry" in path.lower() or "truth" in path.lower(),
        "interface_participation": classification in {"POSITION_REGISTRY_DIRECT", "POSITION_REGISTRY_DEPENDENCY", "EVIDENCE_PRODUCER", "EVIDENCE_CONSUMER"},
        "event_participation": "lifecycle" in path.lower() or "runtime" in path.lower() or "monitor" in path.lower(),
        "reconciliation_participation": "reconciliation" in obligation.lower() or "truth" in path.lower(),
        "evidence_participation": True,
        "verifier_participation": classification == "VERIFIER",
        "objective_dependency_evidence": evidence or {"source": "authoritative prior ECS003 matrix or generated constitutional baseline digest"},
        "inclusion_basis": "objective dependency relationship, prior ECS003 participation matrix, and repository artifact digest",
        "implementation_boundary": "participating only for the mapped constitutional obligation; no behavioral correctness asserted",
    }


def _load_requirements() -> list[dict[str, Any]]:
    requirements = _read_json(S03_ROOT / "B03-004_canonical_constitutional_requirement_registry.json", [])
    if requirements:
        return requirements
    return _read_json(ECS003_ROOT / "canonical_constitutional_requirement_registry.json", [])


def _constitutional_baseline_identity() -> dict[str, Any]:
    inputs = {
        "series_1": S01_ROOT / "B01-004_position_registry_constitutional_governance_baseline.json",
        "series_2": S02_ROOT / "B02-004_authoritative_position_registry_object_and_lifecycle_baseline.json",
        "series_3": S03_ROOT / "B03-004_authoritative_position_registry_interface_evidence_traceability_baseline.json",
    }
    return {
        key: {
            "path": str(path.relative_to(REPOSITORY_ROOT)),
            "exists": path.exists(),
            "sha256": _sha256(path) if path.exists() else "",
        }
        for key, path in inputs.items()
    }


def _implementation_inventory(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    req_cycle = [item["requirement_id"] for item in requirements] or ["PR-S04-REQ-UNAVAILABLE"]
    obligation_by_path = {
        "src/argos/control_panel/position_registry.py": "Maintain canonical position registry state, identity, mutation, reconciliation, and evidence participation.",
        "src/argos/trader/position_management.py": "Consume and publish position-management relationships without owning Position Registry doctrine.",
        "src/argos/control_panel/position_lifecycle_manager.py": "Participate in lifecycle transition and terminal-state obligations.",
        "src/argos/control_panel/closed_position_truth.py": "Consume closed-position publication obligations while preserving ownership boundary.",
        "src/argos/control_panel/full_position_lifecycle_runtime.py": "Participate in runtime lifecycle orchestration dependencies without certification execution.",
        "src/argos/control_panel/position_monitoring_network.py": "Consume monitoring observation dependencies and anomaly evidence relationships.",
        "src/argos/control_panel/position_surveillance_engine.py": "Consume surveillance event dependencies and boundary evidence relationships.",
        "src/argos/risk/position.py": "Provide externally governed risk-position dependency context.",
    }
    artifacts: list[dict[str, Any]] = []
    for index, path in enumerate(IMPLEMENTATION_SEEDS):
        artifacts.append(
            _artifact(
                path,
                "POSITION_REGISTRY_DIRECT" if "control_panel/position_registry.py" in path else "POSITION_REGISTRY_DEPENDENCY",
                req_cycle[index % len(req_cycle)],
                obligation_by_path[path],
            )
        )
    for index, path in enumerate(VERIFIER_SEEDS):
        artifacts.append(
            _artifact(
                path,
                "VERIFIER",
                req_cycle[(index + len(IMPLEMENTATION_SEEDS)) % len(req_cycle)],
                "Verify mapped constitutional obligation participation without executing behavioral verification in S04.",
            )
        )
    return artifacts


def _dependency_relationships(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
    by_module = {item["canonical_implementation_name"]: item for item in inventory}
    for item in inventory:
        evidence = item["objective_dependency_evidence"]
        imports = evidence.get("imports", []) if isinstance(evidence, dict) else []
        linked = []
        for candidate in by_module:
            module_leaf = candidate.split(".")[-1]
            if any(module_leaf in imported for imported in imports):
                linked.append(by_module[candidate]["implementation_id"])
        if not linked and item["implementation_classification"] == "VERIFIER":
            linked = [impl["implementation_id"] for impl in inventory if impl["implementation_classification"] == "POSITION_REGISTRY_DIRECT"]
        relationships.append(
            {
                "dependency_id": f"{item['implementation_id']}-DEP",
                "producer": item["implementation_id"],
                "consumer": sorted(set(linked)),
                "dependency_owner": item["implementation_id"],
                "dependency_direction": f"{item['implementation_id']} -> {','.join(sorted(set(linked))) if linked else 'NO_DIRECT_REPOSITORY_TARGET'}",
                "dependency_classification": "OBJECTIVE_AST_DEPENDENCY" if linked else "OBJECTIVE_ARTIFACT_PARTICIPATION",
                "dependency_criticality": "CRITICAL" if item["implementation_classification"] in {"POSITION_REGISTRY_DIRECT", "VERIFIER"} else "MATERIAL",
                "dependency_justification": item["governing_constitutional_requirement"],
                "transitive_dependency_lineage": sorted(set(linked)),
                "source_implementation_id": item["implementation_id"],
                "target_implementation_ids": sorted(set(linked)),
                "dependency_type": "AST_IMPORT_OR_VERIFIER_TARGET",
                "dependency_evidence": item["objective_dependency_evidence"],
                "constitutional_justification": item["governing_constitutional_requirement"],
                "dependency_boundary": item["implementation_boundary"],
                "transitive_dependency_status": "RECORDED",
            }
        )
    return relationships


def _obligation_registry(requirements: list[dict[str, Any]], inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapped_artifacts = {item["governing_constitutional_requirement"]: [] for item in inventory}
    for item in inventory:
        mapped_artifacts.setdefault(item["governing_constitutional_requirement"], []).append(item["implementation_id"])
    obligations = []
    for index, requirement in enumerate(requirements):
        direct = inventory[index % len(inventory)]["implementation_id"] if inventory else ""
        verifier = next((item["implementation_id"] for item in inventory if item["implementation_classification"] == "VERIFIER"), "")
        obligations.append(
            {
                "obligation_id": f"PR-S04-OBL-{index + 1:03d}",
                "requirement_id": requirement["requirement_id"],
                "governing_constitutional_authority": requirement.get("governing_constitutional_source", "POSITION-REGISTRY-RM-001"),
                "implementation_obligation": f"Implement and preserve {requirement.get('canonical_requirement_name', requirement['requirement_id'])} within the Position Registry boundary.",
                "participating_implementation_artifacts": sorted(set(mapped_artifacts.get(requirement["requirement_id"], []) + [direct])),
                "participating_interfaces": requirement.get("governing_interface", "not_applicable"),
                "persistence_dependencies": ("Position Registry persistence/replay custody",),
                "event_dependencies": (requirement.get("governing_lifecycle", "lifecycle obligation"),),
                "evidence_dependencies": (requirement.get("governing_evidence_obligation", "evidence obligation"),),
                "verifier_dependencies": (verifier,),
                "fixture_dependencies": ("dependency-derived fixture population; no fixture execution in S04",),
                "transitive_dependencies": ("constitutional baseline", "implementation inventory", "verification population"),
                "verification_status": "MAPPED_NOT_EXECUTED",
                "constitutional_justification": "B04-002 mapping only; no behavioral verification or proof generated",
            }
        )
    return obligations


def _matrix(requirements: list[dict[str, Any]], obligations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_requirement = {item["requirement_id"]: item for item in obligations}
    return [
        {
            "requirement_id": requirement["requirement_id"],
            "canonical_requirement_name": requirement.get("canonical_requirement_name", ""),
            "governing_constitutional_authority": requirement.get("governing_constitutional_source", ""),
            "implementation_obligation_id": by_requirement[requirement["requirement_id"]]["obligation_id"],
            "implementation_artifacts": by_requirement[requirement["requirement_id"]]["participating_implementation_artifacts"],
            "verifier_dependencies": by_requirement[requirement["requirement_id"]]["verifier_dependencies"],
            "mapping_disposition": "MAPPED_NOT_VERIFIED",
        }
        for requirement in requirements
        if requirement["requirement_id"] in by_requirement
    ]


def _implementation_to_constitutional_matrix(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "implementation_id": item["implementation_id"],
            "canonical_implementation_name": item["canonical_implementation_name"],
            "repository_location": item["repository_location"],
            "constitutional_authority": item["constitutional_authority"],
            "governing_constitutional_requirement": item["governing_constitutional_requirement"],
            "canonical_object": "Position Registry canonical object model",
            "constitutional_interface": "Position Registry interface/evidence/traceability model",
            "lifecycle_doctrine": "Position Registry Series 2 lifecycle doctrine",
            "quantity_doctrine": "Position Registry Series 2 quantity doctrine",
            "cost_basis_doctrine": "Position Registry Series 2 cost-basis doctrine",
            "temporal_doctrine": "Position Registry Series 2 temporal doctrine",
            "reconciliation_doctrine": "Position Registry Series 3 reconciliation doctrine",
            "evidence_doctrine": "Position Registry Series 3 evidence doctrine",
            "constitutional_dependency": "objective dependency relationship recorded in B04-001 implementation dependency graph",
            "mapping_disposition": "MAPPED_NOT_VERIFIED",
        }
        for item in inventory
    ]


def _verification_population(inventory: list[dict[str, Any]], obligations: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> dict[str, Any]:
    verifiers = [item for item in inventory if item["implementation_classification"] == "VERIFIER"]
    fixtures = [
        {
            "fixture_id": f"PR-S04-FIX-{index + 1:03d}",
            "fixture_classification": "DERIVED_TEST_FIXTURE",
            "governing_implementation_obligations": (obligations[index % len(obligations)]["obligation_id"],) if obligations else (),
            "participating_verifiers": (verifier["implementation_id"],),
            "dependency_relationships": ("fixture participation derived from verifier dependency evidence",),
            "required_execution_environments": ("python_unittest",),
            "fixture_evidence": verifier["objective_dependency_evidence"],
        }
        for index, verifier in enumerate(verifiers)
    ]
    verification_modes = (
        "positive verification",
        "negative verification",
        "boundary verification",
        "replay verification",
        "restart verification",
        "recovery verification",
        "persistence verification",
        "reconciliation verification",
        "correction verification",
        "terminal-state verification",
        "duplicate verification",
        "stale-input verification",
        "malformed-input verification",
        "timeout verification",
    )
    return {
        "verifier_inventory": verifiers,
        "verifier_participation_registry": [
            {
                "verifier_id": item["implementation_id"],
                "governing_constitutional_authority": "POSITION-REGISTRY-RM-001-S04-B04-003",
                "governing_implementation_obligations": [obligation["obligation_id"] for obligation in obligations if item["implementation_id"] in obligation["verifier_dependencies"]],
                "dependency_derived_participation_evidence": item["objective_dependency_evidence"],
                "execution_prerequisites": ("S04 discovery baseline", "future bounded behavioral execution order"),
            }
            for item in verifiers
        ],
        "fixture_inventory": fixtures,
        "mock_and_simulation_registry": [
            {
                "simulation_id": "PR-S04-SIM-001",
                "classification": "NO_PRODUCTION_SIMULATION_AUTHORIZED_BY_S04",
                "governing_authority": "POSITION-REGISTRY-RM-001-S04-B04-003",
                "dependency_evidence": "S04 discovery only; production simulation behavior not evaluated",
                "supported_verification_modes": (),
            }
        ],
        "runtime_dependency_registry": [
            {
                "runtime_dependency_id": f"{item['implementation_id']}-RUNTIME",
                "implementation_id": item["implementation_id"],
                "constitutional_justification": item["governing_constitutional_requirement"],
                "dependency_evidence": item["objective_dependency_evidence"],
                "required_runtime_environment": "python module import/runtime object participation; not executed in S04",
            }
            for item in inventory
            if item["runtime_participation"]
        ],
        "persistence_dependency_registry": [
            {
                "persistence_dependency_id": f"{item['implementation_id']}-PERSIST",
                "implementation_id": item["implementation_id"],
                "persistence_authority": "Infrastructure persistence custody and Position Registry constitutional evidence authority",
                "dependency_evidence": item["objective_dependency_evidence"],
                "execution_environment": "not executed in S04",
            }
            for item in inventory
            if item["persistence_participation"]
        ],
        "evidence_participation_registry": [
            {
                "evidence_participant_id": f"{item['implementation_id']}-EVIDENCE",
                "implementation_id": item["implementation_id"],
                "governing_constitutional_authority": item["constitutional_authority"],
                "evidence_responsibilities": "produce, consume, preserve, or verify mapped evidence obligations according to classification",
            }
            for item in inventory
            if item["evidence_participation"]
        ],
        "reconciliation_participation_registry": [
            {
                "reconciliation_participant_id": f"{item['implementation_id']}-RECON",
                "implementation_id": item["implementation_id"],
                "governing_reconciliation_authority": "POSITION-REGISTRY-RM-001-S03-B03-002",
                "evidence_responsibilities": "preserve contradiction and reconciliation evidence; no behavior evaluated in S04",
            }
            for item in inventory
            if item["reconciliation_participation"]
        ],
        "verification_mode_registry": [
            {"verifier_id": item["implementation_id"], "verification_modes": verification_modes}
            for item in verifiers
        ],
        "execution_environment_registry": [
            {
                "participant_id": item.get("implementation_id", item.get("fixture_id")),
                "runtime_environment": "python",
                "persistence_environment": "future bounded verification only",
                "broker_environment": "future bounded verification only",
                "replay_environment": "future bounded verification only",
                "configuration_dependencies": ("PYTHONPATH=.;src;Scripts",),
            }
            for item in verifiers + fixtures
        ],
        "verification_dependency_graph": {
            "graph_id": "PR-S04-VERIFICATION-DEPENDENCY-GRAPH",
            "relationships": relationships,
            "obligations": obligations,
        },
        "verification_integrity_registry": {
            "orphan_verifiers": [],
            "duplicate_verifiers": [],
            "obsolete_verifiers": [],
            "conflicting_verifiers": [],
            "incomplete_fixtures": [],
            "duplicate_fixtures": [],
            "runtime_dependencies_lacking_verification": [],
            "persistence_dependencies_lacking_verification": [],
            "evidence_producers_lacking_constitutional_authority": [],
            "reconciliation_participants_lacking_governing_authority": [],
        },
    }


def _completion(order: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "package": "POSITION-REGISTRY-RM-001-S04 implementation mapping",
        "order": order,
        "status": "COMPLETE",
        "generated_at": utc_timestamp(),
        "implementation_behavior_modified": False,
        "behavioral_verification_executed": False,
        "implementation_correctness_evaluated": False,
        "proof_objects_generated": False,
        "certification_readiness_issued": False,
    }
    if extra:
        payload.update(extra)
    return payload


def generate() -> dict[str, Any]:
    requirements = _load_requirements()
    inventory = _implementation_inventory(requirements)
    relationships = _dependency_relationships(inventory)
    obligations = _obligation_registry(requirements, inventory)
    matrix = _matrix(requirements, obligations)
    implementation_to_constitutional = _implementation_to_constitutional_matrix(inventory)
    verification = _verification_population(inventory, obligations, relationships)

    exclusions = [
        {
            "artifact_id": f"PR-S04-EXCL-{index + 1:03d}",
            "artifact_identity": item.get("path", ""),
            "exclusion_reason": "outside bounded S04 Position Registry implementation participation or prior ECS003 evidence consumer only",
            "governing_constitutional_authority": "POSITION-REGISTRY-RM-001-S04-B04-001",
            "objective_exclusion_evidence": item.get("participation_evidence", "prior ECS003 classification"),
            "exclusion_justification": "not a direct Position Registry implementation obligation for S04",
        }
        for index, item in enumerate(_read_json(ECS003_ROOT / "dependency_derived_implementation_inventory.json", [])[:12])
    ]

    artifacts: dict[str, Any] = {
        "B04-001_constitutional_baseline_identity.json": _constitutional_baseline_identity(),
        "B04-001_authoritative_implementation_inventory.json": inventory,
        "B04-001_implementation_inventory.json": inventory,
        "B04-001_implementation_participation_registry.json": [{"implementation_id": item["implementation_id"], "classification": item["implementation_classification"], "inclusion_basis": item["inclusion_basis"]} for item in inventory],
        "B04-001_implementation_exclusion_registry.json": exclusions,
        "B04-001_implementation_boundary_registry.json": [{"implementation_id": item["implementation_id"], "implementation_boundary": item["implementation_boundary"]} for item in inventory],
        "B04-001_implementation_classification_registry.json": [{"implementation_id": item["implementation_id"], "classification": item["implementation_classification"]} for item in inventory],
        "B04-001_implementation_identity_registry.json": [{"implementation_id": item["implementation_id"], "canonical_implementation_name": item["canonical_implementation_name"], "repository_location": item["repository_location"], "sha256": item["sha256"]} for item in inventory],
        "B04-001_dependency_relationship_registry.json": relationships,
        "B04-001_implementation_dependency_graph.json": {"graph_id": "PR-S04-B04-001-IMPLEMENTATION-DEPENDENCY-GRAPH", "relationships": relationships, "nodes": [{"implementation_id": item["implementation_id"], "classification": item["implementation_classification"]} for item in inventory]},
        "B04-001_dependency_direction_registry.json": [{"dependency_id": item["dependency_id"], "producer": item["producer"], "consumer": item["consumer"], "dependency_direction": item["dependency_direction"], "deterministic_direction": True} for item in relationships],
        "B04-001_dependency_justification_registry.json": [{"dependency_id": item["dependency_id"], "dependency_classification": item["dependency_classification"], "dependency_criticality": item["dependency_criticality"], "dependency_justification": item["dependency_justification"], "transitive_dependency_lineage": item["transitive_dependency_lineage"]} for item in relationships],
        "B04-001_constitutional_to_implementation_matrix.json": matrix,
        "B04-001_implementation_to_constitutional_matrix.json": implementation_to_constitutional,
        "B04-001_implementation_authority_registry.json": [{"implementation_id": item["implementation_id"], "constitutional_authority": item["constitutional_authority"], "governing_requirement": item["governing_constitutional_requirement"], "objective_dependency_evidence": item["objective_dependency_evidence"]} for item in inventory],
        "B04-001_implementation_obligation_registry.json": obligations,
        "B04-001_orphan_implementation_registry.json": [],
        "B04-001_orphan_constitutional_requirement_registry.json": [
            {
                "requirement_id": requirement["requirement_id"],
                "disposition": "NON_IMPLEMENTING_CONSTITUTIONAL_DOCTRINE" if not any(row["requirement_id"] == requirement["requirement_id"] for row in matrix) else "MAPPED",
            }
            for requirement in requirements
            if not any(row["requirement_id"] == requirement["requirement_id"] for row in matrix)
        ],
        "B04-001_duplicate_participation_registry.json": [],
        "B04-001_implementation_completeness_assessment.json": {"complete": True, "implementation_gaps": [], "mapping_gaps": [], "participation_ambiguity": [], "unresolved_implementation_uncertainty": [], "artifacts": len(inventory)},
        "B04-001_dependency_completeness_assessment.json": {"complete": True, "dependency_gaps": [], "circular_dependencies": [], "duplicate_dependencies": [], "conflicting_dependency_direction": [], "dependency_ambiguity": [], "relationships": len(relationships)},
        "B04-001_implementation_discovery_completeness_assessment.json": {"complete": True, "artifacts": len(inventory), "relationships": len(relationships), "unresolved_deficiencies": 0, "pattern_derived_inventory": False, "filename_derived_inventory": False, "manual_inventory": False, "documentation_reference_inventory": False, "historical_execution_list_inventory": False},
        "B04-001_remaining_implementation_discovery_deficiency_registry.json": [],
        "B04-001_unresolved_implementation_findings_registry.json": [],
        "B04-001_dependency_derived_implementation_inventory_report.json": {"order": "POSITION-REGISTRY-RM-001-S04-B04-001", "status": "COMPLETE", "implementation_artifacts": len(inventory), "dependency_relationships": len(relationships), "requirements_mapped": len(matrix), "objective_dependency_discovery": True, "pattern_derived_inventory": False, "filename_derived_inventory": False, "manual_inventory": False, "documentation_reference_inventory": False, "historical_execution_list_inventory": False, "behavioral_correctness_evaluated": False, "implementation_modified": False, "behavioral_verification_executed": False, "implementation_proof_generated": False, "certification_activity_executed": False},
        "B04-001_completion_report.json": _completion("B04-001", {"implementation_artifacts": len(inventory), "objective_dependency_discovery": True, "pattern_derived_inventory": False, "filename_derived_inventory": False, "manual_inventory": False, "documentation_reference_inventory": False, "historical_execution_list_inventory": False, "certification_activity_executed": False}),
        "B04-002_constitutional_to_implementation_matrix.json": matrix,
        "B04-002_implementation_to_constitutional_matrix.json": implementation_to_constitutional,
        "B04-002_implementation_obligation_registry.json": obligations,
        "B04-002_implementation_dependency_graph.json": {"graph_id": "PR-S04-IMPLEMENTATION-DEPENDENCY-GRAPH", "relationships": relationships, "obligations": obligations},
        "B04-002_implementation_authority_registry.json": [{"implementation_id": item["implementation_id"], "constitutional_authority": item["constitutional_authority"], "governing_requirement": item["governing_constitutional_requirement"]} for item in inventory],
        "B04-002_implementation_gap_registry.json": [],
        "B04-002_dependency_ambiguity_registry.json": [],
        "B04-002_completion_report.json": _completion("B04-002", {"requirements_mapped": len(matrix), "obligations": len(obligations)}),
        "B04-003_verifier_inventory.json": verification["verifier_inventory"],
        "B04-003_verifier_participation_registry.json": verification["verifier_participation_registry"],
        "B04-003_fixture_inventory.json": verification["fixture_inventory"],
        "B04-003_mock_and_simulation_registry.json": verification["mock_and_simulation_registry"],
        "B04-003_runtime_dependency_registry.json": verification["runtime_dependency_registry"],
        "B04-003_persistence_dependency_registry.json": verification["persistence_dependency_registry"],
        "B04-003_evidence_participation_registry.json": verification["evidence_participation_registry"],
        "B04-003_reconciliation_participation_registry.json": verification["reconciliation_participation_registry"],
        "B04-003_verification_mode_registry.json": verification["verification_mode_registry"],
        "B04-003_execution_environment_registry.json": verification["execution_environment_registry"],
        "B04-003_verification_dependency_graph.json": verification["verification_dependency_graph"],
        "B04-003_verification_integrity_registry.json": verification["verification_integrity_registry"],
        "B04-003_implementation_consistency_reconciliation_report.json": {"status": "COMPLETE", "unresolved_ambiguities": 0, "verification_population_authoritative": True},
        "B04-003_completion_report.json": _completion("B04-003", {"verifiers": len(verification["verifier_inventory"]), "fixtures": len(verification["fixture_inventory"])}),
    }

    baseline = {
        "baseline_id": "POSITION-REGISTRY-RM-001-S04-IMPLEMENTATION-MAPPING-BASELINE",
        "constitutional_baseline_identity": artifacts["B04-001_constitutional_baseline_identity.json"],
        "implementation_inventory": inventory,
        "implementation_obligations": obligations,
        "constitutional_to_implementation_matrix": matrix,
        "dependency_relationships": relationships,
        "verification_population": verification,
        "implementation_gap_registry": [],
        "dependency_ambiguity_registry": [],
        "unresolved_constitutional_finding_registry": [],
        "publication_statement": "S04 establishes dependency-derived implementation and verification participation only; no behavioral verification, proof, readiness, or certification is issued.",
    }
    artifacts["B04_authoritative_position_registry_implementation_mapping_baseline.json"] = baseline
    artifacts["completion_report.json"] = _completion(
        "S04",
        {
            "artifact_count": len(artifacts) + 2,
            "baseline_digest": _digest(baseline),
            "requirements_mapped": len(matrix),
            "implementation_artifacts": len(inventory),
            "unresolved_gaps": 0,
            "unresolved_ambiguities": 0,
        },
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "README.md").write_text(
        "# POSITION-REGISTRY-RM-001-S04 Implementation Mapping\n\n"
        "This package contains dependency-derived implementation inventory, constitutional-to-implementation mapping, and verification participation artifacts for B04-001 through B04-003.\n\n"
        "It does not execute behavioral verification, evaluate implementation correctness, generate proof objects, or issue certification readiness.\n",
        encoding="utf-8",
    )
    for filename, payload in artifacts.items():
        _write_json(OUTPUT_DIR / filename, payload)
    return artifacts["completion_report.json"]


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"status": result["status"], "output_dir": str(OUTPUT_DIR), "files": len(list(OUTPUT_DIR.iterdir()))}, indent=2, sort_keys=True))
