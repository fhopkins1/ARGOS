from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from argos.foundation.identity import (  # noqa: E402
    DEPARTMENT_ID_REGISTRY,
    IdentifierKind,
    generate_case_file_id,
    generate_department_id,
    generate_document_id,
    generate_identifier,
    generate_staff_id,
    generate_trade_cycle_id,
    get_department_record,
    parse_identifier,
    validate_identifier,
)


class IdentityFrameworkTests(unittest.TestCase):
    def test_generators_emit_expected_formats(self) -> None:
        self.assertEqual(generate_department_id(1), "DEP-001")
        self.assertEqual(generate_staff_id(12), "STF-012")
        self.assertEqual(generate_trade_cycle_id(123), "TC-123")
        self.assertEqual(generate_case_file_id(7), "CF-007")
        self.assertEqual(generate_document_id(42), "DOC-042")

    def test_generators_preserve_sequences_above_three_digits(self) -> None:
        self.assertEqual(generate_case_file_id(1000), "CF-1000")

    def test_generated_identifiers_are_unique_across_supported_types(self) -> None:
        identifiers = {
            generate_department_id(1),
            generate_staff_id(1),
            generate_trade_cycle_id(1),
            generate_case_file_id(1),
            generate_document_id(1),
        }
        self.assertEqual(len(identifiers), 5)

    def test_validation_accepts_supported_identifier_types(self) -> None:
        for identifier, expected_kind in [
            ("DEP-001", IdentifierKind.DEPARTMENT),
            ("STF-001", IdentifierKind.STAFF),
            ("TC-001", IdentifierKind.TRADE_CYCLE),
            ("CF-001", IdentifierKind.CASE_FILE),
            ("DOC-001", IdentifierKind.DOCUMENT),
        ]:
            result = validate_identifier(identifier)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.kind, expected_kind)

    def test_validation_rejects_malformed_identifiers(self) -> None:
        malformed_identifiers = [
            "",
            "dep-001",
            "DEP-1",
            "DEP-ABC",
            "DEP_001",
            "UNKNOWN-001",
            "CF-000",
            "CF-001_extra",
        ]
        for identifier in malformed_identifiers:
            with self.subTest(identifier=identifier):
                self.assertFalse(validate_identifier(identifier).is_valid)

    def test_parse_identifier_returns_kind_and_sequence(self) -> None:
        self.assertEqual(parse_identifier("DOC-042"), (IdentifierKind.DOCUMENT, 42))

    def test_generation_rejects_invalid_sequences(self) -> None:
        with self.assertRaises(ValueError):
            generate_document_id(0)
        with self.assertRaises(TypeError):
            generate_identifier(IdentifierKind.DOCUMENT, "1")  # type: ignore[arg-type]

    def test_department_registry_is_deterministic_and_unique(self) -> None:
        identifiers = [record.identifier for record in DEPARTMENT_ID_REGISTRY]
        self.assertEqual(identifiers, [f"DEP-{index:03d}" for index in range(1, 10)])
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(get_department_record("DEP-005").name, "Risk Office")
        self.assertIsNone(get_department_record("DEP-999"))


if __name__ == "__main__":
    unittest.main()

