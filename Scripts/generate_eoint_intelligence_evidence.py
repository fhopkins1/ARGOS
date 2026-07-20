from pathlib import Path
from dataclasses import fields, is_dataclass
from enum import Enum
import json
import sys
from types import MappingProxyType


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.intelligence import (  # noqa: E402
    CollectionRequest,
    UNKNOWN,
    RetrievalEvidence,
    TriggerClass,
    TruthDomain,
    build_audit_record,
    build_constitutional_charter,
    build_provenance_record,
    create_observation,
    default_authority_registry,
    evaluate_integrity,
    export_audit_package,
    normalize_observation,
    route_fact,
)


def to_jsonable(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingProxyType):
        return {key: to_jsonable(item) for key, item in value.items()}
    if is_dataclass(value):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    return value


def build_external_audit(input_path: Path) -> dict:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    request = CollectionRequest(
        request_id=payload["request_id"],
        truth_domain=TruthDomain(payload["truth_domain"]),
        trigger=TriggerClass(payload["trigger"]),
        workflow_id=payload["workflow_id"],
        source_id=payload.get("source_id"),
    )
    retrieval = RetrievalEvidence(**payload["retrieval"])
    registry = default_authority_registry()
    observation = create_observation(request, retrieval, registry)
    if not hasattr(observation, "metadata"):
        return {"accepted": False, "failure": observation}
    provenance = build_provenance_record(observation, retrieval, registry)
    fact = normalize_observation(observation, provenance)
    integrity_state, integrity_evidence, quarantine = evaluate_integrity(observation, provenance)
    routing = route_fact(fact, integrity_state, provenance)
    audit = build_audit_record(observation, provenance, fact, routing, integrity_state, retrieval, registry)
    return {
        "accepted": True,
        "observation_id": observation.metadata.observation_id,
        "provenance_id": provenance.provenance_id,
        "fact_id": fact.fact_id,
        "integrity_state": integrity_state.value,
        "integrity_evidence": integrity_evidence,
        "quarantine": quarantine,
        "routing_id": routing.routing_record_id,
        "audit_id": audit.audit_record_id,
        "audit_export": export_audit_package((audit,)),
    }


def main() -> int:
    evidence_dir = REPOSITORY_ROOT / "Documentation" / "EOINT_Evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    registry = default_authority_registry()
    output = {
        "charter": build_constitutional_charter(),
        "registry_id": registry.registry_id,
        "registry_version": registry.version,
        "primary_authorities": {domain.value: registry.resolve(domain).source_id for domain in TruthDomain},
        "accepted_observation": UNKNOWN,
        "accepted_observation_reason": "No accepted observation is generated unless an external retrieval JSON path is supplied.",
    }
    if len(sys.argv) > 1:
        output["accepted_observation"] = build_external_audit(Path(sys.argv[1]).resolve())
    target = evidence_dir / "eoint_001_009_intelligence_evidence.json"
    target.write_text(json.dumps(to_jsonable(output), indent=2, sort_keys=True), encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
