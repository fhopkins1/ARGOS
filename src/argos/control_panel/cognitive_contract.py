"""Prompt and Cognitive Contract Framework for ARGOS OE-011F."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


PROMPT_CONTRACT_VERSION = "OE-011F-1.0.0"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 1.0


@dataclass(frozen=True)
class PromptTemplate:
    """Immutable prompt template record owned by one office."""

    prompt_template_id: str
    prompt_version: str
    office: str
    office_version: str
    schema_version: str
    cognitive_responsibility: str
    temperature: float
    top_p: float
    maximum_input_tokens: int
    maximum_output_tokens: int
    maximum_reasoning_cost_usd: float
    maximum_latency_seconds: int
    output_schema: tuple[str, ...]
    immutable: bool = True


class PromptContractLibrary:
    """Immutable prompt template library for model-facing ARGOS cognition."""

    def __init__(self) -> None:
        self._templates = {template.prompt_template_id: template for template in _default_templates()}

    def template(self, prompt_template_id: str) -> PromptTemplate:
        """Return one immutable template."""
        if prompt_template_id not in self._templates:
            raise ValueError(f"unknown prompt template: {prompt_template_id}")
        return self._templates[prompt_template_id]

    def office_template(self, office: str) -> PromptTemplate:
        """Return the active prompt template for an office."""
        for template in self._templates.values():
            if template.office == office:
                return template
        raise ValueError(f"unknown office prompt template: {office}")

    def snapshot(self) -> dict[str, Any]:
        """Return prompt library visibility state."""
        return {
            "libraryName": "Prompt & Cognitive Contract Framework",
            "engineeringOrder": "OE-011F",
            "contractVersion": PROMPT_CONTRACT_VERSION,
            "defaultTemperature": DEFAULT_TEMPERATURE,
            "topP": DEFAULT_TOP_P,
            "providerIndependent": True,
            "templates": tuple(asdict(item) for item in self._templates.values()),
            "officeResponsibilities": _office_responsibilities(),
            "schemas": {office: tuple(schema) for office, schema in OFFICE_OUTPUT_SCHEMAS.items()},
            "requiredEnvelopeFields": REQUIRED_ENVELOPE_FIELDS,
            "validationPipeline": VALIDATION_PIPELINE,
        }


REQUIRED_ENVELOPE_FIELDS = (
    "enterprise_identity",
    "workflow_id",
    "workflow_token_id",
    "decision_object_id",
    "current_office",
    "current_stage",
    "current_revision",
    "execution_environment",
    "strategy",
    "portfolio_context",
    "risk_constraints",
    "commander_constraints",
    "task",
    "output_schema",
    "budget",
    "audit_identifier",
    "prompt_version",
    "prompt_template_id",
    "office_version",
    "schema_version",
    "validation_rules",
)

VALIDATION_PIPELINE = (
    "JSON validation",
    "Schema validation",
    "Office validation",
    "Workflow validation",
    "Budget validation",
    "LAW VII validation",
    "Decision Object validation",
)

ANALYST_SCHEMA = (
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
    "confidence_reason",
    "uncertainty_sources",
    "required_additional_information",
    "reasoning_audit",
)

OFFICE_OUTPUT_SCHEMAS = {
    "Seeker": ("discovered_information", "evidence", "information_gaps", "confidence", "reasoning_audit"),
    "Analyst": ANALYST_SCHEMA,
    "Risk": ("downside_risks", "risk_adjustment", "invalidation_conditions", "confidence", "reasoning_audit"),
    "Trader": ("execution_readiness", "order_constraints", "execution_risks", "confidence", "reasoning_audit"),
    "Historian": ("summary", "lessons", "archive_references", "confidence", "reasoning_audit"),
}


def build_prompt_contract_envelope(
    *,
    library: PromptContractLibrary,
    workflow_id: str,
    workflow_token_id: str,
    decision_object_id: str,
    current_office: str,
    current_stage: str,
    current_revision: int,
    execution_environment: str,
    strategy: str,
    portfolio_context: dict[str, Any],
    risk_constraints: dict[str, Any],
    commander_constraints: dict[str, Any],
    task: str,
    budget: dict[str, Any],
    audit_identifier: str,
    decision_object: dict[str, Any],
    evidence_package: dict[str, Any],
) -> dict[str, Any]:
    """Build the standard OE-011F prompt envelope."""
    template = library.office_template(current_office)
    return {
        "enterprise_identity": "ARGOS Deterministic Cognitive Enterprise",
        "workflow_id": workflow_id,
        "workflow_token_id": workflow_token_id,
        "decision_object_id": decision_object_id,
        "current_office": current_office,
        "current_stage": current_stage,
        "current_revision": int(current_revision),
        "execution_environment": execution_environment,
        "strategy": strategy,
        "portfolio_context": dict(portfolio_context),
        "risk_constraints": dict(risk_constraints),
        "commander_constraints": dict(commander_constraints),
        "task": task,
        "output_schema": tuple(template.output_schema),
        "budget": dict(budget),
        "audit_identifier": audit_identifier,
        "prompt_version": template.prompt_version,
        "prompt_template_id": template.prompt_template_id,
        "office_version": template.office_version,
        "schema_version": template.schema_version,
        "validation_rules": VALIDATION_PIPELINE,
        "temperature": template.temperature,
        "top_p": template.top_p,
        "decision_object": dict(decision_object),
        "evidence_package": dict(evidence_package),
        "cognitive_responsibility": template.cognitive_responsibility,
        "hallucination_policy": "Return INSUFFICIENT_EVIDENCE when evidence is insufficient.",
        "response_format": "JSON_ONLY",
        "contract_version": PROMPT_CONTRACT_VERSION,
    }


def validate_prompt_contract_envelope(request: Any, library: PromptContractLibrary) -> tuple[str, str]:
    """Validate that a gateway request includes the standard cognitive envelope."""
    envelope = getattr(request, "prompt_contract_envelope", None) or {}
    if not envelope:
        return "PROMPT_CONTRACT_MISSING", "Gateway request requires a Prompt & Cognitive Contract envelope."
    missing = tuple(field for field in REQUIRED_ENVELOPE_FIELDS if field not in envelope)
    if missing:
        return "PROMPT_CONTRACT_METADATA_MISSING", f"Prompt contract missing metadata: {', '.join(missing)}."
    try:
        template = library.template(str(envelope["prompt_template_id"]))
    except ValueError as exc:
        return "PROMPT_TEMPLATE_UNKNOWN", str(exc)
    if envelope["workflow_id"] != request.workflow_id or envelope["workflow_token_id"] != request.workflow_token_id:
        return "PROMPT_CONTRACT_SCOPE_MISMATCH", "Prompt contract workflow scope does not match gateway request."
    if envelope["current_office"] != request.requesting_office or envelope["current_stage"] != request.workflow_stage:
        return "PROMPT_CONTRACT_OFFICE_MISMATCH", "Prompt contract office or stage does not match gateway request."
    if template.office != request.requesting_office:
        return "PROMPT_CONTRACT_OFFICE_SCHEMA_MISMATCH", "Prompt template belongs to a different office."
    if envelope["output_schema"] != tuple(template.output_schema):
        return "PROMPT_CONTRACT_SCHEMA_MISMATCH", "Prompt contract output schema does not match the immutable prompt template."
    if tuple(envelope["output_schema"]) != tuple(OFFICE_OUTPUT_SCHEMAS.get(request.requesting_office, ())):
        return "PROMPT_CONTRACT_SCHEMA_MISMATCH", "Prompt contract used the wrong office schema."
    if float(envelope.get("temperature", DEFAULT_TEMPERATURE)) != DEFAULT_TEMPERATURE:
        return "PROMPT_CONTRACT_TEMPERATURE_VIOLATION", "Production prompt temperature must be 0.2."
    if float(envelope.get("top_p", DEFAULT_TOP_P)) != DEFAULT_TOP_P:
        return "PROMPT_CONTRACT_TOP_P_VIOLATION", "Production top_p is fixed."
    if envelope["audit_identifier"] != request.audit_identifier:
        return "PROMPT_CONTRACT_AUDIT_MISMATCH", "Prompt contract audit identifier does not match gateway request."
    return "", ""


def validate_office_response_schema(office: str, parsed: dict[str, Any]) -> tuple[str, str]:
    """Validate an office-specific model response schema."""
    required = OFFICE_OUTPUT_SCHEMAS.get(office, ())
    missing = tuple(field for field in required if field not in parsed)
    if missing:
        return "PROMPT_CONTRACT_RESPONSE_SCHEMA_INVALID", f"Provider response missing fields: {', '.join(missing)}."
    if office == "Analyst" and parsed.get("recommendation") not in {"BUY", "SELL", "HOLD", "WATCH", "INSUFFICIENT_EVIDENCE"}:
        return "PROMPT_CONTRACT_RESPONSE_SCHEMA_INVALID", "Analyst recommendation violates allowed values."
    return "", ""


def prompt_contract_trace(envelope: dict[str, Any], response: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return replayable prompt contract metadata for outputs and Decision Laboratory."""
    response = response or {}
    return {
        "promptVersion": envelope.get("prompt_version", ""),
        "promptTemplateId": envelope.get("prompt_template_id", ""),
        "officeVersion": envelope.get("office_version", ""),
        "schemaVersion": envelope.get("schema_version", ""),
        "contractVersion": envelope.get("contract_version", PROMPT_CONTRACT_VERSION),
        "temperature": envelope.get("temperature", DEFAULT_TEMPERATURE),
        "topP": envelope.get("top_p", DEFAULT_TOP_P),
        "outputSchema": tuple(envelope.get("output_schema", ())),
        "validationRules": tuple(envelope.get("validation_rules", ())),
        "responseValidationResult": response.get("validation_status", "VALID"),
        "replayable": True,
    }


def _default_templates() -> tuple[PromptTemplate, ...]:
    return (
        _template("Seeker", "PROMPT-CONTRACT-SEEKER-1.0.0", "Discover information. Never recommend trades.", 1500, 400, 0.001),
        _template("Analyst", "PROMPT-CONTRACT-ANALYST-1.0.0", "Analyze evidence. Produce recommendation. Never execute.", 2000, 600, 0.001),
        _template("Risk", "PROMPT-CONTRACT-RISK-1.0.0", "Evaluate downside. Modify recommendation only through risk.", 1500, 400, 0.001),
        _template("Trader", "PROMPT-CONTRACT-TRADER-1.0.0", "Determine execution. Never invent analysis.", 1500, 400, 0.001),
        _template("Historian", "PROMPT-CONTRACT-HISTORIAN-1.0.0", "Summarize, archive, and extract lessons.", 1500, 400, 0.001),
    )


def _template(office: str, template_id: str, responsibility: str, input_tokens: int, output_tokens: int, cost: float) -> PromptTemplate:
    return PromptTemplate(
        prompt_template_id=template_id,
        prompt_version="1.0.0",
        office=office,
        office_version="1.0.0",
        schema_version="1.0.0",
        cognitive_responsibility=responsibility,
        temperature=DEFAULT_TEMPERATURE,
        top_p=DEFAULT_TOP_P,
        maximum_input_tokens=input_tokens,
        maximum_output_tokens=output_tokens,
        maximum_reasoning_cost_usd=cost,
        maximum_latency_seconds=20,
        output_schema=OFFICE_OUTPUT_SCHEMAS[office],
    )


def _office_responsibilities() -> dict[str, str]:
    return {template.office: template.cognitive_responsibility for template in _default_templates()}
