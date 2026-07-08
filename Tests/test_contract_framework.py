from pathlib import Path
import json
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.contracts import (  # noqa: E402
    BaseContract,
    ContractValidationError,
    InfrastructureContract,
    OperationalContract,
    ValidationStatus,
)


def valid_contract_data() -> dict[str, object]:
    return {
        "contract_id": "DOC-001",
        "contract_type": "BASE_CONTRACT",
        "contract_version": "1.0.0",
        "schema_version": "1.0.0",
        "case_file_id": "CF-001",
        "trade_cycle_id": "TC-001",
        "parent_contract_ids": ["DOC-002", "DOC-003"],
        "produced_by_staff_id": "STF-001",
        "produced_by_group_id": "DEP-001",
        "intended_consumer_group_id": "DEP-004",
        "created_timestamp_utc": "2026-07-03T12:00:00Z",
        "updated_timestamp_utc": "2026-07-03T12:05:00Z",
        "validation_status": "valid",
        "validation_errors": [],
        "human_summary": "Canonical contract test fixture.",
        "machine_payload": {"field": "value", "count": 1},
        "signature_hash": "a" * 64,
        "source_reference_ids": ["DOC-004"],
    }


class ContractFrameworkTests(unittest.TestCase):
    def test_valid_base_contract_creation(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data())
        self.assertEqual(contract.contract_id, "DOC-001")
        self.assertEqual(contract.validation_status, ValidationStatus.VALID)
        self.assertEqual(contract.parent_contract_ids, ("DOC-002", "DOC-003"))

    def test_operational_and_infrastructure_contracts_inherit_base_contract(self) -> None:
        operational = OperationalContract.from_dict(valid_contract_data())
        infrastructure = InfrastructureContract.from_dict(valid_contract_data())

        self.assertIsInstance(operational, BaseContract)
        self.assertIsInstance(infrastructure, BaseContract)
        self.assertEqual(operational.to_dict()["contract_family"], "operational")
        self.assertEqual(infrastructure.to_dict()["contract_family"], "infrastructure")

    def test_missing_required_fields_are_rejected(self) -> None:
        data = valid_contract_data()
        data.pop("contract_id")

        with self.assertRaises(ContractValidationError) as context:
            BaseContract.from_dict(data)

        self.assertIn("missing required fields: contract_id", str(context.exception))

    def test_malformed_identifiers_are_rejected(self) -> None:
        data = valid_contract_data()
        data["case_file_id"] = "CF-2026-000001"

        with self.assertRaises(ContractValidationError) as context:
            BaseContract.from_dict(data)

        self.assertIn("case_file_id", str(context.exception))

    def test_json_serialization_and_deserialization_round_trip(self) -> None:
        contract = BaseContract.from_dict(valid_contract_data())
        payload = contract.to_json()
        decoded = json.loads(payload)

        self.assertEqual(list(decoded.keys()), sorted(decoded.keys()))
        self.assertEqual(decoded["validation_status"], "valid")
        self.assertEqual(BaseContract.from_json(payload), contract)

    def test_parent_contract_linkage_is_validated(self) -> None:
        data = valid_contract_data()
        data["parent_contract_ids"] = ["DOC-001"]

        with self.assertRaises(ContractValidationError) as context:
            BaseContract.from_dict(data)

        self.assertIn("parent_contract_ids must not include contract_id", str(context.exception))

    def test_parent_contract_duplicates_are_rejected(self) -> None:
        data = valid_contract_data()
        data["parent_contract_ids"] = ["DOC-002", "DOC-002"]

        with self.assertRaises(ContractValidationError) as context:
            BaseContract.from_dict(data)

        self.assertIn("parent_contract_ids must not contain duplicates", str(context.exception))

    def test_invalid_status_requires_validation_errors(self) -> None:
        data = valid_contract_data()
        data["validation_status"] = "invalid"

        with self.assertRaises(ContractValidationError) as context:
            BaseContract.from_dict(data)

        self.assertIn("validation_errors must not be empty", str(context.exception))

    def test_valid_status_rejects_validation_errors(self) -> None:
        data = valid_contract_data()
        data["validation_errors"] = ["unexpected error"]

        with self.assertRaises(ContractValidationError) as context:
            BaseContract.from_dict(data)

        self.assertIn("validation_errors must be empty", str(context.exception))


if __name__ == "__main__":
    unittest.main()

