"""Attaches annotations (genes, exons, regions...) to classified mutations.

Two ways annotations get connected:

1. Regions sent in the request (``annotations`` list: name/start/end/feature_type).
   A mutation is annotated with every region that contains its reference position.

2. A pluggable provider. If your team has its own annotation code, register it once
   at start-up and it will be called for every mutation:

       from services.annotation_service import register_annotation_provider

       def my_provider(mutation: dict) -> list[dict]:
           # return e.g. [{"name": "BRCA1", "feature_type": "gene"}]
           ...

       register_annotation_provider(my_provider)

Positions are 1-based positions on the REFERENCE sequence. For an insertion this is
the reference position the inserted base sits before.
"""

from utils.exceptions import ReportGenerationError

_provider = None


def register_annotation_provider(provider):
    """Register a callable(mutation_dict) -> list of annotation dicts (or None to clear)."""
    global _provider
    _provider = provider


def _from_regions(position, regions):
    return [
        {
            "name": region["name"],
            "feature_type": region["feature_type"],
            "start": region["start"],
            "end": region["end"],
        }
        for region in regions
        if region["start"] <= position <= region["end"]
    ]


def annotate_mutations(mutations, regions=None):
    """Return a NEW list of mutations, each with an ``annotations`` list."""
    regions = regions or []
    annotated = []

    for mutation in mutations:
        annotations = _from_regions(mutation["position"], regions)

        if _provider is not None:
            try:
                extra = _provider(dict(mutation)) or []
            except Exception as error:
                raise ReportGenerationError(
                    f"Annotation provider failed for mutation {mutation['id']}: {error}"
                ) from error
            annotations.extend(extra)

        annotated.append({**mutation, "annotations": annotations})

    return annotated
