from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.control_panel import EnterpriseCreditGovernor, create_runtime  # noqa: E402


class EnterpriseCreditGovernorTests(unittest.TestCase):
    def _executing_workflow_scope(self, runtime, stages=("Executive",), credit_budget=0.5):
        state = runtime.create_workflow("LAW VII Scoped Workflow", stages, 100, credit_budget, ("summary", "audit_identifier"))
        workflow = state["workflowOrchestrator"]["workflows"][-1]
        state = runtime.start_workflow_execution(workflow["workflow_id"])
        workflow = next(item for item in state["workflowOrchestrator"]["workflows"] if item["workflow_id"] == workflow["workflow_id"])
        return workflow["workflow_id"], workflow["token"]["audit_identifier"], workflow["token"]["current_owner"]

    def test_credit_governor_is_visible_and_dormant_by_default(self) -> None:
        runtime = create_runtime()

        state = runtime.state()

        self.assertIn("creditGovernor", state)
        self.assertTrue(state["creditGovernor"]["dormantByDefault"])
        self.assertEqual(state["creditGovernor"]["mode"], "Normal")
        self.assertIn("Portfolio math", state["creditGovernor"]["deterministicCodePurposes"])

    def test_authorized_ai_activation_is_approved_and_audited(self) -> None:
        runtime = create_runtime()
        workflow_id, workflow_token_id, owner = self._executing_workflow_scope(runtime)

        state = runtime.request_credit_activation(
            task_identifier="TASK-EXPLAIN-001",
            activating_source="Commander",
            receiving_office="Executive",
            purpose="Commander explanation",
            required_output="Structured explanation",
            maximum_runtime_minutes=5,
            maximum_credit_budget_usd=0.25,
            workflow="Commander Explanation Workflow",
            organization="Executive",
            evidence_package=("EVID-001",),
            workflow_id=workflow_id,
            workflow_token_id=workflow_token_id,
            office=owner,
        )

        activation = state["creditGovernor"]["activations"][0]
        self.assertEqual(activation["status"], "APPROVED")
        self.assertTrue(any(event["office"] == "Enterprise Credit Governor" for event in state["eab"]["events"]))

    def test_deterministic_code_purpose_is_rejected(self) -> None:
        runtime = create_runtime()
        workflow_id, workflow_token_id, owner = self._executing_workflow_scope(runtime, stages=("Analyst",))

        state = runtime.request_credit_activation(
            task_identifier="TASK-PORTFOLIO-MATH",
            activating_source="Commander",
            receiving_office="Analyst",
            purpose="Portfolio math",
            required_output="Portfolio calculation",
            maximum_runtime_minutes=5,
            maximum_credit_budget_usd=0.25,
            workflow="Portfolio Math Workflow",
            organization="Analyst",
            workflow_id=workflow_id,
            workflow_token_id=workflow_token_id,
            office=owner,
        )

        activation = state["creditGovernor"]["activations"][0]
        self.assertEqual(activation["status"], "REJECTED")
        self.assertIn("deterministic code", activation["reason"].lower())

    def test_budget_configuration_changes_mode_and_spend_report(self) -> None:
        runtime = create_runtime()

        state = runtime.configure_credit_governor(1, 5, 10, "Executive", 1, "Commander Briefing Workflow", 1, "TASK-1", 0.5)

        governor = state["creditGovernor"]
        self.assertIn(governor["mode"], {"Commander Approval Mode", "Hard Stop Mode"})
        self.assertEqual(governor["budgets"]["office_budgets_usd"]["Executive"], 1)
        self.assertIn("spendByOrganization", governor["spendReport"])

    def test_completion_returns_activation_to_dormancy(self) -> None:
        runtime = create_runtime()
        workflow_id, workflow_token_id, owner = self._executing_workflow_scope(runtime)
        state = runtime.request_credit_activation(
            task_identifier="TASK-EXPLAIN-002",
            activating_source="Commander",
            receiving_office="Executive",
            purpose="Commander explanation",
            required_output="Structured explanation",
            maximum_runtime_minutes=5,
            maximum_credit_budget_usd=0.25,
            workflow="Commander Explanation Workflow",
            organization="Executive",
            workflow_id=workflow_id,
            workflow_token_id=workflow_token_id,
            office=owner,
        )
        activation_id = state["creditGovernor"]["activations"][0]["activation_id"]

        completed = runtime.complete_credit_activation(activation_id)

        self.assertEqual(completed["creditGovernor"]["activations"][0]["status"], "COMPLETED")

    def test_ui_and_server_expose_credit_governor(self) -> None:
        html = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "index.html").read_text(encoding="utf-8")
        js = (REPOSITORY_ROOT / "ui" / "argos_control_panel" / "app.js").read_text(encoding="utf-8")
        server = (REPOSITORY_ROOT / "src" / "argos" / "control_panel" / "server.py").read_text(encoding="utf-8")

        self.assertIn("Enterprise Credit Governor", html)
        self.assertIn("credit-request-activation", html)
        self.assertIn("/api/credit-governor/configure", js)
        self.assertIn("/api/credit-governor/activate", js)
        self.assertIn("/api/credit-governor/state", server)


if __name__ == "__main__":
    unittest.main()
