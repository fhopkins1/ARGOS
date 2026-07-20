"""INF-002 Infrastructure truth and execution doctrine controls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from typing import Mapping


INF_002_VERSION = "INF-002/1.0.0"


class ExecutionTruthFailure(str, Enum):
    PLACEHOLDER_IDENTIFIER = "placeholder_identifier"
    INFERRED_IDENTITY = "inferred_identity"
    MUTABLE_IDENTITY = "mutable_identity"
    NON_REPRODUCIBLE_BUILD = "non_reproducible_build"
    NON_DETERMINISTIC_RUNTIME = "non_deterministic_runtime"
    MISSING_CHAIN_LINK = "missing_chain_link"
    MISSING_EVIDENCE = "missing_evidence"
    MISSING_PROOF = "missing_proof"
    SYNTHETIC_TRUTH = "synthetic_truth"


class ExecutionTruthStatus(str, Enum):
    CONSTITUTIONALLY_VALID = "CONSTITUTIONALLY_VALID"
    INVALID_FAIL_CLOSED = "INVALID_FAIL_CLOSED"


@dataclass(frozen=True)
class RepositoryIdentity:
    repository_id: str
    origin: str
    canonical_branch: str
    commit_hash: str
    lineage: tuple[str, ...]
    certification_history: tuple[str, ...]


@dataclass(frozen=True)
class CandidateIdentity:
    candidate_id: str
    repository_id: str
    commit_hash: str
    branch: str
    build_id: str
    runtime_id: str
    creation_timestamp: str
    certification_cycle: str
    certification_authority: str
    certification_status: str
    inferred: bool = False
    regenerated: bool = False


@dataclass(frozen=True)
class BuildIdentity:
    build_id: str
    compiler_version: str
    dependency_versions: Mapping[str, str]
    package_manifest_hash: str
    lock_file_hashes: tuple[str, ...]
    environment_configuration_hash: str
    build_parameters_hash: str
    build_timestamp: str
    build_host: str
    artifact_checksum: str
    reproducible: bool


@dataclass(frozen=True)
class RuntimeIdentity:
    runtime_id: str
    candidate_id: str
    build_id: str
    runtime_configuration_hash: str
    startup_timestamp: str
    runtime_version: str
    infrastructure_version: str
    configuration_hash: str
    operating_environment: str
    execution_mode: str
    deterministic: bool


@dataclass(frozen=True)
class ExecutionIdentity:
    execution_id: str
    runtime_id: str
    workflow_id: str
    candidate_id: str
    repository_id: str
    build_id: str
    execution_token_id: str
    certification_context_id: str
    reused: bool = False


@dataclass(frozen=True)
class ExecutionChain:
    repository: RepositoryIdentity
    candidate: CandidateIdentity
    build: BuildIdentity
    runtime: RuntimeIdentity
    bridge_certification_id: str
    execution_token_id: str
    workflow_id: str
    infrastructure_evidence_id: str
    infrastructure_proof_id: str
    certification_id: str


@dataclass(frozen=True)
class ExecutionTruthCertification:
    status: ExecutionTruthStatus
    failures: tuple[ExecutionTruthFailure, ...]
    evidence_digest: str
    chain_digest: str


class InfrastructureTruthExecutionValidator:
    """Validates immutable identity and execution-chain truth before execution."""

    _placeholder_values = {"", "placeholder", "unknown", "tbd", "none", "null", "synthetic"}

    def certify(self, chain: ExecutionChain, execution: ExecutionIdentity) -> ExecutionTruthCertification:
        failures: list[ExecutionTruthFailure] = []
        required_values = (
            chain.repository.repository_id,
            chain.repository.origin,
            chain.repository.canonical_branch,
            chain.repository.commit_hash,
            chain.candidate.candidate_id,
            chain.candidate.build_id,
            chain.candidate.runtime_id,
            chain.build.build_id,
            chain.runtime.runtime_id,
            chain.bridge_certification_id,
            chain.execution_token_id,
            chain.workflow_id,
            chain.infrastructure_evidence_id,
            chain.infrastructure_proof_id,
            chain.certification_id,
            execution.execution_id,
            execution.certification_context_id,
        )
        if any(_is_placeholder(value) for value in required_values):
            failures.append(ExecutionTruthFailure.PLACEHOLDER_IDENTIFIER)
        if chain.candidate.inferred:
            failures.append(ExecutionTruthFailure.INFERRED_IDENTITY)
        if chain.candidate.regenerated or execution.reused:
            failures.append(ExecutionTruthFailure.MUTABLE_IDENTITY)
        if not chain.build.reproducible:
            failures.append(ExecutionTruthFailure.NON_REPRODUCIBLE_BUILD)
        if not chain.runtime.deterministic:
            failures.append(ExecutionTruthFailure.NON_DETERMINISTIC_RUNTIME)
        if not _chain_is_consistent(chain, execution):
            failures.append(ExecutionTruthFailure.MISSING_CHAIN_LINK)
        if _is_placeholder(chain.infrastructure_evidence_id):
            failures.append(ExecutionTruthFailure.MISSING_EVIDENCE)
        if _is_placeholder(chain.infrastructure_proof_id):
            failures.append(ExecutionTruthFailure.MISSING_PROOF)

        unique_failures = tuple(dict.fromkeys(failures))
        return ExecutionTruthCertification(
            status=ExecutionTruthStatus.CONSTITUTIONALLY_VALID if not unique_failures else ExecutionTruthStatus.INVALID_FAIL_CLOSED,
            failures=unique_failures,
            evidence_digest=_stable_digest({"evidence": chain.infrastructure_evidence_id, "proof": chain.infrastructure_proof_id}),
            chain_digest=_stable_digest({"chain": asdict(chain), "execution": asdict(execution)}),
        )


def _chain_is_consistent(chain: ExecutionChain, execution: ExecutionIdentity) -> bool:
    return all(
        (
            chain.repository.repository_id == chain.candidate.repository_id == execution.repository_id,
            chain.repository.commit_hash == chain.candidate.commit_hash,
            chain.repository.canonical_branch == chain.candidate.branch,
            chain.candidate.candidate_id == chain.runtime.candidate_id == execution.candidate_id,
            chain.build.build_id == chain.runtime.build_id == execution.build_id,
            chain.runtime.runtime_id == execution.runtime_id,
            chain.execution_token_id == execution.execution_token_id,
            chain.workflow_id == execution.workflow_id,
        )
    )


def _is_placeholder(value: str) -> bool:
    return str(value).strip().lower() in InfrastructureTruthExecutionValidator._placeholder_values


def _stable_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
