"""Regenerates docs/sample_outputs/* from the real report code.

Run from the backend folder:   python -m tests.generate_sample_outputs
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from services.report_service import (  # noqa: E402
    analyze_pair, build_report, classification_response,
    report_response, report_to_csv, report_to_pdf,
)
from tests.sample_data import ANNOTATIONS, REFERENCE, SAMPLE  # noqa: E402
from utils.exceptions import DNAAppError, PDFNotAvailableError  # noqa: E402

OUT = os.path.join(ROOT, "docs", "sample_outputs")
os.makedirs(OUT, exist_ok=True)


def save_json(name, data):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def error_body(error):
    return {"success": False, "detail": error.message, "error_code": error.error_code}


request = {
    "reference": REFERENCE,
    "sample": SAMPLE,
    "reference_name": "reference.fasta",
    "sample_name": "sample.fasta",
    "annotations": ANNOTATIONS,
}
save_json("request.json", request)

analysis = analyze_pair(REFERENCE, SAMPLE, ANNOTATIONS)
save_json("classify_response.json", classification_response(analysis))

report = build_report(analysis, "reference.fasta", "sample.fasta")
# fixed id/time so the committed sample does not change on every regeneration
report["report_id"] = "00000000-0000-4000-8000-000000000000"
report["generated_at"] = "2026-10-07T12:00:00+00:00"
save_json("report_response.json", report_response(report))

with open(os.path.join(OUT, "report.csv"), "w", encoding="utf-8", newline="") as f:
    f.write(report_to_csv(report))

try:
    with open(os.path.join(OUT, "report.pdf"), "wb") as f:
        f.write(report_to_pdf(report))
except PDFNotAvailableError:
    print("reportlab not installed - report.pdf skipped")

errors = {}
for key, args in {
    "missing_sequence": ("", "ATGC", None),
    "invalid_sequence": ("ATGX", "ATGC", None),
    "annotation_out_of_range": ("ATGC", "ATGC", [{"name": "Gene", "start": 2, "end": 99}]),
}.items():
    try:
        analyze_pair(*args)
    except DNAAppError as error:
        errors[key] = {"http_status": error.status_code, "body": error_body(error)}
save_json("error_examples.json", errors)
print("sample outputs written to", OUT)
