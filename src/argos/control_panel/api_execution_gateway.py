"""API Execution Gateway for ARGOS OE-011A."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
import time
from typing import Any, Callable
from urllib import error, request as urllib_request

from argos.foundation.contracts import utc_timestamp

from .cognitive_contract import (
    PromptContractLibrary,
    prompt_contract_trace,
    validate_office_response_schema,
    validate_prompt_contract_envelope,
)


@dataclass(frozen=True)
class ApiExecutionRequest:
    """Single audited AI/model execution request."""

    workflow_id: str
    workflow_token_id: str
    requesting_office: str
    workflow_stage: str
    task_type: str
    model: str
    prompt_template_id: str
    prompt_payload: dict[str, Any]
    expected_output_schema: tuple[str, ...]
    max_runtime_seconds: int
    max_cost_usd: float
    max_input_tokens: int
    max_output_tokens: int
    audit_identifier: str
    dry_run: bool = True
    execution_mode: str = "dry_run"
    provider: str = "none"
    decision_object_id: str = ""
    allow_fallback_to_dry_run: bool = True
    prompt_contract_envelope: dict[str, Any] | None = None


@dataclass(frozen=True)
class ApiExecutionResponse:
    """Gateway response returned for allowed or blocked execution."""

    allowed: bool
    blocked: bool
    violation_code: str
    violation_reason: str
    workflow_id: str
    workflow_token_id: str
    requesting_office: str
    model: str
    estimated_cost_usd: float
    actual_cost_usd: float
    input_tokens: int
    output_tokens: int
    latency_ms: int
    structured_output: dict[str, Any]
    audit_identifier: str
    execution_status: str
    execution_mode: str = "dry_run"
    provider: str = "none"
    workflow_stage: str = ""
    decision_object_id: str = ""
    validation_status: str = "VALID"
    fallback_used: bool = False


@dataclass(frozen=True)
class ApiExecutionAuditRecord:
    """Immutable gateway audit record."""

    timestamp: str
    workflow_id: str
    workflow_token_id: str
    requesting_office: str
    workflow_stage: str
    task_type: str
    model: str
    provider: str
    execution_mode: str
    dry_run: bool
    allowed: bool
    blocked: bool
    violation_code: str
    violation_reason: str
    estimated_cost_usd: float
    actual_cost_usd: float
    input_tokens: int
    output_tokens: int
    latency_ms: int
    validation_status: str
    fallback_used: bool
    decision_object_id: str
    audit_identifier: str


@dataclass(frozen=True)
class RealApiPilotConfig:
    """Safe opt-in configuration for OE-011E real API pilot."""

    enabled: bool = False
    provider: str = "openai"
    model: str = "gpt-4.1-mini"
    max_cost_per_workflow_usd: float = 0.001
    max_cost_per_session_usd: float = 0.01
    max_input_tokens: int = 2000
    max_output_tokens: int = 600
    timeout_seconds: int = 20
    fallback_to_dry_run: bool = True


class ApiExecutionGateway:
    """Single controlled boundary for future AI/model/API execution."""

    def __init__(
        self,
        *,
        workflow_snapshot: Callable[[], dict[str, Any]],
        authorize_credit: Callable[[ApiExecutionRequest], dict[str, Any]],
        complete_credit_activation: Callable[[str], dict[str, Any]],
        real_api_config: RealApiPilotConfig | None = None,
        provider_call: Callable[[ApiExecutionRequest, dict[str, Any]], str] | None = None,
        prompt_contract_library: PromptContractLibrary | None = None,
    ) -> None:
        self._workflow_snapshot = workflow_snapshot
        self._authorize_credit = authorize_credit
        self._complete_credit_activation = complete_credit_activation
        self._real_api_config = real_api_config or RealApiPilotConfig()
        self._provider_call = provider_call
        self._prompt_contract_library = prompt_contract_library or PromptContractLibrary()
        self._audit_log: list[ApiExecutionAuditRecord] = []
        self._active_stage_reasoning: set[tuple[str, str]] = set()
        self._real_api_session_spend_usd = 0.0

    def execute_model_request(self, request: ApiExecutionRequest) -> ApiExecutionResponse:
        """Validate, execute or dry-run, account, and audit one model request."""
        started = time.perf_counter()
        validation_code, validation_reason = self._validate_request(request)
        if validation_code:
            response = self._fallback_or_blocked_response(request, validation_code, validation_reason, started)
            self._record_audit(request, response)
            return response

        stage_key = (request.workflow_id, request.workflow_stage)
        self._active_stage_reasoning.add(stage_key)
        try:
            input_tokens = _deterministic_input_tokens(request)
            output_tokens = _deterministic_output_tokens(request)
            estimated_cost = round(max(0.0, float(request.max_cost_usd)), 4)
            actual_cost = estimated_cost
            activation_state = self._authorize_credit(request)
            activation = activation_state["creditGovernor"]["activations"][0] if activation_state["creditGovernor"]["activations"] else {}
            if activation.get("status") != "APPROVED":
                code = activation.get("law_vii_validation") or "LAW_VII_VIOLATION_BUDGET_EXCEEDED"
                reason = activation.get("reason") or "Credit Governor rejected gateway request."
                response = self._fallback_or_blocked_response(request, code, reason, started)
                self._record_audit(request, response)
                return response
            structured_output = _structured_output(request)
            validation_status = "VALID"
            fallback_used = False
            execution_status = "DRY_RUN_COMPLETED"
            if request.execution_mode == "real_api_pilot":
                provider_result = self._execute_real_api_pilot(request, started)
                if provider_result["blocked"]:
                    if self._real_api_config.fallback_to_dry_run and request.allow_fallback_to_dry_run:
                        structured_output = _structured_output(_fallback_request(request))
                        validation_status = provider_result["validation_status"]
                        fallback_used = True
                        execution_status = "FALLBACK_DRY_RUN_COMPLETED"
                    else:
                        response = self._blocked_response(request, provider_result["code"], provider_result["reason"], started, validation_status=provider_result["validation_status"])
                        self._record_audit(request, response)
                        return response
                else:
                    structured_output = provider_result["structured_output"]
                    input_tokens = provider_result["input_tokens"]
                    output_tokens = provider_result["output_tokens"]
                    validation_status = "VALID"
                    execution_status = "REAL_API_PILOT_COMPLETED"
                    self._real_api_session_spend_usd = round(self._real_api_session_spend_usd + actual_cost, 4)
            if activation.get("activation_id"):
                self._complete_credit_activation(str(activation["activation_id"]))
            response = ApiExecutionResponse(
                allowed=True,
                blocked=False,
                violation_code="",
                violation_reason="",
                workflow_id=request.workflow_id,
                workflow_token_id=request.workflow_token_id,
                requesting_office=request.requesting_office,
                model=request.model,
                estimated_cost_usd=estimated_cost,
                actual_cost_usd=actual_cost,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=_latency_ms(started),
                structured_output=structured_output,
                audit_identifier=request.audit_identifier,
                execution_status=execution_status,
                execution_mode=request.execution_mode,
                provider=request.provider,
                workflow_stage=request.workflow_stage,
                decision_object_id=request.decision_object_id,
                validation_status=validation_status,
                fallback_used=fallback_used,
            )
            self._record_audit(request, response)
            return response
        finally:
            self._active_stage_reasoning.discard(stage_key)

    def snapshot(self) -> dict[str, Any]:
        """Return gateway visibility state."""
        return {
            "gatewayName": "API Execution Gateway",
            "dryRunDefault": True,
            "directProviderCallsEnabled": self._real_api_config.enabled,
            "realApiPilot": asdict(self._real_api_config),
            "realApiSessionSpendUsd": round(self._real_api_session_spend_usd, 4),
            "realApiSessionBudgetRemainingUsd": round(max(0.0, self._real_api_config.max_cost_per_session_usd - self._real_api_session_spend_usd), 4),
            "promptContract": self._prompt_contract_library.snapshot(),
            "events": tuple(asdict(item) for item in reversed(self._audit_log[-50:])),
            "metrics": {
                "requestCount": len(self._audit_log),
                "allowedCount": sum(1 for item in self._audit_log if item.allowed),
                "blockedCount": sum(1 for item in self._audit_log if item.blocked),
                "dryRunCount": sum(1 for item in self._audit_log if item.execution_mode == "dry_run"),
                "realApiPilotCount": sum(1 for item in self._audit_log if item.execution_mode == "real_api_pilot" and item.allowed and not item.fallback_used),
                "fallbackCount": sum(1 for item in self._audit_log if item.fallback_used),
                "actualCostUsd": round(sum(item.actual_cost_usd for item in self._audit_log), 4),
            },
        }

    def _validate_request(self, request: ApiExecutionRequest) -> tuple[str, str]:
        if not request.workflow_id or not request.workflow_token_id or not request.requesting_office:
            return "LAW_VII_VIOLATION_UNSCOPED_API_REQUEST", "Gateway request requires workflow_id, workflow_token_id, and requesting_office."
        prompt_code, prompt_reason = validate_prompt_contract_envelope(request, self._prompt_contract_library)
        if prompt_code:
            return prompt_code, prompt_reason
        snapshot = self._workflow_snapshot()
        workflow = next((item for item in snapshot.get("workflows", ()) if item["workflow_id"] == request.workflow_id), None)
        if workflow is None:
            return "LAW_VII_VIOLATION_UNKNOWN_WORKFLOW", f"Workflow {request.workflow_id} does not exist."
        token = workflow["token"]
        if token["audit_identifier"] != request.workflow_token_id:
            return "LAW_VII_VIOLATION_UNKNOWN_TOKEN", "Workflow token id does not match the workflow token."
        if token["workflow_status"] != "Executing":
            return "LAW_VII_VIOLATION_WORKFLOW_NOT_EXECUTING", f"Workflow {request.workflow_id} is {token['workflow_status']}, not Executing."
        if token["current_owner"] != request.requesting_office:
            return "LAW_VII_VIOLATION_NON_OWNER_API_REQUEST", f"{request.requesting_office} is not current token owner {token['current_owner']}."
        active_owners = tuple(owner for owner, state in workflow["office_states"].items() if state in {"Assigned", "Executing"})
        if active_owners != (request.requesting_office,):
            return "LAW_VII_VIOLATION_NON_OWNER_API_REQUEST", "Workflow does not show exactly one active owner matching the request."
        if (request.workflow_id, request.workflow_stage) in self._active_stage_reasoning:
            return "LAW_VII_VIOLATION_CONCURRENT_STAGE_REASONING", "Concurrent model execution is already active for this workflow stage."
        if workflow["runtime_used"] >= token["runtime_budget"]:
            return "LAW_VII_VIOLATION_BUDGET_EXCEEDED", "Workflow runtime budget has been exhausted."
        if workflow["credits_used"] + max(0.0, float(request.max_cost_usd)) > token["credit_budget"]:
            return "LAW_VII_VIOLATION_BUDGET_EXCEEDED", "Workflow credit budget would be exceeded."
        if request.execution_mode == "real_api_pilot":
            return self._validate_real_api_pilot(request, workflow)
        if request.model != "dry-run-model":
            return "MODEL_POLICY_VIOLATION", "Only dry-run-model is permitted before real provider integration."
        if not request.audit_identifier:
            return "AUDIT_SCOPE_REQUIRED", "Gateway request requires an audit identifier."
        return "", ""

    def _validate_real_api_pilot(self, request: ApiExecutionRequest, workflow: dict[str, Any]) -> tuple[str, str]:
        if not self._real_api_config.enabled:
            return "REAL_API_PILOT_DISABLED", "Real API pilot is disabled by configuration."
        if workflow["workflow_type"] != "paper_trading_session":
            return "REAL_API_PILOT_SCOPE_VIOLATION", "Real API pilot is limited to paper_trading_session workflows."
        if request.requesting_office != "Analyst" or request.workflow_stage != "Analyst":
            return "REAL_API_PILOT_SCOPE_VIOLATION", "Real API pilot is limited to Analyst stage and Analyst office."
        if request.provider != self._real_api_config.provider:
            return "REAL_API_PILOT_PROVIDER_VIOLATION", "Request provider does not match configured provider."
        if request.model != self._real_api_config.model:
            return "REAL_API_PILOT_MODEL_VIOLATION", "Request model does not match configured model."
        if request.max_cost_usd > self._real_api_config.max_cost_per_workflow_usd:
            return "REAL_API_PILOT_BUDGET_BLOCKED", "Request exceeds per-workflow real API budget."
        if self._real_api_session_spend_usd + max(0.0, float(request.max_cost_usd)) > self._real_api_config.max_cost_per_session_usd:
            return "REAL_API_PILOT_BUDGET_BLOCKED", "Request exceeds real API session budget."
        if request.max_input_tokens > self._real_api_config.max_input_tokens or request.max_output_tokens > self._real_api_config.max_output_tokens:
            return "REAL_API_PILOT_BUDGET_BLOCKED", "Request exceeds real API token limits."
        if not request.audit_identifier:
            return "AUDIT_SCOPE_REQUIRED", "Gateway request requires an audit identifier."
        return "", ""

    def _fallback_or_blocked_response(self, request: ApiExecutionRequest, code: str, reason: str, started: float) -> ApiExecutionResponse:
        if request.execution_mode == "real_api_pilot" and self._real_api_config.fallback_to_dry_run and request.allow_fallback_to_dry_run and code.startswith("REAL_API_PILOT"):
            fallback_request = _fallback_request(request)
            response = ApiExecutionResponse(
                allowed=True,
                blocked=False,
                violation_code=code,
                violation_reason=reason,
                workflow_id=request.workflow_id,
                workflow_token_id=request.workflow_token_id,
                requesting_office=request.requesting_office,
                model=fallback_request.model,
                estimated_cost_usd=round(max(0.0, float(fallback_request.max_cost_usd)), 4),
                actual_cost_usd=round(max(0.0, float(fallback_request.max_cost_usd)), 4),
                input_tokens=_deterministic_input_tokens(fallback_request),
                output_tokens=_deterministic_output_tokens(fallback_request),
                latency_ms=_latency_ms(started),
                structured_output=_structured_output(fallback_request),
                audit_identifier=request.audit_identifier,
                execution_status="FALLBACK_DRY_RUN_COMPLETED",
                execution_mode="real_api_pilot",
                provider=request.provider,
                workflow_stage=request.workflow_stage,
                decision_object_id=request.decision_object_id,
                validation_status=code,
                fallback_used=True,
            )
            return response
        return self._blocked_response(request, code, reason, started, validation_status=code)

    def _blocked_response(self, request: ApiExecutionRequest, code: str, reason: str, started: float, *, validation_status: str = "BLOCKED") -> ApiExecutionResponse:
        return ApiExecutionResponse(
            allowed=False,
            blocked=True,
            violation_code=code,
            violation_reason=reason,
            workflow_id=request.workflow_id,
            workflow_token_id=request.workflow_token_id,
            requesting_office=request.requesting_office,
            model=request.model,
            estimated_cost_usd=round(max(0.0, float(request.max_cost_usd)), 4),
            actual_cost_usd=0.0,
            input_tokens=0,
            output_tokens=0,
            latency_ms=_latency_ms(started),
            structured_output={},
            audit_identifier=request.audit_identifier,
            execution_status="BLOCKED",
            execution_mode=request.execution_mode,
            provider=request.provider,
            workflow_stage=request.workflow_stage,
            decision_object_id=request.decision_object_id,
            validation_status=validation_status,
            fallback_used=False,
        )

    def _execute_real_api_pilot(self, request: ApiExecutionRequest, started: float) -> dict[str, Any]:
        prompt = _real_api_prompt(request)
        try:
            raw = self._provider_call(request, prompt) if self._provider_call else _call_openai_provider(request, prompt, self._real_api_config)
        except Exception as exc:  # noqa: BLE001
            return {"blocked": True, "code": "REAL_API_PILOT_PROVIDER_ERROR", "reason": str(exc), "validation_status": "PROVIDER_ERROR"}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"blocked": True, "code": "REAL_API_PILOT_MALFORMED_JSON", "reason": "Provider returned malformed JSON.", "validation_status": "MALFORMED_JSON"}
        schema_code, schema_reason = validate_office_response_schema(request.requesting_office, parsed)
        if schema_code:
            return {"blocked": True, "code": "REAL_API_PILOT_SCHEMA_INVALID", "reason": schema_reason, "validation_status": "SCHEMA_INVALID"}
        structured = _structured_output(request)
        structured["summary"] = str(parsed["summary"])
        structured["evidence"] = tuple(str(item) for item in parsed["evidence"])
        structured["analyst_contract"] = parsed
        structured["api_execution_gateway"] = {
            "model": request.model,
            "provider": request.provider,
            "execution_mode": "real_api_pilot",
            "dry_run": False,
            "task_type": request.task_type,
            "validation_status": "VALID",
            "fallback_used": False,
        }
        structured["prompt_contract"] = prompt_contract_trace(request.prompt_contract_envelope or {}, {"validation_status": "VALID"})
        return {
            "blocked": False,
            "structured_output": structured,
            "input_tokens": _deterministic_input_tokens(request),
            "output_tokens": _deterministic_output_tokens(request),
            "latency_ms": _latency_ms(started),
        }

    def _record_audit(self, request: ApiExecutionRequest, response: ApiExecutionResponse) -> None:
        self._audit_log.append(
            ApiExecutionAuditRecord(
                timestamp=utc_timestamp(),
                workflow_id=request.workflow_id,
                workflow_token_id=request.workflow_token_id,
                requesting_office=request.requesting_office,
                workflow_stage=request.workflow_stage,
                task_type=request.task_type,
                model=request.model,
                provider=request.provider,
                execution_mode=request.execution_mode,
                dry_run=request.dry_run,
                allowed=response.allowed,
                blocked=response.blocked,
                violation_code=response.violation_code,
                violation_reason=response.violation_reason,
                estimated_cost_usd=response.estimated_cost_usd,
                actual_cost_usd=response.actual_cost_usd,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                latency_ms=response.latency_ms,
                validation_status=response.validation_status,
                fallback_used=response.fallback_used,
                decision_object_id=response.decision_object_id,
                audit_identifier=response.audit_identifier,
            )
        )

    def set_provider_call_for_testing(self, provider_call: Callable[[ApiExecutionRequest, dict[str, Any]], str] | None) -> None:
        """Install a deterministic provider stub for tests."""
        self._provider_call = provider_call


def _deterministic_input_tokens(request: ApiExecutionRequest) -> int:
    payload_size = len(json.dumps(request.prompt_payload, sort_keys=True, separators=(",", ":")))
    return min(max(1, int(request.max_input_tokens)), max(1, payload_size // 4 + 12))


def _deterministic_output_tokens(request: ApiExecutionRequest) -> int:
    return min(max(1, int(request.max_output_tokens)), max(1, len(request.expected_output_schema) * 16))


def _structured_output(request: ApiExecutionRequest) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for field in request.expected_output_schema:
        if field == "summary":
            output[field] = f"{request.requesting_office} dry-run gateway analysis completed."
        elif field == "evidence":
            output[field] = f"{request.workflow_id}:{request.requesting_office}:api-gateway-dry-run"
        elif field == "audit_identifier":
            output[field] = request.audit_identifier
        elif field == "workflow_type":
            output[field] = "paper_trading_session"
        elif field == "workflow_stage":
            output[field] = request.workflow_stage
        elif field == "initial_stage":
            output[field] = "market_preparation"
        else:
            output[field] = f"dry_run_{field}"
    output["api_execution_gateway"] = {
        "model": request.model,
        "provider": request.provider,
        "execution_mode": request.execution_mode,
        "dry_run": request.dry_run,
        "task_type": request.task_type,
        "validation_status": "VALID",
        "fallback_used": False,
    }
    output["prompt_contract"] = prompt_contract_trace(request.prompt_contract_envelope or {}, {"validation_status": "VALID"})
    return output


def _fallback_request(request: ApiExecutionRequest) -> ApiExecutionRequest:
    return ApiExecutionRequest(
        workflow_id=request.workflow_id,
        workflow_token_id=request.workflow_token_id,
        requesting_office=request.requesting_office,
        workflow_stage=request.workflow_stage,
        task_type=request.task_type,
        model="dry-run-model",
        prompt_template_id=request.prompt_template_id,
        prompt_payload=request.prompt_payload,
        expected_output_schema=request.expected_output_schema,
        max_runtime_seconds=request.max_runtime_seconds,
        max_cost_usd=min(0.001, max(0.0, float(request.max_cost_usd))),
        max_input_tokens=min(128, max(1, int(request.max_input_tokens))),
        max_output_tokens=min(128, max(1, int(request.max_output_tokens))),
        audit_identifier=request.audit_identifier,
        dry_run=True,
        execution_mode="dry_run",
        provider="none",
        decision_object_id=request.decision_object_id,
        allow_fallback_to_dry_run=True,
        prompt_contract_envelope=request.prompt_contract_envelope,
    )


def _real_api_prompt(request: ApiExecutionRequest) -> dict[str, Any]:
    return {
        "system": (
            "You are ARGOS Analyst in a controlled paper_trading_session pilot. "
            "Return JSON only. Do not include markdown. Do not recommend live trading."
        ),
        "user": request.prompt_contract_envelope or {},
    }


def _analyst_contract_fields() -> tuple[str, ...]:
    return (
        "recommendation",
        "confidence",
        "summary",
        "evidence",
        "supporting_signals",
        "risk_flags",
        "expected_return",
        "position_size_recommendation",
        "target_price",
        "stop_loss",
        "reasoning_audit",
    )


def _call_openai_provider(request: ApiExecutionRequest, prompt: dict[str, Any], config: RealApiPilotConfig) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("missing OPENAI_API_KEY")
    payload = {
        "model": request.model,
        "messages": [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": json.dumps(prompt["user"], sort_keys=True)},
        ],
        "temperature": 0,
        "max_tokens": min(request.max_output_tokens, config.max_output_tokens),
        "response_format": {"type": "json_object"},
    }
    req = urllib_request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=config.timeout_seconds) as response:  # noqa: S310
            decoded = json.loads(response.read().decode("utf-8"))
    except error.URLError as exc:
        raise RuntimeError(f"provider network error: {exc}") from exc
    return decoded["choices"][0]["message"]["content"]


def real_api_config_from_env() -> RealApiPilotConfig:
    """Load safe real API pilot config from environment."""
    return RealApiPilotConfig(
        enabled=_env_bool("ARGOS_ENABLE_REAL_API_PILOT", False),
        provider=os.environ.get("ARGOS_REAL_API_PROVIDER", "openai"),
        model=os.environ.get("ARGOS_REAL_API_MODEL", "gpt-4.1-mini"),
        max_cost_per_workflow_usd=float(os.environ.get("ARGOS_REAL_API_MAX_COST_PER_WORKFLOW_USD", "0.001")),
        max_cost_per_session_usd=float(os.environ.get("ARGOS_REAL_API_MAX_COST_PER_SESSION_USD", "0.01")),
        max_input_tokens=int(os.environ.get("ARGOS_REAL_API_MAX_INPUT_TOKENS", "2000")),
        max_output_tokens=int(os.environ.get("ARGOS_REAL_API_MAX_OUTPUT_TOKENS", "600")),
        timeout_seconds=int(os.environ.get("ARGOS_REAL_API_TIMEOUT_SECONDS", "20")),
        fallback_to_dry_run=_env_bool("ARGOS_REAL_API_FALLBACK_TO_DRY_RUN", True),
    )


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _latency_ms(started: float) -> int:
    return max(1, int((time.perf_counter() - started) * 1000))
