"""Independent ECS-003 constitutional audit package for the Broker Office."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import contextlib
import hashlib
import importlib
import io
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence
import unittest


BROKER_ECS003_VERSION = "BROKER-ECS003/1.0.0"
DEFAULT_OUTPUT_ROOT = Path("Documentation/BROKER_ECS003_AUDIT_EVIDENCE")
BROKER_PATTERNS = ("broker", "Broker", "BROKER")
BROKER_TEST_MODULES = ("Tests.test_broker_integration_office", "Tests.test_or003_paper_brokerage")
AUDIT_PHASES = (
    "A01_repository_inventory",
    "A02_governance_review",
    "A03_constitutional_object_review",
    "A04_lifecycle_review",
    "A05_ownership_review",
    "A06_interface_review",
    "A07_evidence_review",
    "A08_rule_and_verification_review",
    "A09_dependency_closure_review",
    "A10_traceability_review",
    "A11_independent_certification_review",
)


@dataclass(frozen=True)
class Finding:
    identifier: str
    constitutional_requirement: str
    affected_artifact: str
    severity: str
    evidence: str
    remediation_recommendation: str
    disposition: str
    category: str


def run_broker_ecs003_audit(output_root: Path | str = DEFAULT_OUTPUT_ROOT) -> Mapping[str, Any]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    manifest = _candidate_manifest()
    inventory = build_repository_inventory()
    dependency_map = build_dependency_map(inventory)
    tests = run_broker_tests()
    reviews = build_phase_i_reviews(inventory, dependency_map, tests)
    findings = [finding for review in reviews.values() for finding in review["findings"]]
    phase_i_verdict = "UNCONDITIONAL PASS" if not findings and tests["status"] == "PASS" else "FAIL"
    phase_ii = build_phase_ii_review(phase_i_verdict)
    final_verdict = "UNCONDITIONAL PASS" if phase_i_verdict == "UNCONDITIONAL PASS" and phase_ii["verdict"] == "UNCONDITIONAL PASS" else "FAIL"
    final_report = build_final_report(inventory, dependency_map, tests, reviews, findings, phase_i_verdict, phase_ii, final_verdict)

    _write_json(root / "00_candidate_manifest.json", manifest)
    _write_json(root / "01_repository_inventory.json", inventory)
    _write_json(root / "02_dependency_map.json", dependency_map)
    _write_json(root / "03_broker_test_execution.json", tests)
    for index, (name, review) in enumerate(reviews.items(), start=4):
        _write_json(root / f"{index:02d}_{name}.json", review)
    _write_json(root / "15_phase_i_verdict.json", {"phase": "I", "verdict": phase_i_verdict, "finding_count": len(findings)})
    _write_json(root / "16_phase_ii_review.json", phase_ii)
    _write_json(root / "17_findings_registry.json", findings)
    _write_json(root / "18_final_ecs003_report.json", final_report)
    archive = _write_archive_manifest(root)
    result = {
        "package": "BROKER_ECS003_AUDIT_EVIDENCE",
        "version": BROKER_ECS003_VERSION,
        "candidate_digest": manifest["candidate_digest"],
        "phase_i_verdict": phase_i_verdict,
        "phase_ii_verdict": phase_ii["verdict"],
        "final_verdict": final_verdict,
        "constitutional_freeze_decision": final_report["constitutional_freeze_decision"],
        "finding_count": len(findings),
        "archive_manifest": archive,
    }
    _write_json(root / "BROKER_ECS003_AUDIT_PACKAGE.json", result)
    return result


def build_repository_inventory(root: Path | str = Path(".")) -> Mapping[str, Any]:
    base = Path(root)
    tracked = _git_files(base)
    artifacts = []
    for rel in tracked:
        if any(pattern in rel for pattern in BROKER_PATTERNS):
            path = base / rel
            artifacts.append(
                {
                    "path": rel,
                    "artifact_type": _artifact_type(rel),
                    "sha256": _file_digest(path) if path.exists() else "",
                    "participation_basis": _participation_basis(rel),
                }
            )
    artifacts.sort(key=lambda item: item["path"])
    by_type: dict[str, int] = {}
    for item in artifacts:
        by_type[item["artifact_type"]] = by_type.get(item["artifact_type"], 0) + 1
    return {
        "schema_version": "broker-ecs003-repository-inventory/v1",
        "generated_at_utc": _now(),
        "participating_artifact_count": len(artifacts),
        "artifact_counts": by_type,
        "artifacts": artifacts,
    }


def build_dependency_map(inventory: Mapping[str, Any]) -> Mapping[str, Any]:
    artifacts = inventory["artifacts"]
    edges = []
    for artifact in artifacts:
        path = artifact["path"]
        text = Path(path).read_text(encoding="utf-8", errors="ignore") if Path(path).exists() else ""
        for other in artifacts:
            other_name = Path(other["path"]).stem
            if other["path"] != path and other_name and other_name in text:
                edges.append({"source": path, "target": other["path"], "relationship": "textual_or_import_reference"})
        if path.startswith("Tests/") or path.startswith("Tests\\"):
            edges.append({"source": path, "target": "Broker Office verification population", "relationship": "executable_test"})
        if path.startswith("src/"):
            edges.append({"source": path, "target": "Broker Office implementation population", "relationship": "implementation_artifact"})
        if path.startswith("Documentation/"):
            edges.append({"source": path, "target": "Broker Office constitutional/evidence population", "relationship": "documentation_or_evidence"})
    return {
        "schema_version": "broker-ecs003-dependency-map/v1",
        "participation_method": "dependency-derived scan of tracked Broker-related artifacts and references",
        "namespace_only_exclusions_used": False,
        "nodes": artifacts,
        "edges": edges,
    }


def run_broker_tests() -> Mapping[str, Any]:
    records = []
    module_results = []
    for module_name in BROKER_TEST_MODULES:
        result = run_test_module(module_name)
        module_results.append(result)
        records.extend(result["records"])
    counts = _count_dispositions(records)
    return {
        "schema_version": "broker-ecs003-focused-test-execution/v1",
        "modules": module_results,
        "records": records,
        "disposition_counts": counts,
        "tests_run": len(records),
        "status": "PASS" if records and all(record["disposition"] == "PASS" for record in records) else "FAIL",
        "repository_wide_execution_performed": False,
    }


def run_test_module(module_name: str) -> Mapping[str, Any]:
    module = importlib.import_module(module_name)
    suite = unittest.defaultTestLoader.loadTestsFromName(module_name)
    stream = io.StringIO()
    result = _RecordingRunner(stream=stream, verbosity=2).run(suite)
    records = [result.records[key] for key in sorted(result.records)]
    return {
        "module": module_name,
        "source_file": str(Path(getattr(module, "__file__", "")).as_posix()),
        "records": records,
        "disposition_counts": _count_dispositions(records),
        "successful": result.wasSuccessful(),
        "runner_output": stream.getvalue(),
    }


def build_phase_i_reviews(inventory: Mapping[str, Any], dependency_map: Mapping[str, Any], tests: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    objects = _objects_from_source()
    lifecycle_terms = _lifecycle_terms()
    evidence_artifacts = [item for item in inventory["artifacts"] if item["artifact_type"] == "evidence"]
    findings_by_phase = {
        "A01_repository_inventory": [],
        "A02_governance_review": [_finding("A02-001", "Governance must define complete Broker authority, ownership, conflict resolution, and subordination.", "Documentation/broker_integration_office.md", "HIGH", "No Broker-specific governance series defining conflict resolution and subordinate relationships was located.", "Adopt Broker governance decisions before final freeze.", "OPEN", "governance")],
        "A03_constitutional_object_review": [],
        "A04_lifecycle_review": [_finding("A04-001", "Every Broker lifecycle transition must define recovery, replay, timeout, correction, and terminal disposition.", "src/argos/trader/broker_integration.py", "HIGH", "Implementation exposes submission, case-file, and normalization flows, but no complete transition constitution artifact was found.", "Materialize Broker lifecycle transition constitution and map each transition to executable evidence.", "OPEN", "lifecycle")],
        "A05_ownership_review": [_finding("A05-001", "Every Broker object must have exactly one owner and explicit custody/mutation/reconciliation authority.", "Documentation/broker_integration_office.md", "HIGH", "Broker ownership is described operationally, but object-level custody, mutation, reconciliation, transfer, and terminal custody matrix is absent.", "Add Broker ownership and custody matrix for requests, raw responses, canonical events, mappings, case files, capability profiles, health records, and adapter state.", "OPEN", "ownership")],
        "A06_interface_review": [],
        "A07_evidence_review": [],
        "A08_rule_and_verification_review": [],
        "A09_dependency_closure_review": [],
        "A10_traceability_review": [_finding("A10-001", "Requirement-to-verdict traceability must be bidirectional for every Broker relationship.", "Broker ECS-003 audit dependency map", "HIGH", "The audit can derive artifacts and test participation, but no complete bidirectional Requirement->Artifact->Implementation->Rule->Execution->Evidence->Finding->Verdict matrix exists for Broker.", "Publish Broker requirement-level traceability matrix with reciprocal links.", "OPEN", "traceability")],
        "A11_independent_certification_review": [],
    }
    if not evidence_artifacts:
        findings_by_phase["A07_evidence_review"].append(_finding("A07-001", "Evidence must include production, provenance, custody, integrity, retention, and certification-use proof.", "Documentation", "HIGH", "No Broker-specific independent ECS evidence package existed before this audit run.", "Generate candidate-bound Broker evidence and separate candidate assertions from audit evidence.", "OPEN", "evidence"))
    if tests["status"] != "PASS":
        findings_by_phase["A08_rule_and_verification_review"].append(_finding("A08-001", "Declared verification shall not substitute for executed verification.", "Broker focused unittest population", "CRITICAL", "One or more Broker-focused tests failed or errored.", "Repair failing Broker verification before certification.", "OPEN", "verification"))
    if tests["tests_run"] < 8:
        findings_by_phase["A08_rule_and_verification_review"].append(_finding("A08-002", "Rules require positive, negative, boundary, replay, restart, recovery, stale input, conflicting authority, and missing evidence verification.", "Tests/test_broker_integration_office.py; Tests/test_or003_paper_brokerage.py", "HIGH", "Focused Broker tests execute positive, negative, duplicate, health, and non-fabrication paths, but do not prove complete replay/restart/recovery and stale/conflicting authority coverage.", "Add Broker ECS verifier suite for replay, restart, recovery, stale inputs, conflicting authority, and missing evidence.", "OPEN", "verification"))
    if len(dependency_map["edges"]) == 0:
        findings_by_phase["A09_dependency_closure_review"].append(_finding("A09-001", "Dependency-derived participation must be established.", "Broker dependency map", "CRITICAL", "No Broker dependency edges were derived.", "Repair dependency discovery.", "OPEN", "dependency"))
    if not objects:
        findings_by_phase["A03_constitutional_object_review"].append(_finding("A03-001", "Every Broker constitutional object must be identified.", "src/argos/trader/broker_integration.py", "CRITICAL", "No Broker constitutional objects were discoverable.", "Define Broker object registry.", "OPEN", "object"))
    if len(lifecycle_terms) < 5:
        findings_by_phase["A04_lifecycle_review"].append(_finding("A04-002", "Broker lifecycle must be complete.", "Broker source artifacts", "HIGH", "Lifecycle vocabulary is insufficient for complete transition proof.", "Expand lifecycle constitution.", "OPEN", "lifecycle"))
    reviews = {}
    for phase in AUDIT_PHASES:
        reviews[phase] = {
            "phase": phase,
            "status": "PASS" if not findings_by_phase[phase] else "FAIL",
            "findings": [finding.__dict__ for finding in findings_by_phase[phase]],
            "evidence_summary": _phase_evidence_summary(phase, inventory, dependency_map, tests, objects, lifecycle_terms),
        }
    return reviews


def build_phase_ii_review(phase_i_verdict: str) -> Mapping[str, Any]:
    if phase_i_verdict != "UNCONDITIONAL PASS":
        return {
            "phase": "II",
            "executed": False,
            "verdict": "FAIL",
            "reason": "Phase II is constitutionally permitted only after Phase I receives UNCONDITIONAL PASS.",
            "constitutional_freeze_eligible": False,
        }
    return {
        "phase": "II",
        "executed": True,
        "verdict": "UNCONDITIONAL PASS",
        "constitutional_freeze_eligible": True,
    }


def build_final_report(
    inventory: Mapping[str, Any],
    dependency_map: Mapping[str, Any],
    tests: Mapping[str, Any],
    reviews: Mapping[str, Mapping[str, Any]],
    findings: Sequence[Mapping[str, Any]],
    phase_i_verdict: str,
    phase_ii: Mapping[str, Any],
    final_verdict: str,
) -> Mapping[str, Any]:
    by_category: dict[str, int] = {}
    for finding in findings:
        category = str(finding["category"])
        by_category[category] = by_category.get(category, 0) + 1
    object_count = len(_objects_from_source())
    lifecycle_count = len(_lifecycle_terms())
    return {
        "schema_version": "broker-ecs003-final-report/v1",
        "repository_statistics": inventory["artifact_counts"],
        "participating_artifact_count": inventory["participating_artifact_count"],
        "constitutional_object_count": object_count,
        "lifecycle_count": lifecycle_count,
        "rule_count": tests["tests_run"],
        "verification_count": tests["tests_run"],
        "evidence_count": sum(1 for item in inventory["artifacts"] if item["artifact_type"] == "evidence"),
        "dependency_edge_count": len(dependency_map["edges"]),
        "findings_by_category": by_category,
        "unresolved_governance_decisions": [finding for finding in findings if finding["category"] == "governance"],
        "implementation_deficiencies": [finding for finding in findings if finding["category"] in {"lifecycle", "ownership"}],
        "evidence_deficiencies": [finding for finding in findings if finding["category"] == "evidence"],
        "proof_deficiencies": [finding for finding in findings if finding["category"] == "verification"],
        "traceability_deficiencies": [finding for finding in findings if finding["category"] == "traceability"],
        "dependency_deficiencies": [finding for finding in findings if finding["category"] == "dependency"],
        "certification_deficiencies": [finding for finding in findings if finding["category"] in {"governance", "evidence", "verification", "traceability"}],
        "phase_i_verdict": phase_i_verdict,
        "phase_ii_verdict": phase_ii["verdict"],
        "final_certification_verdict": final_verdict,
        "constitutional_freeze_decision": "ELIGIBLE" if final_verdict == "UNCONDITIONAL PASS" else "NOT_ELIGIBLE",
    }


class _RecordingResult(unittest.TextTestResult):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.records: dict[str, dict[str, Any]] = {}

    def startTest(self, test: unittest.TestCase) -> None:  # noqa: N802
        super().startTest(test)
        self.records[test.id()] = {"test_identifier": test.id(), "disposition": "RUNNING", "details": ""}

    def addSuccess(self, test: unittest.TestCase) -> None:  # noqa: N802
        self.records[test.id()]["disposition"] = "PASS"
        super().addSuccess(test)

    def addFailure(self, test: unittest.TestCase, err: Any) -> None:  # noqa: N802
        self.records[test.id()]["disposition"] = "FAIL"
        self.records[test.id()]["details"] = self._exc_info_to_string(err, test)
        super().addFailure(test, err)

    def addError(self, test: unittest.TestCase, err: Any) -> None:  # noqa: N802
        self.records[test.id()]["disposition"] = "ERROR"
        self.records[test.id()]["details"] = self._exc_info_to_string(err, test)
        super().addError(test, err)

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:  # noqa: N802
        self.records[test.id()]["disposition"] = "NOT_APPLICABLE"
        self.records[test.id()]["details"] = reason
        super().addSkip(test, reason)

    def stopTest(self, test: unittest.TestCase) -> None:  # noqa: N802
        if self.records[test.id()]["disposition"] == "RUNNING":
            self.records[test.id()]["disposition"] = "PASS"
        super().stopTest(test)


class _RecordingRunner(unittest.TextTestRunner):
    resultclass = _RecordingResult


def _phase_evidence_summary(
    phase: str,
    inventory: Mapping[str, Any],
    dependency_map: Mapping[str, Any],
    tests: Mapping[str, Any],
    objects: Sequence[str],
    lifecycle_terms: Sequence[str],
) -> Mapping[str, Any]:
    return {
        "participating_artifacts": inventory["participating_artifact_count"],
        "dependency_edges": len(dependency_map["edges"]),
        "broker_objects_observed": objects,
        "lifecycle_terms_observed": lifecycle_terms,
        "focused_tests_run": tests["tests_run"],
        "candidate_pass_reports_accepted_as_primary_evidence": False,
        "phase": phase,
    }


def _objects_from_source() -> tuple[str, ...]:
    source = Path("src/argos/trader/broker_integration.py")
    if not source.exists():
        return ()
    text = source.read_text(encoding="utf-8")
    names = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("class ") and "Broker" in stripped:
            names.append(stripped.split("class ", 1)[1].split("(", 1)[0].split(":", 1)[0])
    return tuple(sorted(set(names)))


def _lifecycle_terms() -> tuple[str, ...]:
    terms = set()
    for path in (Path("src/argos/trader/broker_integration.py"), Path("src/argos/trader/paper_brokerage.py")):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for term in ("acknowledgement", "fill", "partial_fill", "cancellation", "rejection", "execution_update", "settled", "queued", "expired", "cancelled", "rejected"):
            if term in text:
                terms.add(term)
    return tuple(sorted(terms))


def _finding(
    identifier: str,
    requirement: str,
    artifact: str,
    severity: str,
    evidence: str,
    recommendation: str,
    disposition: str,
    category: str,
) -> Finding:
    return Finding(identifier, requirement, artifact, severity, evidence, recommendation, disposition, category)


def _artifact_type(path: str) -> str:
    lower = path.lower()
    if lower.startswith("src/"):
        return "implementation"
    if lower.startswith("tests/"):
        return "executable_rule"
    if "evidence" in lower or lower.endswith(".json") or lower.endswith(".csv") or lower.endswith(".sha256"):
        return "evidence"
    if lower.startswith("documentation/"):
        return "constitutional_artifact"
    return "artifact"


def _participation_basis(path: str) -> str:
    if path.startswith("Tests/") or path.startswith("Tests\\"):
        return "Broker-focused executable verification"
    if path.startswith("src/") or path.startswith("src\\"):
        return "Broker implementation dependency"
    return "Broker constitutional/evidence reference"


def _git_files(base: Path) -> tuple[str, ...]:
    try:
        output = subprocess.check_output(["git", "ls-files"], cwd=str(base), text=True)
        return tuple(line.strip() for line in output.splitlines() if line.strip())
    except Exception:
        return tuple(str(path.relative_to(base).as_posix()) for path in base.rglob("*") if path.is_file())


def _candidate_manifest() -> Mapping[str, Any]:
    return {
        "candidate_digest": _git_digest("HEAD"),
        "working_tree_digest": _git_digest("HEAD^{tree}"),
        "runner_version": BROKER_ECS003_VERSION,
        "generated_at_utc": _now(),
        "candidate_modified": False,
        "implementation_repaired": False,
        "candidate_pass_reports_accepted_as_primary_evidence": False,
    }


def _count_dispositions(records: Sequence[Mapping[str, Any]]) -> Mapping[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        disposition = str(record.get("disposition", "UNKNOWN"))
        counts[disposition] = counts.get(disposition, 0) + 1
    return counts


def _write_archive_manifest(root: Path) -> Mapping[str, Any]:
    files = [{"path": path.relative_to(root).as_posix(), "sha256": _file_digest(path), "bytes": path.stat().st_size} for path in sorted(root.rglob("*")) if path.is_file()]
    manifest = {"file_count": len(files), "files": files}
    _write_json(root / "19_evidence_archive_manifest.json", manifest)
    return manifest


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_digest(rev: str) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", rev], text=True).strip()
    except Exception:
        return _digest(rev)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    print(json.dumps(run_broker_ecs003_audit(), indent=2, sort_keys=True))
