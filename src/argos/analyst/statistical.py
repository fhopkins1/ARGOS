"""Statistical Analysis Office."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

from argos.foundation.audit import AuditService
from argos.foundation.communication import IncomingMailbox
from argos.foundation.configuration import ConfigurationService
from argos.foundation.contracts import OperationalContract, utc_timestamp
from argos.foundation.identity import generate_document_id
from argos.foundation.persistence import InMemoryPersistenceRepository, ObjectType
from argos.foundation.prompts import PromptRepository, PromptSnapshotService

from .department import AnalystDepartment
from .offices import ANALYST_GROUP_ID, AnalystOfficeInstrumentPanel


STATISTICAL_ANALYSIS_OFFICE_ID = "ANALYST-OFFICE-001"


@dataclass(frozen=True)
class StatisticalDataset:
    """Input dataset for deterministic statistical analysis."""

    observations: tuple[float, ...]
    predictors: tuple[float, ...]
    outcomes: tuple[float, ...]
    scenario_payoffs: tuple[float, ...]
    scenario_probabilities: tuple[float, ...]


@dataclass(frozen=True)
class ArgumentMap:
    """Mandatory argument map accompanying each statistical conclusion."""

    conclusion_id: str
    claim: str
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]
    warrant: str


class ProbabilityAnalyst:
    def estimate(self, observations: tuple[float, ...], threshold: float) -> float:
        if not observations:
            raise ValueError("probability estimation requires observations")
        return round(sum(1 for value in observations if value >= threshold) / len(observations), 4)


class DistributionAnalyst:
    def summarize(self, observations: tuple[float, ...]) -> dict[str, float]:
        if not observations:
            raise ValueError("distribution analysis requires observations")
        sorted_values = sorted(observations)
        mean = sum(sorted_values) / len(sorted_values)
        variance = sum((value - mean) ** 2 for value in sorted_values) / len(sorted_values)
        return {
            "mean": round(mean, 4),
            "median": round(_median(sorted_values), 4),
            "variance": round(variance, 4),
            "minimum": round(sorted_values[0], 4),
            "maximum": round(sorted_values[-1], 4),
        }


class CorrelationAnalyst:
    def correlate(self, x_values: tuple[float, ...], y_values: tuple[float, ...]) -> float:
        if len(x_values) != len(y_values) or not x_values:
            raise ValueError("correlation requires equal non-empty series")
        x_mean = sum(x_values) / len(x_values)
        y_mean = sum(y_values) / len(y_values)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        x_var = sum((x - x_mean) ** 2 for x in x_values)
        y_var = sum((y - y_mean) ** 2 for y in y_values)
        if x_var == 0 or y_var == 0:
            return 0.0
        return round(numerator / math.sqrt(x_var * y_var), 4)


class RegressionAnalyst:
    def regress(self, x_values: tuple[float, ...], y_values: tuple[float, ...]) -> dict[str, float]:
        if len(x_values) != len(y_values) or not x_values:
            raise ValueError("regression requires equal non-empty series")
        x_mean = sum(x_values) / len(x_values)
        y_mean = sum(y_values) / len(y_values)
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        slope = 0.0 if denominator == 0 else sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values)) / denominator
        intercept = y_mean - slope * x_mean
        predictions = tuple(intercept + slope * x for x in x_values)
        residual_sum = sum((actual - predicted) ** 2 for actual, predicted in zip(y_values, predictions))
        total_sum = sum((actual - y_mean) ** 2 for actual in y_values)
        r_squared = 1.0 if total_sum == 0 else 1 - (residual_sum / total_sum)
        return {"slope": round(slope, 4), "intercept": round(intercept, 4), "r_squared": round(r_squared, 4)}


class BayesianAnalyst:
    def update(self, prior: float, likelihood: float, false_positive_rate: float) -> float:
        denominator = likelihood * prior + false_positive_rate * (1 - prior)
        if denominator == 0:
            return 0.0
        return round((likelihood * prior) / denominator, 4)


class TimeSeriesAnalyst:
    def moving_average(self, observations: tuple[float, ...], window: int) -> float:
        if window < 1 or len(observations) < window:
            raise ValueError("moving average window is invalid")
        return round(sum(observations[-window:]) / window, 4)


class MonteCarloAnalyst:
    def expected_value(self, payoffs: tuple[float, ...], probabilities: tuple[float, ...]) -> float:
        if len(payoffs) != len(probabilities) or not payoffs:
            raise ValueError("expected value requires equal non-empty payoffs and probabilities")
        if round(sum(probabilities), 6) != 1.0:
            raise ValueError("scenario probabilities must sum to 1")
        return round(sum(payoff * probability for payoff, probability in zip(payoffs, probabilities)), 4)


class ConfidenceAnalyst:
    def confidence_interval(self, observations: tuple[float, ...]) -> dict[str, float]:
        if not observations:
            raise ValueError("confidence interval requires observations")
        mean = sum(observations) / len(observations)
        variance = sum((value - mean) ** 2 for value in observations) / len(observations)
        standard_error = math.sqrt(variance) / math.sqrt(len(observations))
        margin = 1.96 * standard_error
        return {"lower": round(mean - margin, 4), "upper": round(mean + margin, 4), "confidence_level": 0.95}

    def sensitivity(self, expected_value: float, shock: float) -> dict[str, float]:
        return {
            "downside": round(expected_value * (1 - shock), 4),
            "base": round(expected_value, 4),
            "upside": round(expected_value * (1 + shock), 4),
        }


class StatisticalOfficeChief:
    """Office Chief for deterministic statistical analysis."""

    def __init__(self) -> None:
        self.probability = ProbabilityAnalyst()
        self.distribution = DistributionAnalyst()
        self.correlation = CorrelationAnalyst()
        self.regression = RegressionAnalyst()
        self.bayesian = BayesianAnalyst()
        self.time_series = TimeSeriesAnalyst()
        self.monte_carlo = MonteCarloAnalyst()
        self.confidence = ConfidenceAnalyst()

    def analyze(self, dataset: StatisticalDataset) -> dict[str, object]:
        probability = self.probability.estimate(dataset.outcomes, 0)
        distribution = self.distribution.summarize(dataset.observations)
        correlation = self.correlation.correlate(dataset.predictors, dataset.outcomes)
        regression = self.regression.regress(dataset.predictors, dataset.outcomes)
        bayesian = self.bayesian.update(0.5, max(probability, 0.0001), 0.25)
        moving_average = self.time_series.moving_average(dataset.observations, min(3, len(dataset.observations)))
        expected_value = self.monte_carlo.expected_value(dataset.scenario_payoffs, dataset.scenario_probabilities)
        confidence_interval = self.confidence.confidence_interval(dataset.observations)
        sensitivity = self.confidence.sensitivity(expected_value, 0.1)
        model_comparison = {
            "selected_model": "linear_regression" if regression["r_squared"] >= 0.5 else "distribution_baseline",
            "regression_r_squared": regression["r_squared"],
            "baseline_variance": distribution["variance"],
        }
        return {
            "probability_estimate": probability,
            "distribution": distribution,
            "correlation": correlation,
            "regression": regression,
            "bayesian_posterior": bayesian,
            "time_series_moving_average": moving_average,
            "expected_value": expected_value,
            "confidence_interval": confidence_interval,
            "sensitivity": sensitivity,
            "model_comparison": model_comparison,
        }

    def argument_maps(self, analysis: dict[str, object], source_report_ids: tuple[str, ...]) -> tuple[ArgumentMap, ...]:
        contradiction = ("Regression support is limited." if analysis["model_comparison"]["selected_model"] == "distribution_baseline" else "")
        contradicting = (contradiction,) if contradiction else ()
        return (
            ArgumentMap(
                "CONCLUSION-001",
                "Statistical conclusion is supported by deterministic probability, expected value, and confidence estimates.",
                source_report_ids,
                contradicting,
                "Conclusion must cite quantitative outputs and preserve contradictory evidence.",
            ),
        )


class StatisticalAnalysisOffice:
    """Statistical Analysis Office integrated with Analyst Department."""

    def __init__(
        self,
        configuration_service: ConfigurationService,
        persistence_repository: InMemoryPersistenceRepository,
        audit_service: AuditService,
        prompt_repository: PromptRepository,
    ) -> None:
        self.department = AnalystDepartment(
            configuration_service,
            persistence_repository,
            audit_service,
            prompt_repository,
        )
        self.office = self.department.offices[STATISTICAL_ANALYSIS_OFFICE_ID]
        self.chief = StatisticalOfficeChief()

    def generate_statistical_aar(
        self,
        dataset: StatisticalDataset,
        source_reports: tuple[OperationalContract, ...],
        case_file_id: str,
        trade_cycle_id: str,
        document_sequence: int,
        prompt_id: str,
    ) -> OperationalContract:
        self.department.configuration_service.validate_startup()
        snapshot = PromptSnapshotService(self.department.prompt_repository).snapshot(prompt_id, case_file_id, trade_cycle_id)
        analysis = self.chief.analyze(dataset)
        source_ids = tuple(report.contract_id for report in source_reports)
        argument_maps = self.chief.argument_maps(analysis, source_ids)
        created = utc_timestamp()
        payload = {
            "office_id": STATISTICAL_ANALYSIS_OFFICE_ID,
            "office_name": self.office.record.configuration.name,
            "prompt_snapshot_id": snapshot.prompt_snapshot_id,
            "assessment_status": "statistical_analytical_assessment",
            "source_report_ids": list(source_ids),
            "statistical_analysis": analysis,
            "argument_maps": [argument_map.__dict__ for argument_map in argument_maps],
            "seeker_reports_modified": False,
            "risk_office_override": False,
        }
        signature_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        report = OperationalContract(
            contract_id=generate_document_id(document_sequence),
            contract_type="AAR",
            contract_version="1.0.0",
            schema_version="1.0.0",
            case_file_id=case_file_id,
            trade_cycle_id=trade_cycle_id,
            parent_contract_ids=source_ids,
            produced_by_staff_id=self.office.record.configuration.staff_id,
            produced_by_group_id=ANALYST_GROUP_ID,
            intended_consumer_group_id="DEP-002",
            created_timestamp_utc=created,
            updated_timestamp_utc=created,
            validation_status="valid",
            validation_errors=(),
            human_summary="Statistical Analytical Assessment Report.",
            machine_payload=payload,
            signature_hash=signature_hash,
            source_reference_ids=source_ids,
        )
        self.department.persistence_repository.persist(ObjectType.OPERATIONAL_DOCUMENT, report.contract_id, report.to_dict())
        self.office.reports_generated += 1
        return report

    def route_aar(self, aar: OperationalContract, target_inbox: IncomingMailbox):
        return self.department.route_aar(STATISTICAL_ANALYSIS_OFFICE_ID, aar, target_inbox)

    def instrument_panel(self) -> AnalystOfficeInstrumentPanel:
        return self.office.instrument_panel()


def _median(values: list[float]) -> float:
    midpoint = len(values) // 2
    if len(values) % 2:
        return values[midpoint]
    return (values[midpoint - 1] + values[midpoint]) / 2
