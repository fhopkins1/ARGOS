from __future__ import annotations

import json
import unittest

from Scripts import enterprise_learning_rm002_behavioral_implementation as rm002
from src.argos.control_panel.enterprise_learning_runtime import (
    EnterpriseLearningBoundaryError,
    EnterpriseLearningRuntime,
    EnterpriseLearningRuntimeError,
    HypothesisStatus,
    ProductClass,
    ProvenanceRelationship,
    ReproducibilityStatus,
)


class EnterpriseLearningRM002RuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rm002.generate()

    def test_reference_runtime_produces_complete_certification_report(self) -> None:
        runtime = rm002.build_reference_runtime()
        report = runtime.certification_report()
        self.assertEqual("PASS", report["disposition"])
        self.assertEqual(10, len(report["orders_covered"]))
        self.assertEqual("PASS", report["provenance_disposition"])
        self.assertGreaterEqual(report["publication_count"], 1)

    def test_dataset_preserves_source_ownership_and_reproducibility(self) -> None:
        runtime = EnterpriseLearningRuntime()
        dataset = runtime.create_dataset(
            dataset_id="EL-DS-001",
            purpose="Learn from historical closed-position outcomes.",
            source_refs=("HISTORIAN:JOURNEY-001", "PERFORMANCE-TRUTH:PT-001"),
            owner_refs=("Historian Office", "Performance Truth Office"),
            version="1.0.0",
            records=({"workflow": "WF-001", "return": 0.04},),
            validation_rules=("source truth immutable",),
            limitations=("single-fixture dataset",),
            event_time="2026-08-01T16:00:00+00:00",
        )
        self.assertEqual(("Historian Office", "Performance Truth Office"), dataset.owner_refs)
        self.assertEqual(ReproducibilityStatus.REPRODUCIBLE, dataset.reproducibility)
        self.assertIn(dataset.evidence_id, runtime.evidence)

    def test_feature_experiment_hypothesis_and_model_flow(self) -> None:
        runtime = rm002.build_reference_runtime()
        hypothesis = runtime.hypotheses["EL-HYP-001"]
        model = runtime.models["EL-MODEL-001"]
        self.assertEqual(HypothesisStatus.SUPPORTED, hypothesis.status)
        self.assertEqual(ProductClass.PREDICTIVE_MODEL, model.product_class)
        self.assertIn("EL-PUB-001", runtime.publications)

    def test_publication_requires_evidence_explainability_and_provenance(self) -> None:
        runtime = rm002.build_reference_runtime()
        with self.assertRaises(EnterpriseLearningRuntimeError) as context:
            runtime.publish_product(
                publication_id="EL-PUB-BAD",
                product_id="EL-MODEL-001",
                product_class=ProductClass.PREDICTIVE_MODEL,
                consumer_contract={"permitted_uses": ("advisory",), "prohibited_uses": ("execution",)},
                evidence_refs=(),
                explainability_ref="EL-XAI-001",
                provenance_refs=tuple(runtime.provenance),
                event_time="2026-08-01T16:20:00+00:00",
            )
        self.assertEqual("PUBLICATION_EVIDENCE_REQUIRED", context.exception.code)

    def test_boundary_enforcement_fails_closed_for_operational_authority(self) -> None:
        runtime = EnterpriseLearningRuntime()
        with self.assertRaises(EnterpriseLearningBoundaryError) as context:
            runtime.enforce_boundary(
                operation="AUTHORIZE_TRADE_EXECUTION",
                requested_authority="TRADER_EXECUTION_AUTHORITY",
                requesting_component="enterprise-learning",
                event_time="2026-08-01T16:21:00+00:00",
            )
        self.assertEqual("FAIL_CLOSED", context.exception.evidence["disposition"])

    def test_unknown_dataset_experiment_is_rejected(self) -> None:
        runtime = EnterpriseLearningRuntime()
        runtime.register_hypothesis(
            hypothesis_id="EL-HYP-UNKNOWN",
            objective="Unknown dataset shall fail.",
            falsification_criteria=("missing dataset blocks experiment",),
            supporting_evidence=("EL-EVID-SEED",),
            confidence=0.5,
            uncertainty=0.5,
            event_time="2026-08-01T16:22:00+00:00",
        )
        with self.assertRaises(EnterpriseLearningRuntimeError) as context:
            runtime.execute_experiment(
                experiment_id="EL-EXP-BAD",
                hypothesis_id="EL-HYP-UNKNOWN",
                dataset_id="MISSING",
                feature_ids=(),
                method="deterministic-holdout",
                seed=7,
                metrics={"accuracy": 1.0},
                event_time="2026-08-01T16:23:00+00:00",
            )
        self.assertEqual("UNKNOWN_DATASET", context.exception.code)

    def test_provenance_graph_detects_orphans(self) -> None:
        runtime = EnterpriseLearningRuntime()
        runtime.add_provenance_edge(
            source_id="missing-source",
            target_id="missing-target",
            relationship=ProvenanceRelationship.EVIDENCE_SUPPORTS_PRODUCT,
            event_time="2026-08-01T16:24:00+00:00",
        )
        report = runtime.validate_provenance_graph()
        self.assertEqual("FAIL", report["disposition"])
        self.assertEqual(1, len(report["orphan_edges"]))

    def test_generated_completion_report_authorizes_next_series(self) -> None:
        report = json.loads((rm002.OUTPUT_DIR / "completion_report.json").read_text(encoding="utf-8"))
        self.assertEqual(10, report["orders_total"])
        self.assertEqual(10, report["orders_passed"])
        self.assertEqual(0, report["orders_failed"])
        self.assertEqual("Proceed to ENTERPRISE-LEARNING-RM-002A", report["certification_decision"])


if __name__ == "__main__":
    unittest.main()
