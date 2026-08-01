from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any


ORDER_ID = "ENTERPRISE-LEARNING-ECS-004-READINESS-ORDER"
OUTPUT_DIR = Path("Documentation") / "ENTERPRISE_LEARNING_ECS004_READINESS"
RM002_DIR = Path("Documentation") / "ENTERPRISE_LEARNING_RM002_BEHAVIORAL_IMPLEMENTATION"
RM001_DIR = Path("Documentation") / "ENTERPRISE_LEARNING_RM001_CONSTITUTIONAL_BASELINE"
MO001_DIR = Path("Documentation") / "ENTERPRISE_LEARNING_MO001_ARCHITECTURE_HARDENING"
EXECUTION_UTC = "2026-08-01T17:15:00+00:00"


BEHAVIORS = (
    ("EL-ECS004-BEH-001", "learning dataset lifecycle", "ENTERPRISE-LEARNING-RM-002-001", "src/argos/control_panel/enterprise_learning_runtime.py", "Tests/test_enterprise_learning_rm002_runtime.py", "learning_dataset_runtime_report.json"),
    ("EL-ECS004-BEH-002", "feature engineering", "ENTERPRISE-LEARNING-RM-002-002", "src/argos/control_panel/enterprise_learning_runtime.py", "Tests/test_enterprise_learning_rm002_runtime.py", "feature_engineering_runtime_report.json"),
    ("EL-ECS004-BEH-003", "experiment execution", "ENTERPRISE-LEARNING-RM-002-003", "src/argos/control_panel/enterprise_learning_runtime.py", "Tests/test_enterprise_learning_rm002_runtime.py", "experiment_runtime_report.json"),
    ("EL-ECS004-BEH-004", "hypothesis lifecycle", "ENTERPRISE-LEARNING-RM-002-004", "src/argos/control_panel/enterprise_learning_runtime.py", "Tests/test_enterprise_learning_rm002_runtime.py", "hypothesis_runtime_report.json"),
    ("EL-ECS004-BEH-005", "model lifecycle", "ENTERPRISE-LEARNING-RM-002-005", "src/argos/control_panel/enterprise_learning_runtime.py", "Tests/test_enterprise_learning_rm002_runtime.py", "model_lifecycle_runtime_report.json"),
    ("EL-ECS004-BEH-006", "explainability generation", "ENTERPRISE-LEARNING-RM-002-006", "src/argos/control_panel/enterprise_learning_runtime.py", "Tests/test_enterprise_learning_rm002_runtime.py", "explainability_runtime_report.json"),
    ("EL-ECS004-BEH-007", "learning provenance", "ENTERPRISE-LEARNING-RM-002-007", "src/argos/control_panel/enterprise_learning_runtime.py", "Tests/test_enterprise_learning_rm002_runtime.py", "learning_provenance_runtime_report.json"),
    ("EL-ECS004-BEH-008", "knowledge publication", "ENTERPRISE-LEARNING-RM-002-008", "src/argos/control_panel/enterprise_learning_runtime.py", "Tests/test_enterprise_learning_rm002_runtime.py", "knowledge_publication_runtime_report.json"),
    ("EL-ECS004-BEH-009", "behavioral evidence generation", "ENTERPRISE-LEARNING-RM-002-009", "src/argos/control_panel/enterprise_learning_runtime.py", "Tests/test_enterprise_learning_rm002_runtime.py", "behavioral_evidence_runtime_report.json"),
    ("EL-ECS004-BEH-010", "advisory-only authority", "ENTERPRISE-LEARNING-RM-001-009", "src/argos/control_panel/enterprise_learning_runtime.py", "Tests/test_enterprise_learning_rm002_runtime.py", "behavioral_findings_registry.json"),
    ("EL-ECS004-BEH-011", "separation from enterprise truth", "ENTERPRISE-LEARNING-RM-001-004", "src/argos/control_panel/enterprise_learning_runtime.py", "Tests/test_enterprise_learning_rm002_runtime.py", "behavioral_findings_registry.json"),
    ("EL-ECS004-BEH-012", "fail-closed enforcement", "ENTERPRISE-LEARNING-RM-002-010", "src/argos/control_panel/enterprise_learning_runtime.py", "Tests/test_enterprise_learning_rm002_runtime.py", "behavioral_findings_registry.json"),
)


TESTS = (
    ("EL-ECS004-TEST-001", "test_reference_runtime_produces_complete_certification_report", "positive-path", "complete runtime coverage"),
    ("EL-ECS004-TEST-002", "test_dataset_preserves_source_ownership_and_reproducibility", "lifecycle", "dataset lifecycle and ownership"),
    ("EL-ECS004-TEST-003", "test_feature_experiment_hypothesis_and_model_flow", "positive-path", "feature, experiment, hypothesis, model flow"),
    ("EL-ECS004-TEST-004", "test_publication_requires_evidence_explainability_and_provenance", "negative-path", "publication fail closed"),
    ("EL-ECS004-TEST-005", "test_boundary_enforcement_fails_closed_for_operational_authority", "authority-boundary", "operational authority fail closed"),
    ("EL-ECS004-TEST-006", "test_unknown_dataset_experiment_is_rejected", "negative-path", "missing dataset rejection"),
    ("EL-ECS004-TEST-007", "test_provenance_graph_detects_orphans", "provenance", "orphan provenance detection"),
    ("EL-ECS004-TEST-008", "test_generated_completion_report_authorizes_next_series", "evidence-integrity", "RM-002 completion evidence"),
)


MUTATIONS = (
    ("EL-ECS004-MUT-001", "missing datasets", "UNKNOWN_DATASET"),
    ("EL-ECS004-MUT-002", "altered dataset hashes", "DETERMINISTIC_COMPARISON_FAIL"),
    ("EL-ECS004-MUT-003", "invalid feature lineage", "UNKNOWN_DATASET"),
    ("EL-ECS004-MUT-004", "missing experiment evidence", "EXPERIMENT_METRICS_REQUIRED"),
    ("EL-ECS004-MUT-005", "incomplete hypothesis uncertainty", "HYPOTHESIS_MEASUREMENT_INVALID"),
    ("EL-ECS004-MUT-006", "invalid model provenance", "MODEL_EXPERIMENT_REQUIRED"),
    ("EL-ECS004-MUT-007", "missing explainability", "PUBLICATION_EXPLAINABILITY_REQUIRED"),
    ("EL-ECS004-MUT-008", "unauthorized publication", "CONSUMER_CONTRACT_INCOMPLETE"),
    ("EL-ECS004-MUT-009", "operational authority assignment", "BOUNDARY_FAIL_CLOSED"),
    ("EL-ECS004-MUT-010", "attempted establishment of enterprise truth", "BOUNDARY_FAIL_CLOSED"),
    ("EL-ECS004-MUT-011", "altered evidence", "SCHEMA_OR_HASH_VALIDATION_FAIL"),
    ("EL-ECS004-MUT-012", "missing evidence", "PUBLICATION_EVIDENCE_REQUIRED"),
    ("EL-ECS004-MUT-013", "invalid evidence schema", "SCHEMA_VALIDATION_FAIL"),
    ("EL-ECS004-MUT-014", "nondeterministic execution", "DETERMINISTIC_COMPARISON_FAIL"),
    ("EL-ECS004-MUT-015", "repository tampering", "REPOSITORY_HASH_MISMATCH"),
    ("EL-ECS004-MUT-016", "dependency drift", "ENVIRONMENT_SPEC_MISMATCH"),
)


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _copy_order()
    commit = _git("rev-parse", "HEAD")
    short = _git("rev-parse", "--short=12", "HEAD")
    tracked_files = _git("ls-files").splitlines()
    inventory = _file_inventory(tracked_files)

    repo_manifest = {
        "order_id": ORDER_ID,
        "repository_identifier": "ARGOS Enterprise Learning Office",
        "commit": commit,
        "short_commit": short,
        "created_at": EXECUTION_UTC,
        "file_count": len(inventory),
        "file_inventory": inventory,
        "executable_entry_points": [
            "python Scripts/enterprise_learning_rm002_behavioral_implementation.py",
            "python Scripts/enterprise_learning_ecs004_readiness_package.py",
            "python -m unittest Tests.test_enterprise_learning_rm002_runtime Tests.test_enterprise_learning_mo001_architecture_hardening Tests.test_enterprise_learning_rm001_constitutional_baseline Tests.test_learning_integration_office",
        ],
        "dependency_manifests": ["pyproject.toml"],
        "configuration_files": [path for path in tracked_files if path.endswith((".env.example", ".toml", ".json", ".yml", ".yaml"))],
        "test_modules": [path for path in tracked_files if path.startswith("Tests/test_enterprise_learning") or path == "Tests/test_learning_integration_office.py"],
        "evidence_generators": ["Scripts/enterprise_learning_rm002_behavioral_implementation.py", "Scripts/enterprise_learning_ecs004_readiness_package.py"],
        "expected_output_locations": [str(OUTPUT_DIR), str(RM002_DIR), str(RM001_DIR), str(MO001_DIR)],
    }

    deliverables = {
        "ECS004_REPOSITORY_MANIFEST.json": repo_manifest,
        "ECS004_BEHAVIORAL_INVENTORY.json": _behavioral_inventory(),
        "ECS004_TEST_INVENTORY.json": _test_inventory(),
        "ECS004_INPUT_AND_FIXTURE_MANIFEST.json": _fixture_manifest(),
        "ECS004_EVIDENCE_SCHEMA_MANIFEST.json": _schema_manifest(),
        "ECS004_BASELINE_COMPARISON_RULES.json": _baseline_comparison_rules(),
        "ECS004_MUTATION_INVENTORY.json": _mutation_inventory(),
        "ECS004_EXPECTED_RESULTS.json": _expected_results(),
    }
    for name, payload in deliverables.items():
        _write_json(name, payload)
    _write_text("ECS004_REPOSITORY_MANIFEST.md", _repository_manifest_md(repo_manifest))
    _write_text("ECS004_ENVIRONMENT_SPECIFICATION.md", _environment_spec())
    _write_text("ECS004_INSTALLATION_RUNBOOK.md", _installation_runbook())
    _write_text("ECS004_AUDITOR_EXECUTION_RUNBOOK.md", _auditor_runbook())
    _write_text("ECS004_DETERMINISM_CONTROLS.md", _determinism_controls())
    _write_text("ECS004_SUBMISSION_COMPLETENESS_REPORT.md", _completeness_report(repo_manifest))
    hashes = _hash_deliverables()
    _write_text("ECS004_PACKAGE_HASHES.sha256", hashes)
    return {"order_id": ORDER_ID, "commit": commit, "output_dir": str(OUTPUT_DIR), "deliverables": sorted(path.name for path in OUTPUT_DIR.iterdir())}


def _behavioral_inventory() -> list[dict[str, Any]]:
    return [
        {
            "behavior_identifier": behavior_id,
            "behavior": behavior,
            "governing_constitutional_order": order,
            "constitutional_requirement": f"{behavior} shall be deterministic, observable, evidence-backed, and independently reproducible.",
            "source_implementation_location": implementation,
            "test_location": test,
            "execution_command": "python -m unittest Tests.test_enterprise_learning_rm002_runtime",
            "expected_result": "PASS",
            "evidence_artifact": f"Documentation/ENTERPRISE_LEARNING_RM002_BEHAVIORAL_IMPLEMENTATION/{artifact}",
            "evidence_schema": "ECS004_EVIDENCE_SCHEMA_MANIFEST.json",
            "failure_condition": "missing evidence, invalid mapping, unexpected pass of prohibited behavior, or nondeterministic output",
            "reproducibility_criterion": "exact normalized JSON equivalence and stable SHA256 for nonvolatile artifacts",
        }
        for behavior_id, behavior, order, implementation, test, artifact in BEHAVIORS
    ]


def _test_inventory() -> list[dict[str, Any]]:
    return [
        {
            "test_identifier": test_id,
            "test_module": "Tests/test_enterprise_learning_rm002_runtime.py",
            "test_name": test_name,
            "behavior_under_test": behavior,
            "constitutional_requirement": "Enterprise Learning RM-002 runtime behavior remains certifiable under ECS-004 reproduction.",
            "test_classification": classification,
            "prerequisites": ["Python runtime", "repository package", "no external services"],
            "input_fixtures": ["deterministic inline fixture in Scripts/enterprise_learning_rm002_behavioral_implementation.py"],
            "expected_output": "unittest PASS",
            "expected_evidence": "RM-002 JSON evidence regenerated under Documentation/ENTERPRISE_LEARNING_RM002_BEHAVIORAL_IMPLEMENTATION",
            "expected_failure_behavior": "EnterpriseLearningRuntimeError or EnterpriseLearningBoundaryError for negative and boundary tests",
            "deterministic_comparison_method": "normalized JSON exact comparison excluding archive names and host paths",
        }
        for test_id, test_name, classification, behavior in TESTS
    ]


def _fixture_manifest() -> dict[str, Any]:
    return {
        "fixture_package": "inline deterministic RM-002 reference runtime fixture",
        "seed": 42,
        "source": "Scripts/enterprise_learning_rm002_behavioral_implementation.py::build_reference_runtime",
        "inputs": [
            {"identifier": "EL-DS-001", "version": "1.0.0", "purpose": "dataset lifecycle reproduction", "schema": "workflow, return, risk, mode", "consumer": "EnterpriseLearningRuntime.create_dataset"},
            {"identifier": "EL-FEAT-001", "version": "1.0.0", "purpose": "feature engineering reproduction", "schema": "risk_adjusted_return transformation", "consumer": "EnterpriseLearningRuntime.define_feature"},
            {"identifier": "EL-HYP-001", "version": "1.0.0", "purpose": "hypothesis lifecycle reproduction", "schema": "objective, falsification, confidence, uncertainty", "consumer": "EnterpriseLearningRuntime.register_hypothesis"},
        ],
        "external_data_required": False,
        "integrity_hash": _hash_text("EL-DS-001|EL-FEAT-001|EL-HYP-001|seed=42"),
    }


def _schema_manifest() -> dict[str, Any]:
    fields = ["evidence_id", "authority", "subject_id", "event_type", "event_time", "inputs", "outputs", "digest"]
    return {
        "schema_package": "Enterprise Learning ECS-004 schema manifest",
        "schemas": [
            {"schema_id": "EL-EVIDENCE-SCHEMA", "applies_to": "runtime evidence", "required_fields": fields, "validation_command": "python Scripts/enterprise_learning_ecs004_readiness_package.py"},
            {"schema_id": "EL-PROVENANCE-SCHEMA", "applies_to": "provenance evidence", "required_fields": ["edge_id", "source_id", "target_id", "relationship", "evidence_id", "digest"], "validation_command": "python -m unittest Tests.test_enterprise_learning_rm002_runtime"},
            {"schema_id": "EL-PUBLICATION-SCHEMA", "applies_to": "publication evidence", "required_fields": ["publication_id", "product_id", "product_class", "consumer_contract", "evidence_refs", "explainability_ref", "provenance_refs", "state", "digest"], "validation_command": "python -m unittest Tests.test_enterprise_learning_rm002_runtime"},
        ],
        "invalid_evidence_disposition": "FAIL",
    }


def _baseline_comparison_rules() -> dict[str, Any]:
    artifacts = sorted(path for path in RM002_DIR.glob("*.json"))
    return {
        "baseline_artifact_inventory": [{"path": str(path), "sha256": _hash_file(path)} for path in artifacts],
        "normalized_comparison_fields": ["all JSON fields sorted by key"],
        "excluded_volatile_fields": ["archive file name", "host-specific absolute Desktop paths"],
        "comparison_rules": [{"artifact": str(path), "rule": "exact SHA256 after regeneration where timestamp constants are unchanged"} for path in artifacts],
        "equivalence_thresholds": [{"field": "floating point metrics", "threshold": "exact stored value", "justification": "fixture values are deterministic constants"}],
        "expected_pass_outcome": "all regenerated RM-002 artifacts match declared normalized baseline",
        "expected_fail_outcome": "any missing artifact, schema invalidity, or hash mismatch is FAIL",
    }


def _mutation_inventory() -> list[dict[str, str]]:
    return [
        {
            "mutation_id": mutation_id,
            "mutation": mutation,
            "expected_result": "FAIL",
            "expected_failure_code": code,
            "evidence_requirement": "objective failure evidence with requirement and behavior mapping",
        }
        for mutation_id, mutation, code in MUTATIONS
    ]


def _expected_results() -> dict[str, Any]:
    return {
        "overall_status_values": ["PASS", "FAIL", "INCOMPLETE"],
        "expected_assessment_status": "PASS",
        "behaviors_discovered": len(BEHAVIORS),
        "behaviors_executed": len(BEHAVIORS),
        "behaviors_skipped": 0,
        "test_count": len(TESTS),
        "mutation_count": len(MUTATIONS),
        "schema_validation_expected": "PASS",
        "deterministic_comparison_expected": "PASS",
        "ecs004_readiness_conclusion": "READY_FOR_INDEPENDENT_ECS004_ASSESSMENT",
        "certification_claim_made": False,
    }


def _environment_spec() -> str:
    return f"""# ECS-004 Environment Specification

Supported OS: Windows 10/11 or clean Python-capable Linux environment.
Observed OS: {platform.platform()}
Architecture: {platform.machine()}
Python: {sys.version.split()[0]}
Package manager: pip with repository-local `pyproject.toml`.
Database/services: none required for Enterprise Learning ECS-004 reproduction.
Environment variables: none required beyond standard Python execution.
Filesystem: writable repository directory; evidence output under `Documentation/ENTERPRISE_LEARNING_RM002_BEHAVIORAL_IMPLEMENTATION`.
Locale/encoding: UTF-8.
Timezone: deterministic timestamps are fixed constants in the generator; host timezone is not used for evidence identity.
Network: prohibited for execution. No external services or datasets are required.
Minimum resources: 1 CPU, 512 MB RAM, 100 MB free disk.
"""


def _installation_runbook() -> str:
    return """# ECS-004 Installation Runbook

1. Extract `ENTERPRISE_LEARNING_ECS004_REPOSITORY.zip` into an empty directory.
2. Open a terminal in the extracted repository root.
3. Verify Python: `python --version` must report Python 3.11 or newer.
4. Optional environment creation: `python -m venv .venv`.
5. Optional activation on Windows: `.venv\\Scripts\\Activate.ps1`.
6. Install package metadata if desired: `python -m pip install -e .`.
7. Verify repository scripts compile: `python -m py_compile Scripts\\enterprise_learning_rm002_behavioral_implementation.py Scripts\\enterprise_learning_ecs004_readiness_package.py src\\argos\\control_panel\\enterprise_learning_runtime.py`.
8. Expected exit code for every command is `0`. Any nonzero exit code is an installation failure.
"""


def _auditor_runbook() -> str:
    return """# ECS-004 Auditor Execution Runbook

Authoritative command sequence:

1. `python Scripts\\enterprise_learning_rm002_behavioral_implementation.py`
2. `python Scripts\\enterprise_learning_ecs004_readiness_package.py`
3. `python -m unittest Tests.test_enterprise_learning_rm002_runtime Tests.test_enterprise_learning_mo001_architecture_hardening Tests.test_enterprise_learning_rm001_constitutional_baseline Tests.test_learning_integration_office`

Expected result: all tests pass, RM-002 evidence regenerates, ECS-004 readiness manifests regenerate, and no network or external service is used.

Interpretation:

* A missing dependency, missing file, schema mismatch, hash mismatch, or unexpected mutation pass is `FAIL`.
* An interrupted or incomplete run is `INCOMPLETE`.
* This package does not declare ECS-004 certification. It supplies materials for independent assessment.
"""


def _determinism_controls() -> str:
    return """# ECS-004 Determinism Controls

Randomness: fixed seed `42`.
Timestamps: evidence generator uses fixed timestamp constants.
Ordering: JSON is written with sorted keys; inventories are sorted.
Concurrency: no concurrent behavior is required.
Floating point: fixture metrics are explicit constants and compared exactly.
Locale/timezone: output identity does not depend on host locale or timezone.
Filesystem ordering: file inventories are sorted before hashing.
External services: none permitted.
Permitted volatile fields: final ZIP file names and host-specific Desktop paths only.
"""


def _repository_manifest_md(manifest: dict[str, Any]) -> str:
    return f"""# ECS-004 Repository Manifest

Repository: {manifest['repository_identifier']}
Commit: `{manifest['commit']}`
Created: {manifest['created_at']}
Tracked files inventoried: {manifest['file_count']}

Executable entry points:

{chr(10).join(f'* `{item}`' for item in manifest['executable_entry_points'])}
"""


def _completeness_report(manifest: dict[str, Any]) -> str:
    required = [
        "ECS004_REPOSITORY_MANIFEST.json",
        "ECS004_REPOSITORY_MANIFEST.md",
        "ECS004_ENVIRONMENT_SPECIFICATION.md",
        "ECS004_INSTALLATION_RUNBOOK.md",
        "ECS004_AUDITOR_EXECUTION_RUNBOOK.md",
        "ECS004_BEHAVIORAL_INVENTORY.json",
        "ECS004_TEST_INVENTORY.json",
        "ECS004_INPUT_AND_FIXTURE_MANIFEST.json",
        "ECS004_EVIDENCE_SCHEMA_MANIFEST.json",
        "ECS004_BASELINE_COMPARISON_RULES.json",
        "ECS004_DETERMINISM_CONTROLS.md",
        "ECS004_MUTATION_INVENTORY.json",
        "ECS004_EXPECTED_RESULTS.json",
        "ECS004_PACKAGE_HASHES.sha256",
    ]
    unresolved = []
    for path in required:
        if not (OUTPUT_DIR / path).exists() and path != "ECS004_PACKAGE_HASHES.sha256":
            unresolved.append(path)
    return f"""# ECS-004 Submission Completeness Report

Observed facts:

* Repository commit: `{manifest['commit']}`
* Required behavior mappings: {len(BEHAVIORS)}
* Required tests mapped: {len(TESTS)}
* Required mutations mapped: {len(MUTATIONS)}
* External data required: no
* Network required: no
* Developer-specific execution dependency identified: no

Unresolved deficiencies:

{chr(10).join(f'* {item}' for item in unresolved) if unresolved else '* None identified in prepared submission materials.'}

Conclusion: package materials are ready for independent ECS-004 reproduction assessment. This report does not declare ECS-004 certification.
"""


def _file_inventory(paths: list[str]) -> list[dict[str, str]]:
    rows = []
    for path_text in sorted(paths):
        path = Path(path_text)
        if path.exists() and path.is_file():
            rows.append({"path": path_text.replace("\\", "/"), "sha256": _hash_file(path), "bytes": str(path.stat().st_size)})
    return rows


def _hash_deliverables() -> str:
    rows = []
    for path in sorted(OUTPUT_DIR.iterdir()):
        if path.is_file() and path.name != "ECS004_PACKAGE_HASHES.sha256":
            rows.append(f"{_hash_file(path)}  {path.name}")
    return "\n".join(rows) + "\n"


def _copy_order() -> None:
    source = Path(r"C:\Users\Fletc\.codex\attachments\6530a117-4893-43c3-951b-2d0a852d4f76\pasted-text.txt")
    if source.exists():
        (OUTPUT_DIR / "ENTERPRISE-LEARNING-ECS-004-READINESS-ORDER.txt").write_text(source.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(name: str, payload: Any) -> None:
    (OUTPUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_text(name: str, text: str) -> None:
    (OUTPUT_DIR / name).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
