
import logging
import time

from services import mutation_service
from utils.exceptions import EngineError

logger = logging.getLogger(__name__)


def _format_mutation(raw: dict) -> dict:
    kind = raw["type"]

    if kind in ("SNP", "Substitution"):
        return {
            "type": "Substitution",
            "position": raw["position"],
            "original": raw["reference_base"],
            "mutated": raw["sample_base"],
        }
    if kind == "Insertion":
        return {
            "type": "Insertion",
            "position": raw["position"],
            "original": "-",
            "mutated": raw["inserted_base"],
        }
    if kind == "Deletion":
        return {
            "type": "Deletion",
            "position": raw["position"],
            "original": raw["deleted_base"],
            "mutated": "-",
        }
    raise ValueError(f"unknown mutation type {kind!r}")


def analyze(reference: str, sample: str) -> dict:
    """`reference` and `sample` must already be normalised and validated."""
    started = time.perf_counter()

    try:
        raw_mutations = mutation_service.detect_mutations(reference, sample)
        mutations = [_format_mutation(m) for m in raw_mutations]
    except Exception as error:
        logger.exception(
            "Algorithm engine failed (reference_len=%d, sample_len=%d)",
            len(reference), len(sample),
        )
        # Never leak internals to the client.
        raise EngineError("Mutation analysis failed. Please try again.") from error

    summary = {
        "substitutions": sum(m["type"] == "Substitution" for m in mutations),
        "insertions": sum(m["type"] == "Insertion" for m in mutations),
        "deletions": sum(m["type"] == "Deletion" for m in mutations),
    }

    logger.info(
        "Analysis done reference_len=%d sample_len=%d mutations=%d in %.1f ms",
        len(reference), len(sample), len(mutations),
        (time.perf_counter() - started) * 1000,
    )

    return {
        "success": True,
        "message": "DNA analysis completed",
        "mutation_detected": len(mutations) > 0,
        "mutation_count": len(mutations),
        "summary": summary,
        "mutations": mutations,
    }
