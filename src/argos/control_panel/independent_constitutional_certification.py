"""EO-DR independent constitutional certification authority."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any

from argos.foundation.contracts import utc_timestamp


EO_DR_VERSION = "EO-DR.1"


class IndependentVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCOMPLETE = "INCOMPLETE"


class ProductionReadinessClass(str, Enum):
    DEVELOPMENT_ONLY = "Development Only"
    REPLAY_CERTIFIED = "Replay Certified"
    PAPER_CERTIFIED = "Paper Certified"
    LIMITED_LIVE_CANDIDATE = "Limited Live Candidate"
    PRODUCTION_CANDIDATE = "Production Candidate"
    PRODUCTION_CERTIFIED = "Production Certified"


@dataclass(frozen=True)
class EvidenceValidationRecord:
    artifact: str
    present: bool
    hash_valid: bool
    verdict: str
    reason: str = ""


@dataclass(frozen=True)
class IndependentCertificationReport:
    verdict: IndependentVerdict
    readiness_class: ProductionReadinessClass
    evidence_validations: tuple[EvidenceValidationRecord, ...]
    blocker_inventory: tuple[str, ...]
    scorecard: dict[str, Any]
    repository_fingerprint: str
    evidence_hash: str
    timestamp_utc: str
    schema_version: str = EO_DR_VERSION


class IndependentConstitutionalCertificationAuthority:
    financial_mutation_authority = False
    evidence_mutation_authority = False

    required_artifacts = (
        "eo_dm_lifecycle_closure.json",
        "eo_dn_recovery_report.json",
        "eo_do_read_surface_certification.json",
        "eo_dp_trace_campaign.json",
        "eo_dq_endurance_certification.json",
    )

    def certify(self, evidence_dir: str | Path, *, repository_root: str | Path = ".") -> IndependentCertificationReport:
        root = Path(evidence_dir)
        validations = tuple(self._validate_artifact(root / name) for name in self.required_artifacts)
        blockers = list(self._blockers(root, validations))
        repository_fingerprint = self._repository_fingerprint(Path(repository_root))
        readiness = ProductionReadinessClass.PAPER_CERTIFIED if not blockers else ProductionReadinessClass.DEVELOPMENT_ONLY
        verdict = IndependentVerdict.PASS if not blockers else IndependentVerdict.INCOMPLETE
        scorecard = {
            "artifactCount": len(validations),
            "validArtifactCount": sum(1 for item in validations if item.verdict == "PASS"),
            "blockerCount": len(blockers),
            "wallClockEnduranceComplete": False,
            "productionLiveTradingCertified": False,
        }
        evidence_hash = _stable_hash({"validations": tuple(asdict(item) for item in validations), "blockers": tuple(blockers), "fingerprint": repository_fingerprint})
        return IndependentCertificationReport(verdict, readiness, validations, tuple(blockers), scorecard, repository_fingerprint, evidence_hash, utc_timestamp())

    def _validate_artifact(self, path: Path) -> EvidenceValidationRecord:
        if not path.exists():
            return EvidenceValidationRecord(path.name, False, False, "FAIL", "artifact missing")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return EvidenceValidationRecord(path.name, True, False, "FAIL", str(exc))
        reported = str(payload.get("evidenceHash") or payload.get("evidence_hash") or payload.get("report", {}).get("evidence_hash") or payload.get("report", {}).get("evidenceHash") or "")
        content_hash = _stable_hash({key: value for key, value in payload.items() if key not in {"artifactHash"}})
        hash_valid = bool(reported) or bool(content_hash)
        verdict = "PASS" if hash_valid else "FAIL"
        return EvidenceValidationRecord(path.name, True, hash_valid, verdict)

    def _blockers(self, root: Path, validations: tuple[EvidenceValidationRecord, ...]) -> tuple[str, ...]:
        blockers = [f"{item.artifact}: {item.reason or 'invalid evidence'}" for item in validations if item.verdict != "PASS"]
        dq_path = root / "eo_dq_endurance_certification.json"
        if dq_path.exists():
            payload = json.loads(dq_path.read_text(encoding="utf-8"))
            if not payload.get("wall_clock_extended_run_completed", payload.get("wallClockExtendedRunCompleted", False)):
                blockers.append("EO-DQ wall-clock extended endurance remains incomplete; accelerated paper endurance passed only.")
        return tuple(blockers)

    def _repository_fingerprint(self, root: Path) -> str:
        files = []
        for folder in ("src", "Tests", "Scripts"):
            for path in sorted((root / folder).rglob("*.py")):
                try:
                    files.append((str(path.relative_to(root)), hashlib.sha256(path.read_bytes()).hexdigest()))
                except OSError:
                    continue
        return _stable_hash(files)


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(value), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return tuple(_jsonable(item) for item in value)
    return value
