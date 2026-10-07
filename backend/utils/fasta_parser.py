def extract_dna_sequence(content):
    lines = content.splitlines()

    sequence_parts = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Ignore FASTA header
        if line.startswith(">"):
            continue

        sequence_parts.append(line)

    sequence = "".join(sequence_parts).upper()

    return sequence