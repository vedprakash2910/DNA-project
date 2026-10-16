"""Shared demo input: 1 transition, 1 transversion, 1 insertion, 1 deletion."""

REFERENCE = "ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAGCTAGCTAGGATCCGATTACAGGCTA"


def _make_sample():
    s = list(REFERENCE)
    s[6] = "G"    # position 7:  A -> G  (transition)
    s[13] = "A"   # position 14: T -> A  (transversion)
    sample = "".join(s)
    sample = sample[:40] + "T" + sample[40:]   # inserted T (detector reports it at position 42 because ref[41] is also T)
    sample = sample[:55] + sample[56:]         # deletion of reference position 56
    return sample


SAMPLE = _make_sample()

ANNOTATIONS = [
    {"name": "Exon 1", "feature_type": "exon", "start": 1, "end": 20},
    {"name": "GeneX", "feature_type": "gene", "start": 5, "end": 45},
]
