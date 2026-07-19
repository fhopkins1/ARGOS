from argos.css.common import CSSCapability

from .version import CONTRACT_VERSION, EVIDENCE_SCHEMA_VERSION, IMPLEMENTATION_VERSION


def capability() -> CSSCapability:
    return CSSCapability("CSS-005", IMPLEMENTATION_VERSION, CONTRACT_VERSION, EVIDENCE_SCHEMA_VERSION, ("CSS-001", "CSS-002", "CSS-003", "CSS-004"))

