"""Classifies detected mutations and summarises them.

Pure Python (no FastAPI/Pydantic) so it can be unit-tested on its own.
"""

# Transitions swap two purines (A<->G) or two pyrimidines (C<->T).
# Every other substitution is a transversion.
TRANSITION_PAIRS = {frozenset("AG"), frozenset("CT")}

# Project-defined severity bands based on mutation rate
# (mutations / reference length * 100). These are NOT clinical thresholds:
# change them here if your team agrees on different cut-offs.
LOW_RATE_LIMIT = 1.0       # rate <  1%  -> "Low"
MODERATE_RATE_LIMIT = 5.0  # rate <  5%  -> "Moderate", otherwise "High"


def classify_mutation(mutation):
    """Return (category, subtype) for one formatted mutation."""
    mutation_type = mutation["type"]

    if mutation_type == "Substitution":
        pair = frozenset((mutation["original"], mutation["mutated"]))
        subtype = "Transition" if pair in TRANSITION_PAIRS else "Transversion"
        return "SNP", subtype

    if mutation_type in ("Insertion", "Deletion"):
        return "Indel", mutation_type

    raise ValueError(f"Unknown mutation type: {mutation_type}")


def overall_classification(total_mutations, mutation_rate_percent):
    if total_mutations == 0:
        return "No mutation detected"
    if mutation_rate_percent < LOW_RATE_LIMIT:
        return "Low"
    if mutation_rate_percent < MODERATE_RATE_LIMIT:
        return "Moderate"
    return "High"


def classify_mutations(mutations, reference_length):
    """Add id/category/subtype to each mutation and build the summary.

    Returns (classified_mutations, summary).
    """
    classified = []
    by_type = {"Substitution": 0, "Insertion": 0, "Deletion": 0}
    by_subtype = {"Transition": 0, "Transversion": 0, "Insertion": 0, "Deletion": 0}

    for number, mutation in enumerate(mutations, start=1):
        category, subtype = classify_mutation(mutation)
        by_type[mutation["type"]] += 1
        by_subtype[subtype] += 1

        classified.append({
            "id": f"M{number}",
            "type": mutation["type"],
            "category": category,
            "subtype": subtype,
            "position": mutation["position"],
            "original": mutation["original"],
            "mutated": mutation["mutated"],
        })

    total = len(classified)
    rate = round(total / reference_length * 100, 2) if reference_length else 0.0
    transversions = by_subtype["Transversion"]
    ratio = round(by_subtype["Transition"] / transversions, 2) if transversions else None

    summary = {
        "total_mutations": total,
        "mutation_detected": total > 0,
        "by_type": by_type,
        "by_subtype": by_subtype,
        "transition_transversion_ratio": ratio,
        "mutation_rate_percent": rate,
        "overall_classification": overall_classification(total, rate),
    }

    return classified, summary
