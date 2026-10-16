"""Unit tests for the classification/report logic (no FastAPI needed).

Run from the backend folder:   python -m unittest tests.test_report_logic -v
(pytest also works:            python -m pytest tests)
"""
import csv
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import annotation_service
from services.classification_service import classify_mutation, overall_classification
from services.report_service import (
    analyze_pair, build_report, report_to_csv, report_to_pdf,
)
from tests.sample_data import ANNOTATIONS, REFERENCE, SAMPLE
from utils.exceptions import (
    InvalidAnnotationError, InvalidSequenceError, MissingSequenceError,
    PDFNotAvailableError, ReportGenerationError, SequenceTooLongError,
)
from utils.validation import MAX_SEQUENCE_LENGTH, normalize_sequence


class ClassificationTests(unittest.TestCase):
    def test_transition_and_transversion(self):
        sub = lambda a, b: {"type": "Substitution", "original": a, "mutated": b}
        self.assertEqual(classify_mutation(sub("A", "G")), ("SNP", "Transition"))
        self.assertEqual(classify_mutation(sub("C", "T")), ("SNP", "Transition"))
        self.assertEqual(classify_mutation(sub("A", "C")), ("SNP", "Transversion"))
        self.assertEqual(classify_mutation(sub("G", "T")), ("SNP", "Transversion"))

    def test_indels(self):
        self.assertEqual(classify_mutation({"type": "Insertion"}), ("Indel", "Insertion"))
        self.assertEqual(classify_mutation({"type": "Deletion"}), ("Indel", "Deletion"))

    def test_overall_bands(self):
        self.assertEqual(overall_classification(0, 0), "No mutation detected")
        self.assertEqual(overall_classification(1, 0.99), "Low")
        self.assertEqual(overall_classification(1, 1.0), "Moderate")
        self.assertEqual(overall_classification(1, 5.0), "High")


class PipelineTests(unittest.TestCase):
    def test_identical_sequences(self):
        result = analyze_pair(REFERENCE, REFERENCE)
        self.assertEqual(result["mutations"], [])
        self.assertEqual(result["summary"]["overall_classification"], "No mutation detected")
        self.assertFalse(result["summary"]["mutation_detected"])
        self.assertIsNone(result["summary"]["transition_transversion_ratio"])

    def test_demo_sample_summary(self):
        s = analyze_pair(REFERENCE, SAMPLE)["summary"]
        self.assertEqual(s["total_mutations"], 4)
        self.assertEqual(s["by_type"], {"Substitution": 2, "Insertion": 1, "Deletion": 1})
        self.assertEqual(s["by_subtype"]["Transition"], 1)
        self.assertEqual(s["by_subtype"]["Transversion"], 1)
        self.assertEqual(s["transition_transversion_ratio"], 1.0)
        self.assertEqual(s["mutation_rate_percent"], round(4 / 64 * 100, 2))
        self.assertEqual(s["overall_classification"], "High")   # 6.25% >= 5%

    def test_ids_are_sequential(self):
        ids = [m["id"] for m in analyze_pair(REFERENCE, SAMPLE)["mutations"]]
        self.assertEqual(ids, ["M1", "M2", "M3", "M4"])

    def test_pasted_input_is_normalised(self):
        messy = ">seq1\r\n" + " ".join(REFERENCE[:30]) + "\r\n" + REFERENCE[30:].lower()
        self.assertEqual(normalize_sequence(messy), REFERENCE)
        self.assertEqual(analyze_pair(messy, REFERENCE)["mutations"], [])


class AnnotationTests(unittest.TestCase):
    def tearDown(self):
        annotation_service.register_annotation_provider(None)

    def test_regions_attach_by_position(self):
        by_pos = {m["position"]: m for m in analyze_pair(REFERENCE, SAMPLE, ANNOTATIONS)["mutations"]}
        self.assertEqual([a["name"] for a in by_pos[7]["annotations"]], ["Exon 1", "GeneX"])
        self.assertEqual([a["name"] for a in by_pos[14]["annotations"]], ["Exon 1", "GeneX"])
        self.assertEqual(by_pos[42]["annotations"][0]["name"], "GeneX")   # insertion
        self.assertEqual(by_pos[56]["annotations"], [])                    # outside regions

    def test_no_regions_gives_empty_lists(self):
        for m in analyze_pair(REFERENCE, SAMPLE)["mutations"]:
            self.assertEqual(m["annotations"], [])

    def test_provider_is_called(self):
        annotation_service.register_annotation_provider(
            lambda m: [{"name": "custom", "feature_type": "test"}])
        for m in analyze_pair(REFERENCE, SAMPLE)["mutations"]:
            self.assertEqual(m["annotations"][-1]["name"], "custom")

    def test_provider_failure_becomes_report_error(self):
        def boom(_):
            raise RuntimeError("bad")
        annotation_service.register_annotation_provider(boom)
        with self.assertRaises(ReportGenerationError):
            analyze_pair(REFERENCE, SAMPLE)


class ValidationTests(unittest.TestCase):
    def test_missing(self):
        with self.assertRaises(MissingSequenceError):
            analyze_pair("", SAMPLE)
        with self.assertRaises(MissingSequenceError):
            analyze_pair(REFERENCE, "  \n ")

    def test_invalid_base_reports_position(self):
        with self.assertRaises(InvalidSequenceError) as ctx:
            analyze_pair("ATGX", "ATGC")
        self.assertIn("'X' at position 4", ctx.exception.message)
        self.assertIn("Reference", ctx.exception.message)

    def test_too_long(self):
        with self.assertRaises(SequenceTooLongError):
            analyze_pair("A" * (MAX_SEQUENCE_LENGTH + 1), "A")

    def test_bad_annotations(self):
        bad = [
            {"name": "", "start": 1, "end": 2},
            {"name": "x", "start": 0, "end": 2},
            {"name": "x", "start": 5, "end": 2},
            {"name": "x", "start": 1, "end": 9999},
        ]
        for region in bad:
            with self.assertRaises(InvalidAnnotationError, msg=str(region)):
                analyze_pair(REFERENCE, SAMPLE, [region])


class ReportOutputTests(unittest.TestCase):
    def setUp(self):
        self.report = build_report(
            analyze_pair(REFERENCE, SAMPLE, ANNOTATIONS), "ref.fasta", "sample.fasta")

    def test_json_report_shape(self):
        r = self.report
        self.assertEqual(r["report_version"], "1.0")
        self.assertEqual({"report_id", "generated_at", "inputs", "summary", "mutations"} - set(r), set())
        self.assertEqual(r["inputs"]["reference"]["name"], "ref.fasta")
        self.assertEqual(r["inputs"]["reference"]["metadata"]["length"], 64)

    def test_csv_rows(self):
        rows = list(csv.reader(io.StringIO(report_to_csv(self.report))))
        self.assertEqual(rows[0][0], "mutation_id")
        self.assertEqual(len(rows), 1 + 4)
        self.assertEqual(rows[1][:3], ["M1", "Substitution", "SNP"])

    def test_csv_formula_injection_is_neutralised(self):
        evil = analyze_pair(REFERENCE, SAMPLE,
                            [{"name": "=HYPERLINK(\"x\")", "start": 1, "end": 20}])
        rows = list(csv.reader(io.StringIO(report_to_csv(build_report(evil)))))
        self.assertTrue(rows[1][7].startswith("'="))
        # the plain "-" used for insertions/deletions must stay untouched
        ins = next(r for r in rows[1:] if r[1] == "Insertion")
        self.assertEqual(ins[5], "-")

    def test_pdf_bytes(self):
        try:
            pdf = report_to_pdf(self.report)
        except PDFNotAvailableError:
            self.skipTest("reportlab not installed")
        self.assertTrue(pdf.startswith(b"%PDF"))
        empty = report_to_pdf(build_report(analyze_pair(REFERENCE, REFERENCE)))
        self.assertTrue(empty.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
