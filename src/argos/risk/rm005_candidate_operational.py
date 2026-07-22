"""Operational RISK-RM-005 candidate binding and inventory support."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from argos.control_panel.sentinel_bridge_certification_support import EnterpriseCertificationDecision


RISK_OWNER = "Risk Office"


def _jsonable(value: Any) -> Any:
    if isinstance(value, EnterpriseCertificationDecision):
        return value.value
    if is_dataclass(value):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _freeze(values: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted(values.items())))


@dataclass(frozen=True)
class RiskRm005ArtifactRecord:
    artifact_identifier: str
    relative_path: str
    artifact_class: str
    constitutional_owner: str
    byte_size: int
    content_digest: str
    candidate_digest: str


@dataclass(frozen=True)
class RiskRm005CandidateBindingRecord:
    candidate_identifier: str
    candidate_root: str
    candidate_digest: str
    artifact_count: int
    bound_artifact_digests: Mapping[str, str]
    immutable_evidence_references: tuple[str, ...]
    findings: tuple[str, ...]
    result: EnterpriseCertificationDecision
    deterministic_digest: str


@dataclass(frozen=True)
class RiskRm005CandidateOperationalPackage:
    package_identifier: str
    governing_doctrine: str
    order_coverage: tuple[str, ...]
    candidate_binding: RiskRm005CandidateBindingRecord
    discovered_artifacts: tuple[RiskRm005ArtifactRecord, ...]
    candidate_class_registry: Mapping[str, tuple[str, ...]]
    canonical_identity_registry: Mapping[str, str]
    identity_collisions: Mapping[str, tuple[str, ...]]
    constitutional_identifier_registry: Mapping[str, tuple[str, ...]]
    immutable_audit_references: tuple[str, ...]
    final_completion_readiness: EnterpriseCertificationDecision
    deterministic_digest: str


class RiskRm005CandidateOperationalSupport:
    """Build candidate-bound operational evidence for RISK-RM-005-001 through 005."""

    order_coverage = (
        "RISK-RM-005-001",
        "RISK-RM-005-002",
        "RISK-RM-005-003",
        "RISK-RM-005-004",
        "RISK-RM-005-005",
    )

    def build_operational_package(self, candidate_root: str | Path | None = None) -> RiskRm005CandidateOperationalPackage:
        root = Path(candidate_root) if candidate_root is not None else Path(__file__).resolve().parents[3]
        artifacts = self.discover_artifacts(root)
        binding = self.bind_candidate(root, artifacts)
        class_registry = self.materialize_candidate_class_registry(artifacts)
        identity_registry, collisions = self.materialize_identity_registry(artifacts)
        identifier_registry = self.materialize_identifier_registry(artifacts)
        final = EnterpriseCertificationDecision.PASS if (
            binding.result == EnterpriseCertificationDecision.PASS
            and artifacts
            and not collisions
            and all(class_registry.values())
            and all(identifier_registry.values())
        ) else EnterpriseCertificationDecision.FAIL
        package = RiskRm005CandidateOperationalPackage(
            package_identifier=f"RISK-RM-005-CANDIDATE-{binding.candidate_digest[:12].upper()}",
            governing_doctrine="RISK-RM-005-001-TO-005/1.0.0",
            order_coverage=self.order_coverage,
            candidate_binding=binding,
            discovered_artifacts=artifacts,
            candidate_class_registry=_freeze(class_registry),
            canonical_identity_registry=_freeze(identity_registry),
            identity_collisions=_freeze(collisions),
            constitutional_identifier_registry=_freeze(identifier_registry),
            immutable_audit_references=(
                binding.candidate_identifier,
                "RISK-RM-005-002-ARTIFACT-INVENTORY",
                "RISK-RM-005-003-CANDIDATE-CLASS-REGISTRY",
                "RISK-RM-005-004-CANONICAL-IDENTITY-REGISTRY",
                "RISK-RM-005-005-CONSTITUTIONAL-IDENTIFIER-REGISTRY",
            ),
            final_completion_readiness=final,
            deterministic_digest="",
        )
        return replace(package, deterministic_digest=_digest(package))

    def discover_artifacts(self, candidate_root: str | Path) -> tuple[RiskRm005ArtifactRecord, ...]:
        root = Path(candidate_root).resolve()
        discovered: list[tuple[str, Path, str, int, str]] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file() or _is_excluded(path, root):
                continue
            relative_path = path.relative_to(root).as_posix()
            artifact_class = _classify_artifact(relative_path)
            if artifact_class == "outside-risk-certification-scope":
                continue
            digest = _file_digest(path)
            discovered.append((relative_path, path, artifact_class, path.stat().st_size, digest))
        candidate_digest = _digest(tuple((relative, artifact_class, size, digest) for relative, _, artifact_class, size, digest in discovered))
        return tuple(
            RiskRm005ArtifactRecord(
                artifact_identifier=f"RISK-RM005-ARTIFACT-{hashlib.sha256(relative.encode('utf-8')).hexdigest()[:16].upper()}",
                relative_path=relative,
                artifact_class=artifact_class,
                constitutional_owner=RISK_OWNER,
                byte_size=size,
                content_digest=digest,
                candidate_digest=candidate_digest,
            )
            for relative, _, artifact_class, size, digest in discovered
        )

    def bind_candidate(
        self,
        candidate_root: str | Path,
        artifacts: tuple[RiskRm005ArtifactRecord, ...],
        *,
        findings: tuple[str, ...] = (),
    ) -> RiskRm005CandidateBindingRecord:
        root = Path(candidate_root).resolve()
        derived_findings = list(findings)
        if not root.exists():
            derived_findings.append("candidate root does not exist")
        if not artifacts:
            derived_findings.append("candidate has no discovered certifiable artifacts")
        candidate_digest = _digest(tuple((artifact.relative_path, artifact.artifact_class, artifact.content_digest) for artifact in artifacts))
        bound = {artifact.relative_path: artifact.content_digest for artifact in artifacts}
        binding = RiskRm005CandidateBindingRecord(
            candidate_identifier=f"RISK-CANDIDATE-{candidate_digest[:16].upper()}",
            candidate_root=str(root),
            candidate_digest=candidate_digest,
            artifact_count=len(artifacts),
            bound_artifact_digests=_freeze(bound),
            immutable_evidence_references=tuple(artifact.artifact_identifier for artifact in artifacts),
            findings=tuple(derived_findings),
            result=EnterpriseCertificationDecision.PASS if not derived_findings else EnterpriseCertificationDecision.FAIL,
            deterministic_digest="",
        )
        return replace(binding, deterministic_digest=_digest(binding))

    def materialize_candidate_class_registry(
        self,
        artifacts: tuple[RiskRm005ArtifactRecord, ...],
    ) -> Mapping[str, tuple[str, ...]]:
        registry: dict[str, list[str]] = {}
        for artifact in artifacts:
            registry.setdefault(artifact.artifact_class, []).append(artifact.artifact_identifier)
        return {artifact_class: tuple(sorted(identifiers)) for artifact_class, identifiers in sorted(registry.items())}

    def materialize_identity_registry(
        self,
        artifacts: tuple[RiskRm005ArtifactRecord, ...],
    ) -> tuple[Mapping[str, str], Mapping[str, tuple[str, ...]]]:
        registry: dict[str, str] = {}
        reverse: dict[str, list[str]] = {}
        for artifact in artifacts:
            canonical_identity = _canonical_identity(artifact.relative_path)
            registry[artifact.artifact_identifier] = canonical_identity
            reverse.setdefault(canonical_identity, []).append(artifact.artifact_identifier)
        collisions = {
            identity: tuple(sorted(artifact_ids))
            for identity, artifact_ids in sorted(reverse.items())
            if len(artifact_ids) > 1
        }
        return registry, collisions

    def materialize_identifier_registry(
        self,
        artifacts: tuple[RiskRm005ArtifactRecord, ...],
    ) -> Mapping[str, tuple[str, ...]]:
        namespaces: dict[str, list[str]] = {}
        for artifact in artifacts:
            namespace = _identifier_namespace(artifact.relative_path)
            namespaces.setdefault(namespace, []).append(artifact.artifact_identifier)
        return {namespace: tuple(sorted(identifiers)) for namespace, identifiers in sorted(namespaces.items())}


def _is_excluded(path: Path, root: Path) -> bool:
    relative_parts = path.relative_to(root).parts
    excluded = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv"}
    if any(part in excluded for part in relative_parts):
        return True
    if path.suffix.lower() in {".pyc", ".pyo", ".zip"}:
        return True
    return False


def _classify_artifact(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/")
    if normalized.startswith("src/argos/risk/") and normalized.endswith(".py"):
        return "risk-runtime-source"
    if normalized.startswith("Tests/test_risk_") and normalized.endswith(".py"):
        return "risk-certification-test"
    if normalized.startswith("Documentation/RISK-RM-") and normalized.endswith(".md"):
        return "risk-certification-evidence"
    if normalized.startswith("Documentation/RISK-M4_Evidence/"):
        return "risk-generated-evidence"
    return "outside-risk-certification-scope"


def _canonical_identity(relative_path: str) -> str:
    stem = Path(relative_path).with_suffix("").as_posix().lower()
    normalized = "".join(character if character.isalnum() else "-" for character in stem)
    return "-".join(part for part in normalized.split("-") if part)


def _identifier_namespace(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/")
    if normalized.startswith("src/argos/risk/"):
        return "RISK-SOURCE"
    if normalized.startswith("Tests/"):
        return "RISK-TEST"
    if normalized.startswith("Documentation/"):
        return "RISK-EVIDENCE"
    return "RISK-UNKNOWN"
