from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
OUTPUT_DIR = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM002_B01_IMPLEMENTATION_DISCOVERY"

FROZEN_BASELINE = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B05_FINAL_READINESS" / "completion_report.json"
FROZEN_REQUIREMENTS = REPOSITORY_ROOT / "Documentation" / "EXIT_DECISION_RM001_B05_FINAL_READINESS" / "canonical_requirement_identity_registry.json"
DIRECT_IMPLEMENTATION = "src/argos/control_panel/position_exit_decision_engine.py"
DIRECT_TEST = "Tests/test_argos_control_panel_dashboard.py"

EXIT_MARKERS = (
    "ExitDecisionEngine",
    "ExitDecisionConfig",
    "ExitDecisionRecord",
    "exitDecisionRecords",
    "exit_decision",
    "Exit Decision",
    "EO-XC",
)


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


def _git_files() -> tuple[str, ...]:
    output = subprocess.check_output(["git", "ls-files"], cwd=REPOSITORY_ROOT, text=True)
    return tuple(line.strip() for line in output.splitlines() if line.strip())


def _candidate_digest() -> str:
    payload = {
        "frozen_baseline": _file_digest(FROZEN_BASELINE),
        "frozen_requirements": _file_digest(FROZEN_REQUIREMENTS),
        "direct_implementation": _file_digest(REPOSITORY_ROOT / DIRECT_IMPLEMENTATION),
    }
    return _digest(payload)


def _module_for_path(rel: str) -> str:
    path = Path(rel)
    if not rel.startswith("src/") or path.suffix != ".py":
        return ""
    parts = path.with_suffix("").parts[1:]
    return ".".join(parts)


def _path_for_module(module: str) -> str:
    if not module.startswith("argos."):
        return ""
    candidate = SRC_ROOT / Path(*module.split(".")).with_suffix(".py")
    if candidate.exists():
        return _relative(candidate)
    package_init = SRC_ROOT / Path(*module.split(".")) / "__init__.py"
    if package_init.exists():
        return _relative(package_init)
    return ""


def _read_text(rel: str) -> str:
    return (REPOSITORY_ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _parse_python(rel: str) -> ast.AST | None:
    try:
        return ast.parse(_read_text(rel))
    except SyntaxError:
        return None


def _imports(rel: str) -> tuple[dict[str, str], ...]:
    tree = _parse_python(rel)
    if tree is None:
        return ()
    imports: list[dict[str, str]] = []
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
            target = _path_for_module(base)
            if target:
                imports.append({"module": base, "artifact": target, "import_type": "from"})
            for alias in node.names:
                nested = f"{base}.{alias.name}" if base else alias.name
                nested_target = _path_for_module(nested)
                if nested_target:
                    imports.append({"module": nested, "artifact": nested_target, "import_type": "from_name"})
    return tuple(sorted({json.dumps(item, sort_keys=True): item for item in imports}.values(), key=lambda item: (item["artifact"], item["module"])))


def _class_and_function_names(rel: str) -> dict[str, tuple[str, ...]]:
    tree = _parse_python(rel)
    if tree is None:
        return {"classes": (), "functions": ()}
    classes = sorted(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    functions = sorted(node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
    return {"classes": tuple(classes), "functions": tuple(functions)}


def _has_exit_marker(rel: str) -> bool:
    text = _read_text(rel)
    return any(marker in text for marker in EXIT_MARKERS)


def _discover_runtime_population() -> list[dict[str, Any]]:
    candidate_rels = [DIRECT_IMPLEMENTATION]
    seen = set(candidate_rels)
    queue = list(candidate_rels)
    while queue:
        rel = queue.pop(0)
        if not rel.endswith(".py"):
            continue
        for imported in _imports(rel):
            artifact = imported["artifact"]
            if artifact.startswith("src/argos/") and artifact not in seen:
                seen.add(artifact)
                queue.append(artifact)
    records = []
    for index, rel in enumerate(sorted(seen), start=1):
        path = REPOSITORY_ROOT / rel
        names = _class_and_function_names(rel)
        direct = rel == DIRECT_IMPLEMENTATION
        records.append(
            {
                "participant_id": f"EXIT-RM002-B01-RUNTIME-{index:03d}",
                "artifact": rel,
                "classification": "DIRECT_EXIT_DECISION_IMPLEMENTATION" if direct else "OBJECTIVE_RUNTIME_DEPENDENCY",
                "discovery_basis": "direct frozen Exit Decision implementation" if direct else "AST import dependency from participating implementation",
                "sha256": _file_digest(path),
                "imports": list(_imports(rel)) if rel.endswith(".py") else [],
                "classes": names["classes"],
                "functions": names["functions"],
            }
        )
    return records


def _discover_verifiers() -> list[dict[str, Any]]:
    verifiers = []
    for rel in _git_files():
        if not rel.startswith("Tests/") or not rel.endswith(".py"):
            continue
        if not _has_exit_marker(rel):
            continue
        names = _class_and_function_names(rel)
        focused = tuple(name for name in names["functions"] if "eo_xc" in name or "exit" in name.lower())
        if not focused:
            continue
        verifiers.append(
            {
                "verifier_id": f"EXIT-RM002-B01-VERIFIER-{len(verifiers) + 1:03d}",
                "artifact": rel,
                "sha256": _file_digest(REPOSITORY_ROOT / rel),
                "discovery_basis": "test artifact contains Exit Decision markers and focused test functions",
                "focused_tests": focused,
                "execution_status": "NOT_EXECUTED_UNDER_B01",
            }
        )
    return verifiers


def _fixture_markers(verifiers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fixtures = []
    for verifier in verifiers:
        rel = verifier["artifact"]
        names = _class_and_function_names(rel)
        for name in names["functions"]:
            if name.startswith("_") and any(term in name for term in ("exit", "position", "fixture", "snapshot", "env")):
                fixtures.append(
                    {
                        "fixture_id": f"EXIT-RM002-B01-FIXTURE-{len(fixtures) + 1:03d}",
                        "artifact": rel,
                        "fixture_symbol": name,
                        "discovery_basis": "private test helper used as fixture candidate; not executed under B01",
                    }
                )
    return fixtures


def _configuration_dependencies(runtime: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dependencies = []
    for participant in runtime:
        text = _read_text(participant["artifact"])
        markers = {
            "enterprise_configuration_registry": "enterprise configuration registry parameter",
            "ExitDecisionConfig": "ExitDecisionConfig dataclass",
            "os.environ": "environment variable access",
            "utc_timestamp": "enterprise timestamp utility",
        }
        for marker, basis in markers.items():
            if marker in text:
                dependencies.append(
                    {
                        "dependency_id": f"EXIT-RM002-B01-CONFIG-{len(dependencies) + 1:03d}",
                        "artifact": participant["artifact"],
                        "dependency": marker,
                        "classification": "CONFIGURATION_DEPENDENCY",
                        "discovery_basis": basis,
                    }
                )
    return dependencies


def _interface_dependencies(runtime: list[dict[str, Any]]) -> list[dict[str, Any]]:
    interfaces = []
    direct_text = _read_text(DIRECT_IMPLEMENTATION)
    interface_markers = (
        ("position_registry", "Position Registry", "inbound read and bounded recommendation gateway"),
        ("position_surveillance", "Monitoring", "inbound surveillance snapshot feed"),
        ("strategy_package_manager", "Strategy", "inbound strategy flags"),
        ("risk_context", "Risk", "inbound risk constraints and emergency state"),
        ("commander_overrides", "Commander", "inbound commander override constraints"),
        ("latestDecisions", "Trader", "outbound recommendation consumption surface"),
        ("exitDecisionRecords", "Historian", "evidence and historical custody surface"),
    )
    for marker, owner, role in interface_markers:
        if marker in direct_text:
            interfaces.append(
                {
                    "interface_id": f"EXIT-RM002-B01-IFACE-{len(interfaces) + 1:03d}",
                    "marker": marker,
                    "authority_owner": owner,
                    "interaction_role": role,
                    "artifact": DIRECT_IMPLEMENTATION,
                    "discovery_basis": "marker present in direct Exit Decision implementation signature or snapshot contract",
                }
            )
    return interfaces


def _persistence_participants(runtime: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    markers = ("self._records", "_last_decision_by_position", "snapshot", "recordAppendOnly", "audit_reference")
    for participant in runtime:
        text = _read_text(participant["artifact"])
        found = tuple(marker for marker in markers if marker in text)
        if found:
            records.append(
                {
                    "persistence_id": f"EXIT-RM002-B01-PERSIST-{len(records) + 1:03d}",
                    "artifact": participant["artifact"],
                    "markers": found,
                    "classification": "IN_MEMORY_OR_SNAPSHOT_PARTICIPANT",
                    "behavioral_status": "NOT_VERIFIED_UNDER_B01",
                }
            )
    return records


def _obligations(requirements: list[dict[str, Any]], runtime: list[dict[str, Any]], verifiers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    implementation_artifacts = tuple(item["artifact"] for item in runtime)
    verifier_artifacts = tuple(item["artifact"] for item in verifiers)
    records = []
    for index, req in enumerate(requirements, start=1):
        records.append(
            {
                "obligation_id": f"EXIT-RM002-B01-OBL-{index:04d}",
                "requirement_id": req["requirement_id"],
                "requirement_classification": req["classification"],
                "constitutional_owner": req["owner"],
                "implementation_artifacts": implementation_artifacts,
                "verifier_artifacts": verifier_artifacts,
                "discovery_basis": "frozen RM001 B05 canonical requirement mapped to dependency-derived implementation population",
                "verification_status": "PENDING_BEHAVIORAL_VERIFICATION_B02",
            }
        )
    return records


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    baseline = _read_json(FROZEN_BASELINE)
    requirements = _read_json(FROZEN_REQUIREMENTS)
    runtime = _discover_runtime_population()
    verifiers = _discover_verifiers()
    fixtures = _fixture_markers(verifiers)
    configuration = _configuration_dependencies(runtime)
    interfaces = _interface_dependencies(runtime)
    persistence = _persistence_participants(runtime)
    obligations = _obligations(requirements, runtime, verifiers)
    exclusions = [
        {
            "artifact": rel,
            "classification": "NON_PARTICIPATING",
            "reason": "no objective Exit Decision marker and no AST dependency path from direct implementation",
        }
        for rel in _git_files()
        if rel.endswith((".py", ".json", ".md"))
        and rel not in {item["artifact"] for item in runtime}
        and rel not in {item["artifact"] for item in verifiers}
        and not _has_exit_marker(rel)
    ][:500]
    graph = {
        "nodes": [
            *({"id": item["participant_id"], "type": "runtime", "artifact": item["artifact"]} for item in runtime),
            *({"id": item["verifier_id"], "type": "verifier", "artifact": item["artifact"]} for item in verifiers),
            *({"id": item["obligation_id"], "type": "obligation", "requirement_id": item["requirement_id"]} for item in obligations),
        ],
        "edges": [
            *(
                {
                    "from": item["participant_id"],
                    "to": imported["artifact"],
                    "type": "AST_IMPORTS",
                }
                for item in runtime
                for imported in item["imports"]
            ),
            *(
                {
                    "from": obligation["obligation_id"],
                    "to": artifact,
                    "type": "REQUIRES_IMPLEMENTATION_ARTIFACT",
                }
                for obligation in obligations
                for artifact in obligation["implementation_artifacts"]
            ),
        ],
    }
    findings = []
    if baseline.get("final_constitutional_ecs003_verdict") != "UNCONDITIONAL_PASS":
        findings.append({"finding_id": "EXIT-RM002-B01-FIND-001", "severity": "BLOCKING", "classification": "FROZEN_BASELINE_NOT_READY"})
    if not any(item["artifact"] == DIRECT_IMPLEMENTATION for item in runtime):
        findings.append({"finding_id": "EXIT-RM002-B01-FIND-002", "severity": "BLOCKING", "classification": "DIRECT_IMPLEMENTATION_NOT_DISCOVERED"})
    if not verifiers:
        findings.append({"finding_id": "EXIT-RM002-B01-FIND-003", "severity": "BLOCKING", "classification": "NO_VERIFIER_POPULATION"})
    completion_checks = {
        "frozen_rm001_baseline_ready": baseline.get("final_constitutional_ecs003_verdict") == "UNCONDITIONAL_PASS",
        "implementation_inventory_present": bool(runtime),
        "direct_implementation_discovered": any(item["artifact"] == DIRECT_IMPLEMENTATION for item in runtime),
        "runtime_participants_present": bool(runtime),
        "persistence_participants_present": bool(persistence),
        "verifier_population_present": bool(verifiers),
        "fixture_population_present": bool(fixtures),
        "configuration_dependencies_present": bool(configuration),
        "interface_dependencies_present": bool(interfaces),
        "implementation_obligations_mapped": len(obligations) == len(requirements),
        "no_behavioral_execution": True,
        "conditional_remediation_not_activated": True,
    }
    artifacts: dict[str, Any] = {
        "frozen_constitutional_baseline_registry.json": {
            "source": _relative(FROZEN_BASELINE),
            "sha256": _file_digest(FROZEN_BASELINE),
            "verdict": baseline.get("final_constitutional_ecs003_verdict"),
            "ready_for": baseline.get("ready_for"),
        },
        "implementation_inventory.json": runtime,
        "runtime_participant_registry.json": runtime,
        "persistence_participant_registry.json": persistence,
        "verifier_population_registry.json": verifiers,
        "fixture_population_registry.json": fixtures,
        "configuration_dependency_registry.json": configuration,
        "interface_dependency_registry.json": interfaces,
        "implementation_obligation_registry.json": obligations,
        "requirement_to_implementation_obligation_matrix.json": obligations,
        "dependency_graph.json": graph,
        "exclusion_registry.json": exclusions,
        "discovery_finding_registry.json": findings,
        "conditional_program_registry.json": {
            "B06": "CONDITIONAL_ONLY_NOT_ACTIVATED",
            "B07": "CONDITIONAL_ONLY_NOT_ACTIVATED",
            "B08": "CONDITIONAL_ONLY_NOT_ACTIVATED",
            "B09": "CONDITIONAL_ONLY_NOT_ACTIVATED",
        },
    }
    for name, payload in artifacts.items():
        _write_json(OUTPUT_DIR / name, payload)
    completion_report = {
        "package": "EXIT-DECISION-RM-002-B01",
        "status": "COMPLETE" if all(completion_checks.values()) and not findings else "INCOMPLETE",
        "objective": "Dependency-Derived Implementation Discovery",
        "candidate_digest": _candidate_digest(),
        "frozen_constitutional_baseline": "EXIT-DECISION-RM-001-B05",
        "behavioral_verification_executed": False,
        "implementation_modified": False,
        "constitutional_doctrine_modified": False,
        "manual_inventory_authoritative": False,
        "conditional_remediation_orders_created": False,
        "completion_checks": completion_checks,
        "runtime_participant_count": len(runtime),
        "verifier_count": len(verifiers),
        "fixture_count": len(fixtures),
        "obligation_count": len(obligations),
        "ready_for": "EXIT-DECISION-RM-002-B02" if all(completion_checks.values()) and not findings else "REMEDIATION_REQUIRED_BEFORE_B02",
        "evidence_digest": _digest(artifacts),
    }
    _write_json(OUTPUT_DIR / "completion_report.json", completion_report)
    _write_text(
        OUTPUT_DIR / "README.md",
        "# EXIT-DECISION-RM-002-B01 Dependency-Derived Implementation Discovery\n\nPrimary entry point: completion_report.json\n",
    )
    return 0 if completion_report["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
