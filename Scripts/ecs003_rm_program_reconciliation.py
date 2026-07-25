from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOC_ROOT = REPOSITORY_ROOT / "Documentation"
OUTPUT_DIR = DOC_ROOT / "ECS003_RM_PROGRAM_RECONCILIATION"
SOURCE_ORDER_DIR = OUTPUT_DIR / "source_orders"

SOURCE_ORDERS = {
    "ECS-003-RM-B01": Path(r"C:\Users\Fletc\.codex\attachments\274e11ef-f72b-4730-ad50-ae8bd9a2c643\pasted-text.txt"),
    "ECS-003-RM-B02": Path(r"C:\Users\Fletc\.codex\attachments\638d1afa-9828-47a1-8ec0-e3fe8f6c4f2b\pasted-text.txt"),
    "ECS-003-RM-B04": Path(r"C:\Users\Fletc\.codex\attachments\27e11de1-1d50-4424-849c-8637be00240a\pasted-text.txt"),
    "ECS-003-RM-B05": Path(r"C:\Users\Fletc\.codex\attachments\fce9bdc8-d324-4187-bf46-e32832e31206\pasted-text.txt"),
    "ECS-003-RM-B06": Path(r"C:\Users\Fletc\.codex\attachments\ab0022af-d7fd-4010-9bac-b8b82caa9911\pasted-text.txt"),
    "ECS-003-RM-B08": Path(r"C:\Users\Fletc\.codex\attachments\86bc53fa-107a-4c30-ad9a-3f300e33a327\pasted-text.txt"),
    "ECS-003-RM-B09": Path(r"C:\Users\Fletc\.codex\attachments\f98b7b50-8012-480d-bbe0-a5878458b3fa\pasted-text.txt"),
}

PROGRAM_BINDINGS = {
    "ECS-003-RM-B01": {
        "monitoring_evidence": DOC_ROOT / "MONITORING_RM002_B06_DEPENDENCY_DISCOVERY_RECONCILIATION",
        "primary_completion": DOC_ROOT / "MONITORING_RM002_B06_DEPENDENCY_DISCOVERY_RECONCILIATION" / "completion_report.json",
        "constitutional_function": "dependency_derived_implementation_discovery",
    },
    "ECS-003-RM-B02": {
        "monitoring_evidence": DOC_ROOT / "MONITORING_RM002_B02_BEHAVIORAL_VERIFICATION",
        "primary_completion": DOC_ROOT / "MONITORING_RM002_B02_BEHAVIORAL_VERIFICATION" / "completion_report.json",
        "constitutional_function": "behavioral_verification",
    },
    "ECS-003-RM-B04": {
        "monitoring_evidence": DOC_ROOT / "MONITORING_RM002_B04_FINAL_CERTIFICATION",
        "primary_completion": DOC_ROOT / "MONITORING_RM002_B04_FINAL_CERTIFICATION" / "completion_report.json",
        "constitutional_function": "initial_proof_generation_and_certification",
    },
    "ECS-003-RM-B05": {
        "monitoring_evidence": DOC_ROOT / "MONITORING_RM002_B05_CLEAN_ROOM_NEGATIVE_VALIDATION",
        "primary_completion": DOC_ROOT / "MONITORING_RM002_B05_CLEAN_ROOM_NEGATIVE_VALIDATION" / "completion_report.json",
        "constitutional_function": "independent_reproduction_audit",
    },
    "ECS-003-RM-B06": {
        "monitoring_evidence": DOC_ROOT / "MONITORING_RM002_B06_DEPENDENCY_DISCOVERY_RECONCILIATION",
        "primary_completion": DOC_ROOT / "MONITORING_RM002_B06_DEPENDENCY_DISCOVERY_RECONCILIATION" / "completion_report.json",
        "constitutional_function": "behavioral_coverage_and_dependency_discovery_remediation",
    },
    "ECS-003-RM-B08": {
        "monitoring_evidence": DOC_ROOT / "MONITORING_RM002_B08_CLEAN_ROOM_REPRODUCIBILITY",
        "primary_completion": DOC_ROOT / "MONITORING_RM002_B08_CLEAN_ROOM_REPRODUCIBILITY" / "completion_report.json",
        "constitutional_function": "clean_room_reproducibility_remediation",
    },
    "ECS-003-RM-B09": {
        "monitoring_evidence": DOC_ROOT / "MONITORING_RM002_B09_FAIL_CLOSED_CERTIFICATION",
        "primary_completion": DOC_ROOT / "MONITORING_RM002_B09_FAIL_CLOSED_CERTIFICATION" / "completion_report.json",
        "constitutional_function": "fail_closed_certification_validation",
    },
}

OMITTED_SERIES = {
    "ECS-003-RM-B03": "NOT_SUPPLIED_IN_CURRENT_EXECUTION_PACKAGE",
    "ECS-003-RM-B07": "NOT_SUPPLIED_IN_CURRENT_EXECUTION_PACKAGE; B08 records B07 input as formally unavailable",
}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _payload_digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _copy_source_orders() -> list[dict[str, Any]]:
    SOURCE_ORDER_DIR.mkdir(parents=True, exist_ok=True)
    registry: list[dict[str, Any]] = []
    for order_id, source_path in sorted(SOURCE_ORDERS.items()):
        copied_path = SOURCE_ORDER_DIR / f"{order_id}.txt"
        shutil.copyfile(source_path, copied_path)
        text = copied_path.read_text(encoding="utf-8", errors="replace")
        registry.append(
            {
                "order_id": order_id,
                "source_attachment": str(source_path),
                "committed_copy": _relative(copied_path),
                "sha256": _file_digest(copied_path),
                "line_count": len(text.splitlines()),
                "byte_count": copied_path.stat().st_size,
                "disposition": "SOURCE_ORDER_PRESERVED",
            }
        )
    return registry


def _artifact_manifest(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    entries: list[dict[str, Any]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        entries.append(
            {
                "path": _relative(path),
                "sha256": _file_digest(path),
                "bytes": path.stat().st_size,
            }
        )
    return entries


def _program_registry(source_registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_by_id = {entry["order_id"]: entry for entry in source_registry}
    registry: list[dict[str, Any]] = []
    for order_id, binding in sorted(PROGRAM_BINDINGS.items()):
        completion_path = binding["primary_completion"]
        completion = _read_json(completion_path)
        evidence_manifest = _artifact_manifest(binding["monitoring_evidence"])
        terminal = completion.get("status") == "COMPLETE"
        registry.append(
            {
                "order_id": order_id,
                "constitutional_function": binding["constitutional_function"],
                "source_order_digest": source_by_id[order_id]["sha256"],
                "source_order_copy": source_by_id[order_id]["committed_copy"],
                "monitoring_evidence_root": _relative(binding["monitoring_evidence"]),
                "primary_completion_report": _relative(completion_path),
                "primary_completion_sha256": _file_digest(completion_path),
                "primary_completion": completion,
                "evidence_artifact_count": len(evidence_manifest),
                "evidence_manifest_digest": _payload_digest(evidence_manifest),
                "terminal_disposition": "COMPLETE" if terminal else "INCOMPLETE",
            }
        )
    return registry


def _traceability(program_registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "trace_id": f"ECS003-RM-TRACE-{index:03d}",
            "source_order": record["order_id"],
            "constitutional_function": record["constitutional_function"],
            "governing_evidence_root": record["monitoring_evidence_root"],
            "completion_report": record["primary_completion_report"],
            "completion_digest": record["primary_completion_sha256"],
            "terminal_disposition": record["terminal_disposition"],
        }
        for index, record in enumerate(program_registry, start=1)
    ]


def _readiness(program_registry: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {record["order_id"]: record["primary_completion"] for record in program_registry}
    checks = {
        "all_supplied_programs_complete": all(record["terminal_disposition"] == "COMPLETE" for record in program_registry),
        "b04_unconditional_pass": by_id["ECS-003-RM-B04"].get("final_verdict") == "UNCONDITIONAL_PASS",
        "b05_independent_pass": by_id["ECS-003-RM-B05"].get("independent_verdict") == "UNCONDITIONAL_PASS",
        "b06_reproducible_discovery": by_id["ECS-003-RM-B06"].get("independently_reproducible") is True,
        "b08_clean_room_ready": by_id["ECS-003-RM-B08"].get("reproducibility_readiness") == "READY_FOR_FAIL_CLOSED_CERTIFICATION_VALIDATION",
        "b09_fail_closed_ready": by_id["ECS-003-RM-B09"].get("certification_system_readiness") == "READY_FOR_FINAL_INDEPENDENT_ECS003_CERTIFICATION",
        "b09_no_open_blockers": by_id["ECS-003-RM-B09"].get("open_blockers") == 0,
    }
    ready = all(checks.values())
    return {
        "package": "ECS-003-RM program reconciliation",
        "status": "COMPLETE" if ready else "INCOMPLETE",
        "readiness": "READY_FOR_ECS003_REMEDIATION_AUDIT" if ready else "NOT_READY_FOR_ECS003_REMEDIATION_AUDIT",
        "checks": checks,
        "omitted_series": OMITTED_SERIES,
        "supplied_program_count": len(program_registry),
        "constitutional_doctrine_modified": False,
        "implementation_behavior_modified": False,
        "repository_wide_certification_executed": False,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_registry = _copy_source_orders()
    program_registry = _program_registry(source_registry)
    traceability = _traceability(program_registry)
    readiness = _readiness(program_registry)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    _write_json(OUTPUT_DIR / "ecs003_rm_program_source_order_registry.json", source_registry)
    _write_json(OUTPUT_DIR / "ecs003_rm_program_order_registry.json", program_registry)
    _write_json(OUTPUT_DIR / "ecs003_rm_cross_program_traceability_registry.json", traceability)
    _write_json(OUTPUT_DIR / "ecs003_rm_omitted_series_disposition_registry.json", OMITTED_SERIES)
    _write_json(OUTPUT_DIR / "ecs003_rm_readiness_assessment.json", readiness)

    for record in program_registry:
        out_name = f"{record['order_id'].lower().replace('-', '_')}_registry.json"
        _write_json(OUTPUT_DIR / out_name, record)

    completion_report = {
        "package": "ECS-003-RM program reconciliation and audit packaging",
        "status": readiness["status"],
        "readiness": readiness["readiness"],
        "generated_at": generated_at,
        "supplied_orders": [record["order_id"] for record in program_registry],
        "omitted_series": OMITTED_SERIES,
        "program_registry_digest": _payload_digest(program_registry),
        "traceability_digest": _payload_digest(traceability),
        "source_order_registry_digest": _payload_digest(source_registry),
        "completion_criteria": {
            "source_orders_preserved": len(source_registry) == len(SOURCE_ORDERS),
            "all_supplied_programs_terminal": readiness["checks"]["all_supplied_programs_complete"],
            "cross_program_traceability_generated": len(traceability) == len(program_registry),
            "audit_readiness_recorded": readiness["readiness"] == "READY_FOR_ECS003_REMEDIATION_AUDIT",
        },
    }
    _write_json(OUTPUT_DIR / "ecs003_rm_completion_report.json", completion_report)
    _write_json(OUTPUT_DIR / "completion_report.json", completion_report)
    _write_text(
        OUTPUT_DIR / "README.md",
        "\n".join(
            [
                "# ECS-003-RM Program Reconciliation",
                "",
                "This package preserves the supplied ECS-003-RM B01, B02, B04, B05, B06, B08, and B09 orders,",
                "binds each order to the existing Monitoring ECS-003 remediation evidence, and records omitted series disposition.",
                "",
                f"Readiness: {readiness['readiness']}",
                f"Status: {readiness['status']}",
                "",
                "Primary entry point: completion_report.json",
                "",
            ]
        ),
    )


if __name__ == "__main__":
    main()
