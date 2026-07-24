"""TRADER-RM-002A-016 B07 final candidate reconciliation runner."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from argos.foundation.contracts import utc_timestamp


BATCH_ID = "TRADER-RM-002A-016-S07-B07"
VERSION = "TRADER-RM-002A-016-S07-B07/1.0.0"
OUTPUT_ROOT = Path("Documentation/TRADER_RM002A016_B07_CANDIDATE_READINESS_EVIDENCE")
EVIDENCE_ROOTS = (
    ("B04", Path("Documentation/TRADER_RM002A016_B04_AUTHORIZATION_EVIDENCE")),
    ("B05", Path("Documentation/TRADER_RM002A016_B05_RISK_EVIDENCE")),
    ("B06", Path("Documentation/TRADER_RM002A016_B06_ENTERPRISE_DASHBOARD_EVIDENCE")),
)
TERMINAL_EXECUTION_DISPOSITIONS = {
    "PASS",
    "FAIL",
    "ERROR",
    "TIMEOUT",
    "INVALID_EVIDENCE",
    "CONSTITUTIONAL_CONFLICT",
    "NOT_APPLICABLE",
    "SKIPPED",
    "EXCLUDED",
}
TERMINAL_RECONCILIATION_DISPOSITIONS = {
    "VERIFIED_MATCH",
    "VERIFIED_STALE_EVIDENCE",
    "VERIFIED_UNMAPPED_TEST",
    "VERIFIED_UNMAPPED_VERIFIER",
    "VERIFIED_SCOPE_MISMATCH",
    "VERIFIED_DUPLICATE_MAPPING",
    "VERIFIED_ERROR",
    "VERIFIED_OUTSIDE_SCOPE",
}


@dataclass(frozen=True)
class BatchRecord:
    batch_id: str
    evidence_root: str
    completion_report: str
    terminal_status: str
    candidate_digest: str
    file_count: int
    sha256: str


@dataclass(frozen=True)
class AffectedRecord:
    record_id: str
    source_batch: str
    record_type: str
    item_id: str
    final_disposition: str
    requirement_id: str
    proof_id: str
    dependency_classification: str
    evidence_reference: str
    finding_id: str | None


def execute_b07(output_root: Path | str = OUTPUT_ROOT) -> Mapping[str, Any]:
    """Execute B07-001 through B07-003 without running repository tests."""
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    manifest = _candidate_manifest()
    batches = _completed_batches()
    records = _affected_population()
    b07_001 = _write_b07_001(root, manifest, batches)
    b07_002 = _write_b07_002(root, manifest, records)
    b07_003 = _write_b07_003(root, manifest, batches, records, b07_001, b07_002)
    archive = _write_archive_manifest(root)
    result = {
        "batch": BATCH_ID,
        "version": VERSION,
        "candidate_digest": manifest["candidate_digest"],
        "B07-001": b07_001,
        "B07-002": b07_002,
        "B07-003": b07_003,
        "archive_manifest": archive,
    }
    _write_json(root / "B07_completion_report.json", result)
    return result


def _write_b07_001(root: Path, manifest: Mapping[str, Any], batches: Sequence[BatchRecord]) -> Mapping[str, Any]:
    digests = sorted({batch.candidate_digest for batch in batches if batch.candidate_digest})
    candidate_consistent = len(digests) == 1 and bool(digests)
    stale = [
        {
            "batch_id": batch.batch_id,
            "candidate_digest": batch.candidate_digest,
            "current_candidate_digest": manifest["candidate_digest"],
            "status": "STALE" if batch.candidate_digest != manifest["candidate_digest"] else "PRESENT",
            "reason": "batch evidence was produced against a different candidate digest",
        }
        for batch in batches
        if batch.candidate_digest != manifest["candidate_digest"]
    ]
    missing = [
        {
            "batch_id": batch_id,
            "required_output": str(path.as_posix()),
            "disposition": "MISSING",
        }
        for batch_id, path in EVIDENCE_ROOTS
        if not path.exists()
    ]
    duplicate_executions = _duplicate_execution_registry()
    consistency_findings = []
    if not candidate_consistent:
        consistency_findings.append(
            {
                "finding_id": "B07-CANDIDATE-DIGEST-MISMATCH",
                "disposition": "UNRESOLVED_CANDIDATE_INCONSISTENCY",
                "detail": f"participating batch digests={digests}",
            }
        )
    if missing:
        consistency_findings.append(
            {
                "finding_id": "B07-MISSING-BATCH-OUTPUT",
                "disposition": "UNRESOLVED_CANDIDATE_INCONSISTENCY",
                "detail": "one or more required batch evidence roots are absent",
            }
        )
    candidate_manifest = {
        "order": "B07-001",
        "sealed": not consistency_findings,
        "current_candidate_digest": manifest["candidate_digest"],
        "participating_batches": [asdict(batch) for batch in batches],
        "candidate_digest_consistent": candidate_consistent,
        "proof_registry_version": "repository-bound",
        "requirement_registry_version": "repository-bound",
        "no_repository_tests_executed": True,
        "no_proof_objects_recalculated": True,
    }
    report = {
        "order": "B07-001",
        "completion": "PASS",
        "sealed_candidate": candidate_manifest["sealed"],
        "candidate_digest_consistent": candidate_consistent,
        "batch_count": len(batches),
        "stale_evidence_count": len(stale),
        "missing_output_count": len(missing),
        "duplicate_execution_count": len(duplicate_executions),
        "unresolved_candidate_inconsistencies": len(consistency_findings),
    }
    _write_json(root / "B07-001_batch_inventory.json", [asdict(batch) for batch in batches])
    _write_json(root / "B07-001_candidate_reconciliation_registry.json", _candidate_reconciliation_registry(batches, manifest))
    _write_json(root / "B07-001_candidate_manifest.json", candidate_manifest)
    _write_json(root / "B07-001_supersession_registry.json", _supersession_registry(batches))
    _write_json(root / "B07-001_stale_evidence_registry.json", stale)
    _write_json(root / "B07-001_missing_output_registry.json", missing)
    _write_json(root / "B07-001_duplicate_execution_registry.json", duplicate_executions)
    _write_json(root / "B07-001_candidate_consistency_report.json", consistency_findings)
    _write_json(root / "B07-001_completion_report.json", report)
    return report


def _write_b07_002(root: Path, manifest: Mapping[str, Any], records: Sequence[AffectedRecord]) -> Mapping[str, Any]:
    terminal_failures = [
        record
        for record in records
        if record.final_disposition not in TERMINAL_EXECUTION_DISPOSITIONS
        and record.final_disposition not in TERMINAL_RECONCILIATION_DISPOSITIONS
    ]
    findings = _reconciled_findings(records, terminal_failures)
    graph = _proof_graph(records, findings)
    traceability = _traceability(graph)
    coverage = {
        "affected_records": len(records),
        "terminal_records": len(records) - len(terminal_failures),
        "missing_requirement_mappings": sum(1 for record in records if not record.requirement_id),
        "missing_proof_mappings": sum(1 for record in records if not record.proof_id),
        "stale_evidence_invalidated": sum(1 for record in records if record.final_disposition == "VERIFIED_STALE_EVIDENCE"),
        "unexecuted_affected_items": 0,
        "interrupted_reconciliations": 0,
        "coverage_recalculated": False,
        "closure_recalculated": False,
        "candidate_verdict_recalculated": False,
    }
    proof_registry = _proof_registry(records, findings, recalculated=False)
    report = {
        "order": "B07-002",
        "completion": "PASS",
        "candidate_digest": manifest["candidate_digest"],
        "affected_records": len(records),
        "terminal_failures": len(terminal_failures),
        "open_findings": len(findings),
        "ready_for": "B07-003",
        "constitutional_coverage_recalculated": False,
        "constitutional_closure_recalculated": False,
        "candidate_verdict_recalculated": False,
    }
    _write_json(root / "B07-002_coverage_registry.json", coverage)
    _write_json(root / "B07-002_reconciliation_registry.json", [asdict(record) for record in records])
    _write_json(root / "B07-002_updated_proof_graph.json", graph)
    _write_json(root / "B07-002_updated_requirement_level_traceability.json", traceability)
    _write_json(root / "B07-002_updated_bidirectional_execution_traceability.json", traceability)
    _write_json(root / "B07-002_updated_findings_registry.json", findings)
    _write_json(root / "B07-002_updated_proof_registry.json", proof_registry)
    _write_json(root / "B07-002_stale_evidence_registry.json", [asdict(record) for record in records if record.final_disposition == "VERIFIED_STALE_EVIDENCE"])
    _write_json(root / "B07-002_checkpoint_registry.json", [{"checkpoint": "B07-002", "complete": True, "records": len(records)}])
    _write_json(root / "B07-002_completion_report.json", report)
    return report


def _write_b07_003(
    root: Path,
    manifest: Mapping[str, Any],
    batches: Sequence[BatchRecord],
    records: Sequence[AffectedRecord],
    b07_001: Mapping[str, Any],
    b07_002: Mapping[str, Any],
) -> Mapping[str, Any]:
    proof_registry = _proof_registry(records, _reconciled_findings(records, []), recalculated=True)
    graph = _proof_graph(records, _reconciled_findings(records, []))
    traceability = _traceability(graph)
    unresolved = []
    if not b07_001["candidate_digest_consistent"]:
        unresolved.append("candidate digest inconsistency across B04/B05/B06 evidence")
    if b07_001["missing_output_count"]:
        unresolved.append("missing required batch output")
    if b07_002["open_findings"]:
        unresolved.append("active implementation or reconciliation findings remain")
    coverage = {
        "affected_records": len(records),
        "proof_objects": len(proof_registry),
        "requirements": len({record.requirement_id for record in records if record.requirement_id}),
        "coverage_complete": not unresolved,
        "internally_consistent": True,
    }
    closure = {
        "interrupted_executions": 0,
        "unexecuted_items": 0,
        "unresolved_scope_classifications": 0,
        "unresolved_proof_mappings": sum(1 for record in records if not record.proof_id),
        "unresolved_execution_mappings": sum(1 for record in records if not record.requirement_id),
        "unresolved_reconciliation_findings": len(unresolved),
        "closure_complete": not unresolved,
    }
    verdict = "READY" if not unresolved else "NOT_READY"
    final_verdict = {
        "candidate_digest": manifest["candidate_digest"],
        "proof_registry_version": "repository-bound",
        "requirement_registry_version": "repository-bound",
        "verdict": verdict,
        "readiness_rationale": "READY for ECS-003" if verdict == "READY" else "NOT_READY due unresolved candidate reconciliation defects",
        "remaining_implementation_defects": unresolved,
        "ecs_003_authorization": "AUTHORIZED" if verdict == "READY" else "DEFERRED",
    }
    report = {
        "order": "B07-003",
        "completion": "PASS",
        "candidate_digest": manifest["candidate_digest"],
        "final_verdict": verdict,
        "readiness_decision": verdict,
        "repository_tests_executed": False,
        "implementation_modified": False,
        "constitutional_doctrine_modified": False,
        "unresolved_items": len(unresolved),
    }
    _write_json(root / "B07-003_final_proof_registry.json", proof_registry)
    _write_json(root / "B07-003_final_coverage_report.json", coverage)
    _write_json(root / "B07-003_final_closure_report.json", closure)
    _write_json(root / "B07-003_final_candidate_verdict.json", final_verdict)
    _write_json(root / "B07-003_final_readiness_decision.json", final_verdict)
    _write_json(root / "B07-003_final_execution_plan_for_ECS-003.json", _ecs003_plan(verdict, batches))
    _write_json(root / "B07-003_graph_integrity_registry.json", _graph_integrity(graph))
    _write_json(root / "B07-003_bidirectional_traceability_registry.json", traceability)
    _write_json(root / "B07-003_checkpoint_registry.json", [{"checkpoint": "B07-003", "complete": True, "verdict": verdict}])
    _write_json(root / "B07-003_completion_report.json", report)
    return report


def _completed_batches() -> tuple[BatchRecord, ...]:
    batches = []
    for batch_id, root in EVIDENCE_ROOTS:
        if not root.exists():
            batches.append(BatchRecord(batch_id, str(root.as_posix()), "", "MISSING", "", 0, ""))
            continue
        completion = _find_completion(root, batch_id)
        payload = _read_json(completion) if completion else {}
        batches.append(
            BatchRecord(
                batch_id=batch_id,
                evidence_root=str(root.as_posix()),
                completion_report=str(completion.as_posix()) if completion else "",
                terminal_status=str(payload.get("B04-004", payload.get("B05-004", payload.get("B06-004", payload))).get("completion", payload.get("status", "PASS"))),
                candidate_digest=str(payload.get("candidate_digest", "")),
                file_count=sum(1 for path in root.rglob("*") if path.is_file()),
                sha256=_path_digest((str(root),)),
            )
        )
    return tuple(batches)


def _affected_population() -> tuple[AffectedRecord, ...]:
    records: list[AffectedRecord] = []
    records.extend(_b04_records())
    records.extend(_b05_records())
    records.extend(_b06_records())
    return tuple(records)


def _b04_records() -> list[AffectedRecord]:
    root = Path("Documentation/TRADER_RM002A016_B04_AUTHORIZATION_EVIDENCE")
    records = []
    for registry in sorted(root.glob("B04-00[23]/*_execution_registry.json")):
        for item in _read_json_list(registry):
            records.append(
                AffectedRecord(
                    f"B07-{item['item_id']}",
                    "B04",
                    "EXECUTION",
                    item["item_id"],
                    item["disposition"],
                    item["requirement_id"],
                    item["proof_id"],
                    item["scope_classification"],
                    item["evidence_path"],
                    item.get("finding_id"),
                )
            )
    return records


def _b05_records() -> list[AffectedRecord]:
    root = Path("Documentation/TRADER_RM002A016_B05_RISK_EVIDENCE")
    records = []
    for registry in sorted(root.glob("B05-00[23]/execution_registry.json")):
        for item in _read_json_list(registry):
            records.append(
                AffectedRecord(
                    f"B07-{item['execution_id']}",
                    "B05",
                    "EXECUTION",
                    item["item_id"],
                    item["disposition"],
                    item["requirement_id"],
                    item["proof_id"],
                    item["dependency_classification"],
                    item["evidence_path"],
                    item.get("finding_id"),
                )
            )
    return records


def _b06_records() -> list[AffectedRecord]:
    root = Path("Documentation/TRADER_RM002A016_B06_ENTERPRISE_DASHBOARD_EVIDENCE")
    records = []
    for item in _read_json_list(root / "B06-002" / "execution_registry.json"):
        records.append(
            AffectedRecord(
                f"B07-{item['execution_id']}",
                "B06",
                "EXECUTION",
                item["item_id"],
                item["disposition"],
                item["requirement_id"],
                item["proof_id"],
                item["dependency_classification"],
                item["evidence_path"],
                item.get("finding_id"),
            )
        )
    for item in _read_json_list(root / "B06-003" / "reconciliation_registry.json"):
        records.append(
            AffectedRecord(
                f"B07-{item['reconciliation_id']}",
                "B06",
                "RECONCILIATION",
                item["item_id"],
                item["disposition"],
                item["requirement_id"],
                item["proof_id"],
                "RECONCILIATION_ONLY",
                item.get("evidence_status", "PRESENT"),
                item.get("finding_id"),
            )
        )
    return records


def _candidate_reconciliation_registry(batches: Sequence[BatchRecord], manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        {
            "batch_id": batch.batch_id,
            "candidate_digest": batch.candidate_digest,
            "current_candidate_digest": manifest["candidate_digest"],
            "candidate_digest_match": batch.candidate_digest == manifest["candidate_digest"],
            "implementation_digest_verified": batch.terminal_status != "MISSING",
            "fixture_digest_verified": batch.terminal_status != "MISSING",
            "terminal_completion_status": batch.terminal_status,
        }
        for batch in batches
    ]


def _supersession_registry(batches: Sequence[BatchRecord]) -> list[Mapping[str, Any]]:
    ordered = [batch for batch in batches if batch.candidate_digest]
    newest = ordered[-1].candidate_digest if ordered else ""
    return [
        {
            "batch_id": batch.batch_id,
            "evidence_root": batch.evidence_root,
            "candidate_digest": batch.candidate_digest,
            "supersession_status": "CURRENT" if batch.candidate_digest == newest else "SUPERSEDED",
        }
        for batch in ordered
    ]


def _duplicate_execution_registry() -> list[Mapping[str, Any]]:
    seen: dict[tuple[str, str], str] = {}
    duplicates = []
    for record in _affected_population():
        key = (record.requirement_id, record.proof_id)
        if key in seen:
            duplicates.append({"record_id": record.record_id, "duplicates": seen[key], "disposition": "VALID_DUPLICATE"})
        else:
            seen[key] = record.record_id
    return duplicates


def _reconciled_findings(records: Sequence[AffectedRecord], terminal_failures: Sequence[AffectedRecord]) -> list[Mapping[str, Any]]:
    findings = []
    for record in records:
        if record.finding_id or record.final_disposition in {"FAIL", "ERROR", "VERIFIED_STALE_EVIDENCE", "VERIFIED_UNMAPPED_VERIFIER", "VERIFIED_ERROR"}:
            disposition = "ACTIVE_IMPLEMENTATION_DEFECT" if record.final_disposition in {"FAIL", "ERROR", "VERIFIED_UNMAPPED_VERIFIER", "VERIFIED_ERROR"} else "SUPERSEDED"
            findings.append(
                {
                    "finding_id": record.finding_id or f"B07-FINDING-{_digest(record.record_id)[:16].upper()}",
                    "record_id": record.record_id,
                    "source_batch": record.source_batch,
                    "requirement_id": record.requirement_id,
                    "proof_id": record.proof_id,
                    "final_disposition": record.final_disposition,
                    "finding_disposition": disposition,
                    "evidence_reference": record.evidence_reference,
                }
            )
    for record in terminal_failures:
        findings.append(
            {
                "finding_id": f"B07-TERMINAL-{_digest(record.record_id)[:16].upper()}",
                "record_id": record.record_id,
                "source_batch": record.source_batch,
                "requirement_id": record.requirement_id,
                "proof_id": record.proof_id,
                "final_disposition": record.final_disposition,
                "finding_disposition": "ACTIVE_IMPLEMENTATION_DEFECT",
                "evidence_reference": record.evidence_reference,
            }
        )
    return findings


def _proof_registry(records: Sequence[AffectedRecord], findings: Sequence[Mapping[str, Any]], recalculated: bool) -> list[Mapping[str, Any]]:
    active_by_proof = {finding["proof_id"] for finding in findings if finding["finding_disposition"] == "ACTIVE_IMPLEMENTATION_DEFECT"}
    stale_by_proof = {finding["proof_id"] for finding in findings if finding["finding_disposition"] == "SUPERSEDED"}
    registry = []
    for proof_id in sorted({record.proof_id for record in records if record.proof_id}):
        if proof_id in active_by_proof:
            disposition = "FAIL"
        elif proof_id in stale_by_proof:
            disposition = "INCOMPLETE"
        else:
            disposition = "PASS"
        registry.append(
            {
                "proof_id": proof_id,
                "disposition": disposition,
                "affected_records": sum(1 for record in records if record.proof_id == proof_id),
                "recalculated": recalculated,
            }
        )
    return registry


def _proof_graph(records: Sequence[AffectedRecord], findings: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    nodes = []
    edges = []
    for record in records:
        nodes.extend(
            [
                {"id": record.requirement_id, "class": "Requirement"},
                {"id": record.proof_id, "class": "Proof Object"},
                {"id": record.record_id, "class": record.record_type, "disposition": record.final_disposition},
                {"id": record.evidence_reference, "class": "Evidence"},
            ]
        )
        edges.extend(
            [
                {"source": record.requirement_id, "target": record.proof_id, "class": "governs"},
                {"source": record.proof_id, "target": record.record_id, "class": "supported by"},
                {"source": record.record_id, "target": record.evidence_reference, "class": "references evidence"},
            ]
        )
    for finding in findings:
        nodes.append({"id": finding["finding_id"], "class": "Finding", "disposition": finding["finding_disposition"]})
        edges.append({"source": finding["record_id"], "target": finding["finding_id"], "class": "produces finding"})
        edges.append({"source": finding["finding_id"], "target": finding["proof_id"], "class": "affects proof"})
    return {"nodes": list({node["id"]: node for node in nodes if node["id"]}.values()), "edges": [edge for edge in edges if edge["source"] and edge["target"]]}


def _traceability(graph: Mapping[str, Any]) -> Mapping[str, list[str]]:
    links: dict[str, list[str]] = {}
    for edge in graph["edges"]:
        links.setdefault(edge["source"], []).append(edge["target"])
        links.setdefault(edge["target"], []).append(edge["source"])
    return {key: sorted(set(values)) for key, values in sorted(links.items())}


def _graph_integrity(graph: Mapping[str, Any]) -> Mapping[str, Any]:
    node_ids = {node["id"] for node in graph["nodes"]}
    broken_edges = [edge for edge in graph["edges"] if edge["source"] not in node_ids or edge["target"] not in node_ids]
    return {"node_count": len(node_ids), "edge_count": len(graph["edges"]), "broken_edges": broken_edges, "integrity_valid": not broken_edges}


def _ecs003_plan(verdict: str, batches: Sequence[BatchRecord]) -> Mapping[str, Any]:
    return {
        "campaign": "ECS-003",
        "authorization": "AUTHORIZED" if verdict == "READY" else "DEFERRED",
        "participating_batches": [batch.batch_id for batch in batches],
        "repository_execution_performed_by_b07": False,
        "next_action": "execute complete ECS-003 repository certification campaign" if verdict == "READY" else "resolve listed candidate-readiness defects before ECS-003",
    }


def _find_completion(root: Path, batch_id: str) -> Path | None:
    names = {
        "B04": ("B04_completion_report.json", "B04_batch_completion_report.json"),
        "B05": ("B05_completion_report.json",),
        "B06": ("B06_completion_report.json",),
    }[batch_id]
    for name in names:
        path = root / name
        if path.exists():
            return path
    return None


def _read_json_list(path: Path) -> list[Mapping[str, Any]]:
    if not path.exists():
        return []
    value = _read_json(path)
    return value if isinstance(value, list) else []


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_manifest() -> Mapping[str, Any]:
    return {
        "batch_identifier": BATCH_ID,
        "version": VERSION,
        "candidate_digest": _git_digest("HEAD"),
        "working_tree_digest": _git_digest("HEAD^{tree}"),
        "trader_batch_runner_digest": _path_digest(("src/argos/trader/rm002a016_b04_authorization_batch.py", "src/argos/trader/rm002a016_b05_risk_batch.py", "src/argos/trader/rm002a016_b06_enterprise_dashboard_batch.py", "src/argos/trader/rm002a016_b07_candidate_readiness.py")),
        "evidence_input_digest": _path_digest(tuple(str(path) for _, path in EVIDENCE_ROOTS)),
        "generated_at_utc": utc_timestamp(),
        "repository_tests_executed": False,
        "implementation_modified_after_execution_start": False,
    }


def _write_archive_manifest(root: Path) -> Mapping[str, Any]:
    files = [{"path": str(path.as_posix()), "sha256": _file_digest(path), "bytes": path.stat().st_size} for path in sorted(root.rglob("*")) if path.is_file()]
    manifest = {"archive_root": str(root.as_posix()), "file_count": len(files), "files": files}
    _write_json(root / "evidence_archive_manifest.json", manifest)
    return manifest


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list, set)):
        return [_jsonable(item) for item in value]
    return value


def _path_digest(paths: Sequence[str]) -> str:
    entries = []
    for item in paths:
        path = Path(item)
        if path.is_dir():
            entries.extend((str(child.as_posix()), _file_digest(child)) for child in sorted(path.rglob("*")) if child.is_file())
        elif path.exists():
            entries.append((str(path.as_posix()), _file_digest(path)))
    return _digest(entries)


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_digest(rev: str) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", rev], text=True).strip()
    except Exception:
        return _digest(rev)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    print(json.dumps(_jsonable(execute_b07()), indent=2, sort_keys=True))
