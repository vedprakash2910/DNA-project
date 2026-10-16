# DNA Mutation Detector - Classification & Report API

Base URL (local): `http://127.0.0.1:8000` - interactive docs at `/docs` (Swagger).
All endpoints below are `POST`, accept JSON, and live under `/api/dna`.

| Endpoint | Returns |
|---|---|
| `/api/dna/classify` | Mutations with category/subtype + summary (JSON) |
| `/api/dna/report` | Full report: inputs, summary, annotated mutations (JSON) |
| `/api/dna/report/csv` | Same report, one row per mutation (`text/csv` download) |
| `/api/dna/report/pdf` | Same report as a PDF download (needs `reportlab`) |

Existing endpoints (`/upload`, `/analyze-sequences`) are unchanged.

## Request body (all four endpoints)

| Field | Type | Required | Notes |
|---|---|---|---|
| `reference` | string | yes | A/T/G/C only. Case, spaces, line breaks and FASTA `>` header lines are cleaned automatically. Max 1,000,000 bases. |
| `sample` | string | yes | Same rules as `reference`. |
| `reference_name` | string | no | Label shown in the report. Default `"reference"`. Max 100 chars. |
| `sample_name` | string | no | Default `"sample"`. Max 100 chars. |
| `annotations` | list | no | Regions on the **reference** (see below). Max 1000. |

Annotation region: `{"name": "Exon 1", "feature_type": "exon", "start": 1, "end": 20}`
- `start`/`end` are 1-based and inclusive, `1 <= start <= end <= reference length`.
- `feature_type` is optional (default `"region"`).
- A mutation gets every region whose range contains its `position`.

Example request (sequences shortened here; full version in `docs/sample_outputs/request.json`):

```json
{
  "reference": "ATGGCCATTGTAATGGGCCG...",
  "sample": "ATGGCCGTTGTAAAGGGCCG...",
  "reference_name": "reference.fasta",
  "sample_name": "sample.fasta",
  "annotations": [
    {
      "name": "Exon 1",
      "feature_type": "exon",
      "start": 1,
      "end": 20
    },
    {
      "name": "GeneX",
      "feature_type": "gene",
      "start": 5,
      "end": 45
    }
  ]
}
```

## POST /api/dna/classify

Response `200`:

```json
{
  "success": true,
  "message": "Mutation classification completed",
  "mutation_detected": true,
  "summary": {
    "total_mutations": 4,
    "mutation_detected": true,
    "by_type": {
      "Substitution": 2,
      "Insertion": 1,
      "Deletion": 1
    },
    "by_subtype": {
      "Transition": 1,
      "Transversion": 1,
      "Insertion": 1,
      "Deletion": 1
    },
    "transition_transversion_ratio": 1.0,
    "mutation_rate_percent": 6.25,
    "overall_classification": "High"
  },
  "mutations": [
    {
      "id": "M1",
      "type": "Substitution",
      "category": "SNP",
      "subtype": "Transition",
      "position": 7,
      "original": "A",
      "mutated": "G",
      "annotations": [
        {
          "name": "Exon 1",
          "feature_type": "exon",
          "start": 1,
          "end": 20
        },
        {
          "name": "GeneX",
          "feature_type": "gene",
          "start": 5,
          "end": 45
        }
      ]
    },
    {
      "id": "M2",
      "type": "Substitution",
      "category": "SNP",
      "subtype": "Transversion",
      "position": 14,
      "original": "T",
      "mutated": "A",
      "annotations": [
        {
          "name": "Exon 1",
          "feature_type": "exon",
          "start": 1,
          "end": 20
        },
        {
          "name": "GeneX",
          "feature_type": "gene",
          "start": 5,
          "end": 45
        }
      ]
    },
    {
      "id": "M3",
      "type": "Insertion",
      "category": "Indel",
      "subtype": "Insertion",
      "position": 42,
      "original": "-",
      "mutated": "T",
      "annotations": [
        {
          "name": "GeneX",
          "feature_type": "gene",
          "start": 5,
          "end": 45
        }
      ]
    },
    {
      "id": "M4",
      "type": "Deletion",
      "category": "Indel",
      "subtype": "Deletion",
      "position": 56,
      "original": "T",
      "mutated": "-",
      "annotations": []
    }
  ]
}
```

### Mutation fields

| Field | Values |
|---|---|
| `id` | `M1`, `M2`, ... in order of position |
| `type` | `Substitution`, `Insertion`, `Deletion` (same as `/analyze-sequences`) |
| `category` | `SNP` (substitution) or `Indel` (insertion/deletion) |
| `subtype` | `Transition` (A<->G, C<->T), `Transversion` (other substitutions), `Insertion`, `Deletion` |
| `position` | 1-based position on the reference |
| `original` / `mutated` | Bases; `-` means "no base" (insertion / deletion) |
| `annotations` | List of `{name, feature_type, start, end}` (empty if none match) |

### Summary fields

| Field | Meaning |
|---|---|
| `total_mutations`, `mutation_detected` | Count and a true/false flag |
| `by_type`, `by_subtype` | Counts per type / subtype |
| `transition_transversion_ratio` | Transitions / transversions, `null` if there are no transversions |
| `mutation_rate_percent` | `total_mutations / reference length * 100` (2 decimals) |
| `overall_classification` | `No mutation detected`, `Low` (< 1%), `Moderate` (1% to < 5%), `High` (>= 5%) |

The Low/Moderate/High cut-offs are project-defined, not clinical. Change them in
`services/classification_service.py` (`LOW_RATE_LIMIT`, `MODERATE_RATE_LIMIT`).

## POST /api/dna/report

Response `200` (`report` object; full file in `docs/sample_outputs/report_response.json`):

```json
{
  "success": true,
  "message": "Report generated successfully",
  "report": {
    "report_id": "00000000-0000-4000-8000-000000000000",
    "report_version": "1.0",
    "generated_at": "2026-10-07T12:00:00+00:00",
    "inputs": {
      "reference": {
        "name": "reference.fasta",
        "metadata": {
          "length": 64,
          "A_count": 16,
          "T_count": 14,
          "G_count": 20,
          "C_count": 14,
          "GC_content": 53.12
        }
      },
      "sample": {
        "name": "sample.fasta",
        "metadata": {
          "length": 64,
          "A_count": 16,
          "T_count": 13,
          "G_count": 21,
          "C_count": 14,
          "GC_content": 54.69
        }
      }
    },
    "summary": {
      "total_mutations": 4,
      "mutation_detected": true,
      "by_type": {
        "Substitution": 2,
        "Insertion": 1,
        "Deletion": 1
      },
      "by_subtype": {
        "Transition": 1,
        "Transversion": 1,
        "Insertion": 1,
        "Deletion": 1
      },
      "transition_transversion_ratio": 1.0,
      "mutation_rate_percent": 6.25,
      "overall_classification": "High"
    },
    "mutations": [
      {
        "id": "M1",
        "type": "Substitution",
        "category": "SNP",
        "subtype": "Transition",
        "position": 7,
        "original": "A",
        "mutated": "G",
        "annotations": [
          {
            "name": "Exon 1",
            "feature_type": "exon",
            "start": 1,
            "end": 20
          },
          {
            "name": "GeneX",
            "feature_type": "gene",
            "start": 5,
            "end": 45
          }
        ]
      },
      {
        "id": "M2",
        "type": "Substitution",
        "category": "SNP",
        "subtype": "Transversion",
        "position": 14,
        "original": "T",
        "mutated": "A",
        "annotations": [
          {
            "name": "Exon 1",
            "feature_type": "exon",
            "start": 1,
            "end": 20
          },
          {
            "name": "GeneX",
            "feature_type": "gene",
            "start": 5,
            "end": 45
          }
        ]
      },
      {
        "id": "M3",
        "type": "Insertion",
        "category": "Indel",
        "subtype": "Insertion",
        "position": 42,
        "original": "-",
        "mutated": "T",
        "annotations": [
          {
            "name": "GeneX",
            "feature_type": "gene",
            "start": 5,
            "end": 45
          }
        ]
      },
      {
        "id": "M4",
        "type": "Deletion",
        "category": "Indel",
        "subtype": "Deletion",
        "position": 56,
        "original": "T",
        "mutated": "-",
        "annotations": []
      }
    ]
  }
}
```

`report_id` and `generated_at` change on every call.

## POST /api/dna/report/csv

Response `200`, `Content-Type: text/csv; charset=utf-8`,
`Content-Disposition: attachment; filename="dna_mutation_report.csv"`.
UTF-8 with BOM so Excel shows non-ASCII annotation names correctly. Cells that start with
`=`, `+`, `@` (or `-` followed by text) are prefixed with `'` to prevent spreadsheet formula injection.

```csv
mutation_id,type,category,subtype,position,original,mutated,annotations
M1,Substitution,SNP,Transition,7,A,G,Exon 1 (exon); GeneX (gene)
M2,Substitution,SNP,Transversion,14,T,A,Exon 1 (exon); GeneX (gene)
M3,Insertion,Indel,Insertion,42,-,T,GeneX (gene)
M4,Deletion,Indel,Deletion,56,T,-,
```

## POST /api/dna/report/pdf

Response `200`, `Content-Type: application/pdf`, `filename="dna_mutation_report.pdf"`.
Contains the inputs table, the summary table and the mutation table (first 1000 mutations;
the CSV has all of them). Example: `docs/sample_outputs/report.pdf`.
If `reportlab` is not installed the endpoint returns `501` (`pdf_not_available`).

Frontend download example:

```js
const res = await fetch("http://127.0.0.1:8000/api/dna/report/pdf", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ reference, sample }),
});
if (!res.ok) throw new Error((await res.json()).detail);
const url = URL.createObjectURL(await res.blob());
// <a href={url} download="dna_mutation_report.pdf">
```

## Errors

Errors from these endpoints look like this (`detail` is the same key the existing endpoints use):

```json
{ "success": false, "detail": "<human readable message>", "error_code": "<machine code>" }
```

| HTTP | `error_code` | When |
|---|---|---|
| 400 | `missing_sequence` | `reference` or `sample` is empty after cleaning |
| 400 | `invalid_sequence` | A character other than A/T/G/C (message gives the character and position) |
| 413 | `sequence_too_long` | More than 1,000,000 bases |
| 422 | `invalid_annotation` | Empty name, `start < 1`, `end < start`, `end` beyond reference, or > 1000 regions |
| 422 | *(no code; FastAPI default)* | Field missing or wrong type, e.g. `sample` not sent. Body is `{"detail": [...]}` |
| 500 | `report_generation_failed` | Annotation provider raised an error |
| 500 | `internal_error` | Unexpected bug (details are only in the server log) |
| 501 | `pdf_not_available` | `reportlab` not installed (PDF endpoint only) |

Real examples:

```json
{
  "missing_sequence": {
    "http_status": 400,
    "body": {
      "success": false,
      "detail": "Both reference and sample sequences are required",
      "error_code": "missing_sequence"
    }
  },
  "invalid_sequence": {
    "http_status": 400,
    "body": {
      "success": false,
      "detail": "Reference sequence contains invalid character 'X' at position 4. Only A, T, G and C are allowed.",
      "error_code": "invalid_sequence"
    }
  },
  "annotation_out_of_range": {
    "http_status": 422,
    "body": {
      "success": false,
      "detail": "Annotation 'Gene' ends at 99, beyond the reference length (4)",
      "error_code": "invalid_annotation"
    }
  }
}
```

## Connecting annotations

1. **From the request**: send an `annotations` list (above). Nothing else to do.
2. **From your own annotation code**: register a function once at startup (e.g. in `main.py`):

```python
from services.annotation_service import register_annotation_provider

def my_provider(mutation: dict) -> list:
    # mutation has id, type, position, original, mutated, ...
    return [{"name": "BRCA1", "feature_type": "gene"}]   # or [] if none

register_annotation_provider(my_provider)
```

Its results are added to the `annotations` list of every mutation in all four endpoints.

## Running the tests

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests -v                      # logic + API tests
python -m unittest tests.test_report_logic -v  # logic tests only (no FastAPI needed)
python -m tests.generate_sample_outputs        # regenerate docs/sample_outputs
```

## Known limitation (mutation detector)

`detect_mutations` is a one-base look-ahead heuristic, not a real alignment. Some single
substitutions are reported as a Deletion + Insertion pair (e.g. reference `ATGCATGC` vs
sample `ATGCTTGC`), and the position of an insertion next to a repeated base can be off by one.
The classification and reports show whatever the detector returns.
