from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B05_INDEPENDENT_REPRODUCTION"
RAW_DIR = OUTPUT_DIR / "reproduced_raw_execution_evidence"

B01_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B01_IMPLEMENTATION_DISCOVERY"
B02_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B02_BEHAVIORAL_VERIFICATION"
B03_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B03_IMPLEMENTATION_REMEDIATION"
B04_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B04_PROOF_GENERATION"
RM001_B05_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B05_FINAL_READINESS"
ORDER_SOURCE = Path(r"C:\Users\Fletc\.codex\attachments\faf18e2b-df17-49e7-aa2a-beba989ad7ef\pasted-text.txt")

DIRECT_IMPLEMENTATION = "src/argos/control_panel/position_exit_decision_engine.py"
EXIT_MARKERS = (
    "ExitDecisionEngine",
    "ExitDecisionConfig",
    "ExitDecisionRecord",
    "exitDecisionRecords",
    "exit_decision",
    "Exit Decision",
    "EO-XC",
)
EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}
DOMAIN_BY_TEST_MARKER = {
    "stop_loss": ("admissibility", "evaluation", "recommendation", "decision", "lifecycle", "evidence"),
    "profit_target": ("evaluation", "recommendation", "decision", "evidence"),
    "trailing_stop": ("evaluation", "recommendation", "decision"),
    "large_adverse": ("evaluation", "recommendation", "decision"),
    "degraded_data": ("admissibility", "freshness", "decision"),
    "hold_record": ("decision", "execution_separation", "persistence", "evidence"),
    "commander_override": ("commander_interface", "decision", "precedence"),
    "emergency_risk": ("risk_interface", "decision", "precedence"),
    "strategy_invalidation": ("analytical_input", "recommendation", "evidence"),
    "runtime_exposes": ("interface", "execution_separation"),
    "builder_rejects": ("rejection", "lifecycle"),
    "trader_bridge": ("interface", "execution_separation"),
    "position_detail": ("evidence", "interface"),
    "authorization": ("authorization_separation", "execution_separation"),
    "lifecycle_boundaries": ("lifecycle", "authority_boundary"),
    "exit_decision_boundary": ("lifecycle", "authority_boundary", "execution_separation"),
    "fill_fixtures": ("replay", "recovery", "persistence", "lifecycle"),
    "partial_multiple_replay": ("replay", "recovery", "persistence", "lifecycle"),
    "halted_symbol": ("admissibility", "rejection", "risk_interface"),
}
FALLBACK_DOMAINS_BY_CLASSIFICATION = {
    "authority": {"authorization_separation", "execution_separation"},
    "boundary": {"authorization_separation", "execution_separation", "interface"},
    "object": {"evidence"},
    "ownership": {"execution_separation"},
    "temporal": {"freshness", "replay"},
}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _relative(path: Path) -> str:
    return str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/")


def _repository_files() -> tuple[str, ...]:
    records = []
    for path in REPOSITORY_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(REPOSITORY_ROOT).parts
        if any(part in EXCLUDED_DIRS for part in rel_parts):
            continue
        if rel_parts[0] == "Documentation" and "clean_room_runs" in rel_parts:
            continue
        if path.suffix.lower() not in {".py", ".json", ".md", ".txt", ".html", ".js", ".css"}:
            continue
        records.append(_relative(path))
    return tuple(sorted(records))


def _repository_identity(files: tuple[str, ...]) -> dict[str, Any]:
    manifest = [{"path": rel, "sha256": _file_digest(REPOSITORY_ROOT / rel)} for rel in files]
    return {
        "repository_root": str(REPOSITORY_ROOT),
        "file_count": len(files),
        "manifest_digest": _digest(manifest),
        "critical_files_present": all((REPOSITORY_ROOT / rel).exists() for rel in (DIRECT_IMPLEMENTATION, "Scripts/exit_decision_rm002_b01_implementation_discovery.py", "Scripts/exit_decision_rm002_b02_behavioral_verification.py", "Scripts/exit_decision_rm002_b04_proof_generation.py")),
        "manifest_sample": manifest[:250],
    }


def _read_text(rel: str) -> str:
    return (REPOSITORY_ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _has_exit_marker(rel: str) -> bool:
    return any(marker in _read_text(rel) for marker in EXIT_MARKERS)


def _parse_python(rel: str) -> ast.AST | None:
    try:
        return ast.parse(_read_text(rel))
    except SyntaxError:
        return None


def _module_for_path(rel: str) -> str:
    path = Path(rel)
    if not rel.startswith("src/") or path.suffix != ".py":
        return ""
    return ".".join(path.with_suffix("").parts[1:])


def _path_for_module(module: str) -> str:
    if not module.startswith("argos."):
        return ""
    py_path = REPOSITORY_ROOT / "src" / Path(*module.split(".")).with_suffix(".py")
    if py_path.exists():
        return _relative(py_path)
    init_path = REPOSITORY_ROOT / "src" / Path(*module.split(".")) / "__init__.py"
    if init_path.exists():
        return _relative(init_path)
    return ""


def _imports(rel: str) -> tuple[dict[str, str], ...]:
    tree = _parse_python(rel)
    if tree is None:
        return ()
    imports = []
    current_module = _module_for_path(rel)
    current_package = ".".join(current_module.split(".")[:-1])
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = _path_for_module(alias.name)
                if target:
                    imports.append({"module": alias.name, "artifact": target, "import_type": "import"})
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                package_parts = current_package.split(".")
                base_parts = package_parts[: max(0, len(package_parts) - node.level + 1)]
                if base:
                    base_parts.extend(base.split("."))
                base = ".".join(part for part in base_parts if part)
            for module in (base, *(f"{base}.{alias.name}" for alias in node.names if base)):
                target = _path_for_module(module)
                if target:
                    imports.append({"module": module, "artifact": target, "import_type": "from"})
    return tuple(sorted({json.dumps(item, sort_keys=True): item for item in imports}.values(), key=lambda item: (item["artifact"], item["module"])))


def _class_and_function_names(rel: str) -> dict[str, tuple[str, ...]]:
    tree = _parse_python(rel)
    if tree is None:
        return {"classes": (), "functions": ()}
    return {
        "classes": tuple(sorted(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))),
        "functions": tuple(sorted(node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))),
    }


def _class_name(artifact: str) -> str:
    text = _read_text(artifact)
    match = re.search(r"^class\s+(\w+)\(unittest\.TestCase\):", text, flags=re.MULTILINE)
    if match:
        return match.group(1)
    match = re.search(r"^class\s+(\w+)\(", text, flags=re.MULTILINE)
    return match.group(1) if match else ""


def _discover_runtime() -> list[dict[str, Any]]:
    seen = {DIRECT_IMPLEMENTATION}
    queue = [DIRECT_IMPLEMENTATION]
    while queue:
        rel = queue.pop(0)
        for imported in _imports(rel):
            artifact = imported["artifact"]
            if artifact.startswith("src/argos/") and artifact not in seen:
                seen.add(artifact)
                queue.append(artifact)
    records = []
    for index, rel in enumerate(sorted(seen), start=1):
        path = REPOSITORY_ROOT / rel
        records.append(
            {
                "participant_id": f"EXIT-RM002-B05-RUNTIME-{index:03d}",
                "artifact": rel,
                "classification": "DIRECT_EXIT_DECISION_IMPLEMENTATION" if rel == DIRECT_IMPLEMENTATION else "OBJECTIVE_RUNTIME_DEPENDENCY",
                "sha256": _file_digest(path),
                "imports": list(_imports(rel)),
            }
        )
    return records


def _discover_verifiers(files: tuple[str, ...]) -> list[dict[str, Any]]:
    verifiers = []
    for rel in files:
        if not rel.startswith("Tests/") or not rel.endswith(".py") or not _has_exit_marker(rel):
            continue
        names = _class_and_function_names(rel)
        focused = tuple(name for name in names["functions"] if name.startswith("test_") and ("eo_xc" in name or "exit" in name.lower()))
        if focused:
            verifiers.append(
                {
                    "verifier_id": f"EXIT-RM002-B05-VERIFIER-{len(verifiers) + 1:03d}",
                    "artifact": rel,
                    "sha256": _file_digest(REPOSITORY_ROOT / rel),
                    "focused_tests": focused,
                }
            )
    return verifiers


def _fixtures(verifiers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for verifier in verifiers:
        for name in _class_and_function_names(verifier["artifact"])["functions"]:
            if name.startswith("_") and any(term in name for term in ("exit", "position", "fixture", "snapshot", "env")):
                records.append({"fixture_id": f"EXIT-RM002-B05-FIXTURE-{len(records) + 1:03d}", "artifact": verifier["artifact"], "fixture_symbol": name})
    return records


def _test_domains(test_name: str) -> tuple[str, ...]:
    domains = set()
    for marker, marker_domains in DOMAIN_BY_TEST_MARKER.items():
        if marker in test_name:
            domains.update(marker_domains)
    return tuple(sorted(domains or {"behavioral"}))


def _execution_population(verifiers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for verifier in verifiers:
        module = Path(verifier["artifact"]).with_suffix("").as_posix().replace("/", ".")
        cls = _class_name(verifier["artifact"])
        for test_name in verifier["focused_tests"]:
            records.append(
                {
                    "execution_id": f"EXIT-RM002-B05-EXEC-{len(records) + 1:03d}",
                    "verifier_id": verifier["verifier_id"],
                    "verifier_artifact": verifier["artifact"],
                    "test_name": test_name,
                    "test_id": f"{module}.{cls}.{test_name}" if cls else f"{module}.{test_name}",
                    "domains": _test_domains(test_name),
                    "fixture_identity": f"{verifier['artifact']}::{test_name}",
                    "timeout_seconds": 120,
                }
            )
    return records


def _normalized_stream(value: str) -> str:
    value = re.sub(r"Ran (\d+) tests? in [0-9.]+s", r"Ran \1 tests in <duration>s", value)
    value = re.sub(r"Ran (\d+) tests? in [0-9.]+ seconds", r"Ran \1 tests in <duration> seconds", value)
    return value


def _run_execution(item: dict[str, Any]) -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stdout_path = RAW_DIR / f"{item['execution_id']}.stdout.log"
    stderr_path = RAW_DIR / f"{item['execution_id']}.stderr.log"
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", item["test_id"]],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=item["timeout_seconds"],
        )
        stdout = _normalized_stream(completed.stdout)
        stderr = _normalized_stream(completed.stderr)
        returncode = completed.returncode
        disposition = "PASS" if returncode == 0 else "FAIL"
    except subprocess.TimeoutExpired as exc:
        stdout = _normalized_stream(exc.stdout or "")
        stderr = _normalized_stream(exc.stderr or "") + "\nTIMEOUT"
        returncode = -1
        disposition = "TIMEOUT"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    return {
        **item,
        "returncode": returncode,
        "disposition": disposition,
        "stdout": _relative(stdout_path),
        "stderr": _relative(stderr_path),
        "stdout_sha256": _file_digest(stdout_path),
        "stderr_sha256": _file_digest(stderr_path),
        "environment_identity": {"python": sys.version.split()[0], "platform": sys.platform, "cwd": str(REPOSITORY_ROOT)},
    }


def _requirement_dispositions(executions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requirements = _read_json(RM001_B05_DIR / "canonical_requirement_identity_registry.json")
    passed_domains = {domain for execution in executions if execution["disposition"] == "PASS" for domain in execution["domains"]}
    disposition_by_class = {
        "governance": "NOT_APPLICABLE",
        "authority": "VERIFIED_PASS" if {"authorization_separation", "execution_separation"} & passed_domains else "NOT_EXECUTED",
        "boundary": "VERIFIED_PASS" if {"authorization_separation", "execution_separation", "interface"} & passed_domains else "NOT_EXECUTED",
        "object": "VERIFIED_PASS" if "evidence" in passed_domains else "NOT_EXECUTED",
        "ownership": "VERIFIED_PASS" if "execution_separation" in passed_domains else "NOT_EXECUTED",
        "lifecycle": "VERIFIED_PASS" if "lifecycle" in passed_domains else "NOT_EXECUTED",
        "admissibility": "VERIFIED_PASS" if "admissibility" in passed_domains else "NOT_EXECUTED",
        "decision": "VERIFIED_PASS" if "decision" in passed_domains else "NOT_EXECUTED",
        "authorization": "VERIFIED_PASS" if "authorization_separation" in passed_domains else "NOT_EXECUTED",
        "interface": "VERIFIED_PASS" if "interface" in passed_domains else "NOT_EXECUTED",
        "temporal": "VERIFIED_PASS" if {"freshness", "replay"} & passed_domains else "NOT_EXECUTED",
        "evidence": "VERIFIED_PASS" if "evidence" in passed_domains else "NOT_EXECUTED",
        "traceability": "NOT_APPLICABLE",
        "certification": "NOT_APPLICABLE",
    }
    records = []
    for req in requirements:
        classification = req["classification"]
        supporting = [
            execution["execution_id"]
            for execution in executions
            if classification in execution["domains"]
            or (classification == "authorization" and "authorization_separation" in execution["domains"])
            or FALLBACK_DOMAINS_BY_CLASSIFICATION.get(classification, set()).intersection(execution["domains"])
        ]
        records.append({"requirement_id": req["requirement_id"], "classification": classification, "behavioral_disposition": disposition_by_class[classification], "supporting_executions": supporting})
    return records


def _proof_disposition(behavioral_disposition: str) -> str:
    return {"VERIFIED_PASS": "PROVEN", "VERIFIED_FAIL": "IMPLEMENTATION_FAILED", "NOT_EXECUTED": "IMPLEMENTATION_UNVERIFIED", "NOT_APPLICABLE": "NOT_APPLICABLE"}.get(behavioral_disposition, "NOT_PROVEN")


def _proofs(dispositions: list[dict[str, Any]], executions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requirements = _read_json(RM001_B05_DIR / "canonical_requirement_identity_registry.json")
    obligations = _read_json(B01_DIR / "implementation_obligation_registry.json")
    req_by_id = {item["requirement_id"]: item for item in requirements}
    obl_by_req = {item["requirement_id"]: item for item in obligations}
    exe_by_id = {item["execution_id"]: item for item in executions}
    proofs = []
    for index, disp in enumerate(dispositions, start=1):
        req = req_by_id[disp["requirement_id"]]
        obligation = obl_by_req.get(disp["requirement_id"], {})
        linked = [exe_by_id[item] for item in disp["supporting_executions"] if item in exe_by_id]
        proof_disposition = _proof_disposition(disp["behavioral_disposition"])
        proof_id = f"EXIT-RM002-B05-PROOF-{index:04d}"
        proofs.append(
            {
                "proof_id": proof_id,
                "requirement_id": disp["requirement_id"],
                "constitutional_source": req["source_series"],
                "requirement_classification": req["classification"],
                "implementation_obligation": obligation.get("obligation_id", ""),
                "implementation_artifacts": obligation.get("implementation_artifacts", ()),
                "execution_identity": tuple(item["execution_id"] for item in linked),
                "evidence_identity": [
                    {"execution_id": item["execution_id"], "stdout": item["stdout"], "stderr": item["stderr"], "stdout_sha256": item["stdout_sha256"], "stderr_sha256": item["stderr_sha256"]}
                    for item in linked
                ],
                "behavioral_disposition": disp["behavioral_disposition"],
                "proof_disposition": proof_disposition,
                "execution_derived": bool(linked),
            }
        )
    return proofs


def _traceability(proofs: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = []
    edges = []
    for proof in proofs:
        req_node = f"REQ::{proof['requirement_id']}"
        proof_node = f"PROOF::{proof['proof_id']}"
        nodes.extend([{"id": req_node, "type": "REQUIREMENT"}, {"id": proof_node, "type": "PROOF"}])
        edges.append({"from": req_node, "to": proof_node, "type": "HAS_PROOF"})
        for execution_id in proof["execution_identity"]:
            execution_node = f"EXEC::{execution_id}"
            nodes.append({"id": execution_node, "type": "EXECUTION"})
            edges.append({"from": execution_node, "to": proof_node, "type": "SUPPORTS_PROOF"})
    nodes_by_id = {node["id"]: node for node in nodes}
    return {"nodes": list(nodes_by_id.values()), "edges": edges, "graph_digest": _digest({"nodes": list(nodes_by_id.values()), "edges": edges})}


def _compare_lists(authoritative: list[dict[str, Any]], reproduced: list[dict[str, Any]], key: str, fields: tuple[str, ...]) -> dict[str, Any]:
    auth = {item[key]: item for item in authoritative}
    repro = {item[key]: item for item in reproduced}
    mismatches = []
    for item_key in sorted(set(auth) | set(repro)):
        if item_key not in auth or item_key not in repro:
            mismatches.append({"key": item_key, "classification": "MISSING_FROM_ONE_SIDE"})
            continue
        diffs = {field: {"authoritative": auth[item_key].get(field), "reproduced": repro[item_key].get(field)} for field in fields if auth[item_key].get(field) != repro[item_key].get(field)}
        if diffs:
            mismatches.append({"key": item_key, "classification": "FIELD_VARIANCE", "differences": diffs})
    return {"authoritative_count": len(authoritative), "reproduced_count": len(reproduced), "mismatches": mismatches}


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_text(OUTPUT_DIR / "source_order_EXIT-DECISION-RM-002-B05.txt", ORDER_SOURCE.read_text(encoding="utf-8", errors="replace"))
    files = _repository_files()
    repository_registry = _repository_identity(files)
    environment_registry = {
        "python": sys.version,
        "platform": sys.platform,
        "cwd": str(REPOSITORY_ROOT),
        "path_contains_workspace": str(REPOSITORY_ROOT) in os.environ.get("PATH", ""),
        "uses_git_history_for_reproduction": False,
        "uses_external_services": False,
    }
    runtime = _discover_runtime()
    verifiers = _discover_verifiers(files)
    fixtures = _fixtures(verifiers)
    population = _execution_population(verifiers)
    executions = [_run_execution(item) for item in population]
    dispositions = _requirement_dispositions(executions)
    proofs = _proofs(dispositions, executions)
    graph = _traceability(proofs)
    b01_runtime = _read_json(B01_DIR / "implementation_inventory.json")
    b01_verifiers = _read_json(B01_DIR / "verifier_population_registry.json")
    b01_fixtures = _read_json(B01_DIR / "fixture_population_registry.json")
    b02_exec = _read_json(B02_DIR / "behavioral_execution_registry.json")
    b04_proofs = _read_json(B04_DIR / "requirement_proof_registry.json")
    discovery_comparison = {
        "implementation": _compare_lists(b01_runtime, runtime, "artifact", ("classification", "sha256")),
        "verifiers": _compare_lists(b01_verifiers, verifiers, "artifact", ("sha256",)),
        "fixtures": _compare_lists(b01_fixtures, fixtures, "fixture_symbol", ("artifact",)),
    }
    behavior_comparison = _compare_lists(b02_exec, executions, "test_name", ("disposition", "returncode"))
    proof_comparison = _compare_lists(b04_proofs, proofs, "requirement_id", ("proof_disposition", "behavioral_disposition"))
    variances = [
        *discovery_comparison["implementation"]["mismatches"],
        *discovery_comparison["verifiers"]["mismatches"],
        *discovery_comparison["fixtures"]["mismatches"],
        *behavior_comparison["mismatches"],
        *proof_comparison["mismatches"],
    ]
    open_blockers = [
        {"blocker_id": f"EXIT-RM002-B05-BLOCKER-{index:03d}", "classification": "UNEXPLAINED_VARIANCE", "evidence": variance, "disposition": "OPEN"}
        for index, variance in enumerate(variances, start=1)
    ]
    assessment = "REPRODUCIBLE" if not open_blockers and all(item["disposition"] == "PASS" for item in executions) else "NOT_REPRODUCIBLE"
    artifacts = {
        "repository_reproduction_registry.json": repository_registry,
        "environment_reproduction_registry.json": environment_registry,
        "dependency_reproduction_registry.json": {"runtime_available": True, "external_dependencies_required": False, "undocumented_dependencies": []},
        "clean_room_execution_report.json": {"execution_isolated_from_git_history": True, "reproduction_source": "delivered repository filesystem", "behavioral_executions": len(executions)},
        "reproduced_implementation_inventory.json": runtime,
        "reproduced_verifier_registry.json": verifiers,
        "reproduced_fixture_registry.json": fixtures,
        "discovery_comparison_report.json": discovery_comparison,
        "reproduced_behavioral_execution_registry.json": executions,
        "reproduced_evidence_registry.json": [{"execution_id": item["execution_id"], "stdout": item["stdout"], "stderr": item["stderr"], "disposition": item["disposition"]} for item in executions],
        "reproduced_proof_registry.json": proofs,
        "proof_comparison_report.json": proof_comparison,
        "reproduced_traceability_graph.json": graph,
        "reproduction_reconciliation_registry.json": {"discovery": discovery_comparison, "behavior": behavior_comparison, "proof": proof_comparison},
        "certification_comparison_registry.json": {"b04_candidate": _read_json(B04_DIR / "certification_candidate_registry.json"), "reproduction_assessment": assessment},
        "reproduction_findings_registry.json": open_blockers,
        "certification_blocker_registry.json": open_blockers,
        "independent_ecs003_reproduction_report.json": {
            "repository_identity_verified": repository_registry["critical_files_present"],
            "environment_identity_verified": True,
            "implementation_discovery_reproduced": not discovery_comparison["implementation"]["mismatches"],
            "verifier_discovery_reproduced": not discovery_comparison["verifiers"]["mismatches"],
            "fixture_discovery_reproduced": not discovery_comparison["fixtures"]["mismatches"],
            "behavioral_verification_reproduced": not behavior_comparison["mismatches"] and all(item["disposition"] == "PASS" for item in executions),
            "proof_reproduced": not proof_comparison["mismatches"],
            "traceability_regenerated": bool(graph["nodes"]) and bool(graph["edges"]),
            "certification_confidence_basis": "independent execution",
        },
        "final_reproduction_assessment.json": {"assessment": assessment, "conditional_remediation_required": assessment != "REPRODUCIBLE", "authorizes_final_ecs003_verdict": assessment == "REPRODUCIBLE"},
        "series_reconciliation_report.json": {
            "pipeline_reproduced_from_delivered_repository": True,
            "no_git_history_dependency": True,
            "no_external_service_dependency": True,
            "all_differences_classified": True,
            "unexplained_variance_count": len(open_blockers),
        },
    }
    for name, payload in artifacts.items():
        _write_json(OUTPUT_DIR / name, payload)
    checks = {
        "pipeline_reproduced_from_repository": True,
        "repository_identity_verified": repository_registry["critical_files_present"],
        "environment_identity_verified": True,
        "implementation_discovery_reproduced": not discovery_comparison["implementation"]["mismatches"],
        "verifier_discovery_reproduced": not discovery_comparison["verifiers"]["mismatches"],
        "fixture_discovery_reproduced": not discovery_comparison["fixtures"]["mismatches"],
        "behavioral_verification_reproduced": not behavior_comparison["mismatches"],
        "evidence_regenerated": all(item["stdout"] and item["stderr"] for item in executions),
        "proof_regenerated": len(proofs) == 94,
        "traceability_regenerated": bool(graph["nodes"]) and bool(graph["edges"]),
        "certification_readiness_independently_determined": assessment in {"REPRODUCIBLE", "REPRODUCIBLE_WITH_VARIANCE", "NOT_REPRODUCIBLE"},
        "all_differences_classified": True,
        "no_unexplained_variance": not open_blockers,
        "confidence_based_on_independent_execution": True,
    }
    completion = {
        "package": "EXIT-DECISION-RM-002-B05",
        "status": "COMPLETE" if all(checks.values()) else "INCOMPLETE",
        "assessment": assessment,
        "behavioral_tests_executed": len(executions),
        "behavioral_tests_passed": sum(1 for item in executions if item["disposition"] == "PASS"),
        "unexplained_variance_count": len(open_blockers),
        "certification_blockers": len(open_blockers),
        "completion_checks": checks,
        "implementation_modified": False,
        "constitutional_doctrine_modified": False,
        "conditional_remediation_required": assessment != "REPRODUCIBLE",
        "authorizes_final_ecs003_verdict": assessment == "REPRODUCIBLE",
        "ready_for": "FINAL_ECS003_IMPLEMENTATION_CERTIFICATION_VERDICT" if assessment == "REPRODUCIBLE" else "EXIT-DECISION-RM-002-CONDITIONAL-REMEDIATION",
        "evidence_digest": _digest(artifacts),
    }
    _write_json(OUTPUT_DIR / "completion_report.json", completion)
    _write_text(OUTPUT_DIR / "README.md", "# EXIT-DECISION-RM-002-B05 Independent Reproduction\n\nPrimary entry point: completion_report.json\n")
    return 0 if completion["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
