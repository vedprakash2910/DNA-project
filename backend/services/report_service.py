"""Report logic: runs the analysis pipeline and builds JSON / CSV / PDF output.

Kept separate from the routes and free of FastAPI/Pydantic so it can be tested
and reused (for example from a script) without starting the server.
"""

import csv
import io
from datetime import datetime, timezone
from uuid import uuid4

from services.annotation_service import annotate_mutations
from services.classification_service import classify_mutations
from services.mutation_service import (
    calculate_metadata,
    detect_mutations,
    format_mutations,
)
from utils.exceptions import PDFNotAvailableError
from utils.validation import validate_annotation_regions, validate_sequence_pair

REPORT_VERSION = "1.0"
CSV_COLUMNS = [
    "mutation_id", "type", "category", "subtype",
    "position", "original", "mutated", "annotations",
]
PDF_MAX_ROWS = 1000


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------
def analyze_pair(reference, sample, regions=None):
    """Validate -> detect -> classify -> annotate. Raises DNAAppError on bad input."""
    reference, sample = validate_sequence_pair(reference, sample)
    regions = validate_annotation_regions(regions or [], len(reference))

    mutations = format_mutations(detect_mutations(reference, sample))
    classified, summary = classify_mutations(mutations, len(reference))
    annotated = annotate_mutations(classified, regions)

    return {
        "reference": reference,
        "sample": sample,
        "mutations": annotated,
        "summary": summary,
    }


def classification_response(analysis):
    """Body returned by POST /api/dna/classify."""
    return {
        "success": True,
        "message": "Mutation classification completed",
        "mutation_detected": analysis["summary"]["mutation_detected"],
        "summary": analysis["summary"],
        "mutations": analysis["mutations"],
    }


# --------------------------------------------------------------------------
# JSON report
# --------------------------------------------------------------------------
def build_report(analysis, reference_name="reference", sample_name="sample"):
    return {
        "report_id": str(uuid4()),
        "report_version": REPORT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": {
            "reference": {
                "name": reference_name,
                "metadata": calculate_metadata(analysis["reference"]),
            },
            "sample": {
                "name": sample_name,
                "metadata": calculate_metadata(analysis["sample"]),
            },
        },
        "summary": analysis["summary"],
        "mutations": analysis["mutations"],
    }


def report_response(report):
    """Body returned by POST /api/dna/report."""
    return {
        "success": True,
        "message": "Report generated successfully",
        "report": report,
    }


# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------
def _safe_cell(value):
    """Stop spreadsheet apps from running user text as a formula (CSV injection)."""
    text = str(value)
    if text and (text[0] in "=+@\t\r" or (text[0] == "-" and len(text) > 1)):
        return "'" + text
    return text


def format_annotations(annotations):
    return "; ".join(
        f"{a['name']} ({a['feature_type']})" if a.get("feature_type") else a["name"]
        for a in annotations
    )


def report_to_csv(report):
    """One row per mutation. Returns a str (route encodes it as UTF-8 with BOM)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)

    for m in report["mutations"]:
        writer.writerow([
            m["id"], m["type"], m["category"], m["subtype"], m["position"],
            _safe_cell(m["original"]), _safe_cell(m["mutated"]),
            _safe_cell(format_annotations(m.get("annotations", []))),
        ])

    return buffer.getvalue()


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------
def _short(text, limit):
    text = str(text)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def report_to_pdf(report):
    """Return the report as PDF bytes. Needs the optional 'reportlab' package."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
    except ImportError as error:
        raise PDFNotAvailableError(
            "PDF export needs the 'reportlab' package. Run: pip install reportlab"
        ) from error

    styles = getSampleStyleSheet()
    header_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])

    summary = report["summary"]
    ref = report["inputs"]["reference"]
    smp = report["inputs"]["sample"]

    def counts(meta):
        return f"A:{meta['A_count']} T:{meta['T_count']} G:{meta['G_count']} C:{meta['C_count']}"

    story = [
        Paragraph("DNA Mutation Analysis Report", styles["Title"]),
        Paragraph(f"Report ID: {report['report_id']}", styles["Normal"]),
        Paragraph(f"Generated (UTC): {report['generated_at']}", styles["Normal"]),
        Spacer(1, 6 * mm),
        Paragraph("Input sequences", styles["Heading2"]),
    ]

    inputs_table = Table([
        ["", "Reference", "Sample"],
        ["Name", _short(ref["name"], 40), _short(smp["name"], 40)],
        ["Length (bases)", ref["metadata"]["length"], smp["metadata"]["length"]],
        ["GC content (%)", ref["metadata"]["GC_content"], smp["metadata"]["GC_content"]],
        ["Base counts", counts(ref["metadata"]), counts(smp["metadata"])],
    ], colWidths=[35 * mm, 65 * mm, 65 * mm])
    inputs_table.setStyle(header_style)
    story += [inputs_table, Spacer(1, 6 * mm), Paragraph("Summary", styles["Heading2"])]

    ratio = summary["transition_transversion_ratio"]
    summary_table = Table([
        ["Metric", "Value"],
        ["Overall classification", summary["overall_classification"]],
        ["Total mutations", summary["total_mutations"]],
        ["Mutation rate (%)", summary["mutation_rate_percent"]],
        ["Substitutions / Insertions / Deletions",
         f"{summary['by_type']['Substitution']} / {summary['by_type']['Insertion']} / "
         f"{summary['by_type']['Deletion']}"],
        ["Transitions / Transversions",
         f"{summary['by_subtype']['Transition']} / {summary['by_subtype']['Transversion']}"],
        ["Ti/Tv ratio", "n/a" if ratio is None else ratio],
    ], colWidths=[80 * mm, 85 * mm])
    summary_table.setStyle(header_style)
    story += [summary_table, Spacer(1, 6 * mm), Paragraph("Mutations", styles["Heading2"])]

    mutations = report["mutations"]
    if not mutations:
        story.append(Paragraph("No mutations detected.", styles["Normal"]))
    else:
        rows = [["ID", "Type", "Subtype", "Pos", "Orig", "Mut", "Annotations"]]
        for m in mutations[:PDF_MAX_ROWS]:
            rows.append([
                m["id"], m["type"], m["subtype"], m["position"],
                m["original"], m["mutated"],
                _short(format_annotations(m.get("annotations", [])), 45),
            ])
        table = Table(rows, repeatRows=1, colWidths=[
            14 * mm, 24 * mm, 26 * mm, 18 * mm, 14 * mm, 14 * mm, 65 * mm,
        ])
        table.setStyle(header_style)
        story.append(table)
        if len(mutations) > PDF_MAX_ROWS:
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(
                f"Showing first {PDF_MAX_ROWS} of {len(mutations)} mutations. "
                "Use the CSV export for the full list.", styles["Italic"]))

    buffer = io.BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, title="DNA Mutation Analysis Report").build(story)
    return buffer.getvalue()
