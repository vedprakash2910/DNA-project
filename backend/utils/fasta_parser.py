def extract_dna_sequence(content: str) -> str:
    """Return a clean, upper-case sequence from FASTA / plain-text content.

    - FASTA header lines (starting with '>') are skipped
    - all whitespace (spaces, tabs, CR/LF) is removed
    """
    sequence_parts = []

    for line in content.splitlines():
        line = line.strip()

        if not line or line.startswith(">"):
            continue

        sequence_parts.append("".join(line.split()))

    return "".join(sequence_parts).upper()
