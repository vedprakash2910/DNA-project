def calculate_metadata(sequence):
    sequence = sequence.upper()

    length = len(sequence)

    a_count = sequence.count("A")
    t_count = sequence.count("T")
    g_count = sequence.count("G")
    c_count = sequence.count("C")

    if length > 0:
        gc_content = ((g_count + c_count) / length) * 100
    else:
        gc_content = 0

    return {
        "length": length,
        "A_count": a_count,
        "T_count": t_count,
        "G_count": g_count,
        "C_count": c_count,
        "GC_content": round(gc_content, 2)
    }


def detect_mutations(reference, sample):
    mutations = []

    i = 0
    j = 0

    while i < len(reference) and j < len(sample):

        if reference[i] == sample[j]:
            i += 1
            j += 1
            continue

        # Check for insertion
        if j + 1 < len(sample) and reference[i] == sample[j + 1]:
            mutations.append({
                "type": "Insertion",
                "position": i + 1,
                "inserted_base": sample[j]
            })

            j += 1
            continue

        # Check for deletion
        if i + 1 < len(reference) and reference[i + 1] == sample[j]:
            mutations.append({
                "type": "Deletion",
                "position": i + 1,
                "deleted_base": reference[i]
            })

            i += 1
            continue

        # Otherwise, treat it as SNP
        mutations.append({
            "type": "SNP",
            "position": i + 1,
            "reference_base": reference[i],
            "sample_base": sample[j]
        })

        i += 1
        j += 1

    # Remaining sample bases = insertion
    while j < len(sample):
        mutations.append({
            "type": "Insertion",
            "position": i + 1,
            "inserted_base": sample[j]
        })

        j += 1

    # Remaining reference bases = deletion
    while i < len(reference):
        mutations.append({
            "type": "Deletion",
            "position": i + 1,
            "deleted_base": reference[i]
        })

        i += 1

    return mutations