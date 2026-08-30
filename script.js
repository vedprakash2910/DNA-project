/* =========================================
   GET HTML ELEMENTS
========================================= */

const referenceInput =
    document.getElementById("referenceSequence");

const sampleInput =
    document.getElementById("sampleSequence");

const analyzeBtn =
    document.getElementById("analyzeBtn");

const mutationTable =
    document.getElementById("mutationTable");

const mutationCount =
    document.getElementById("mutationCount");

const referenceLength =
    document.getElementById("referenceLength");

const sampleLength =
    document.getElementById("sampleLength");

const errorMessage =
    document.getElementById("errorMessage");

const referenceCounter =
    document.getElementById("referenceCount");

const sampleCounter =
    document.getElementById("sampleCount");

const historyList =
    document.getElementById("historyList");

const clearHistoryBtn =
    document.getElementById("clearHistoryBtn");


/* =========================================
   CLEAN DNA SEQUENCE
========================================= */

function cleanSequence(sequence) {

    return sequence
        .toUpperCase()
        .replace(/\s+/g, "");

}


/* =========================================
   VALIDATE DNA
========================================= */

function isValidDNA(sequence) {

    return /^[ATCG]+$/.test(sequence);

}


/* =========================================
   UPDATE CHARACTER COUNTER
========================================= */

referenceInput.addEventListener("input", function () {

    const sequence = cleanSequence(this.value);

    referenceCounter.textContent =
        sequence.length + " bases";

});


sampleInput.addEventListener("input", function () {

    const sequence = cleanSequence(this.value);

    sampleCounter.textContent =
        sequence.length + " bases";

});


/* =========================================
   ANALYZE MUTATION
========================================= */

analyzeBtn.addEventListener("click", function () {

    errorMessage.textContent = "";

    const reference =
        cleanSequence(referenceInput.value);

    const sample =
        cleanSequence(sampleInput.value);


    /* Check empty input */

    if (!reference || !sample) {

        errorMessage.textContent =
            "Please enter both reference and sample DNA sequences.";

        return;
    }


    /* Check valid DNA */

    if (!isValidDNA(reference)) {

        errorMessage.textContent =
            "Reference sequence can contain only A, T, C and G.";

        return;
    }


    if (!isValidDNA(sample)) {

        errorMessage.textContent =
            "Sample sequence can contain only A, T, C and G.";

        return;
    }


    /* Update lengths */

    referenceLength.textContent =
        reference.length;

    sampleLength.textContent =
        sample.length;


    /* Find mutations */

    const mutations = [];


    const maxLength =
        Math.max(reference.length, sample.length);


    for (let i = 0; i < maxLength; i++) {

        const original =
            reference[i] || "-";

        const mutated =
            sample[i] || "-";


        if (original !== mutated) {

            let type = "Substitution";


            if (original === "-") {

                type = "Insertion";

            }
            else if (mutated === "-") {

                type = "Deletion";

            }


            mutations.push({

                type: type,

                position: i + 1,

                original: original,

                mutated: mutated

            });

        }

    }


    /* Display results */

    displayMutations(mutations);


    /* Save report */

    saveHistory(
        reference,
        sample,
        mutations
    );


    /* Scroll to results */

    document
        .getElementById("results")
        .scrollIntoView({
            behavior: "smooth"
        });

});


/* =========================================
   DISPLAY MUTATIONS
========================================= */

function displayMutations(mutations) {

    mutationCount.textContent =
        mutations.length;


    mutationTable.innerHTML = "";


    if (mutations.length === 0) {

        mutationTable.innerHTML = `
            <tr>
                <td colspan="4" class="empty">
                    ✅ No mutations detected.
                </td>
            </tr>
        `;

        return;
    }


    mutations.forEach(function (mutation) {

        const row =
            document.createElement("tr");


        row.innerHTML = `

            <td>
                <span class="mutation-type">
                    ${mutation.type}
                </span>
            </td>

            <td>
                ${mutation.position}
            </td>

            <td>
                <span class="base">
                    ${mutation.original}
                </span>
            </td>

            <td>
                <span class="base">
                    ${mutation.mutated}
                </span>
            </td>

        `;


        mutationTable.appendChild(row);

    });

}


/* =========================================
   HISTORY / REPORTS
========================================= */

function saveHistory(
    reference,
    sample,
    mutations
) {

    const history =
        JSON.parse(
            localStorage.getItem("dnaHistory")
        ) || [];


    const report = {

        id: Date.now(),

        date:
            new Date().toLocaleString(),

        referenceLength:
            reference.length,

        sampleLength:
            sample.length,

        mutationCount:
            mutations.length

    };


    history.unshift(report);


    /* Keep latest 10 reports */

    if (history.length > 10) {

        history.pop();

    }


    localStorage.setItem(
        "dnaHistory",
        JSON.stringify(history)
    );


    displayHistory();

}


/* =========================================
   DISPLAY HISTORY
========================================= */

function displayHistory() {

    const history =
        JSON.parse(
            localStorage.getItem("dnaHistory")
        ) || [];


    historyList.innerHTML = "";


    if (history.length === 0) {

        historyList.innerHTML = `
            <div class="no-history">
                No previous reports available.
            </div>
        `;

        return;
    }


    history.forEach(function (report) {

        const item =
            document.createElement("div");


        item.className =
            "history-item";


        item.innerHTML = `

            <div>

                <h4>
                    DNA Mutation Analysis
                </h4>

                <p>
                    ${report.date}
                    |
                    Reference:
                    ${report.referenceLength}
                    bases
                    |
                    Sample:
                    ${report.sampleLength}
                    bases
                </p>

            </div>

            <div class="history-count">

                ${report.mutationCount}
                mutation(s)

            </div>

        `;


        historyList.appendChild(item);

    });

}


/* =========================================
   CLEAR HISTORY
========================================= */

clearHistoryBtn.addEventListener(
    "click",
    function () {

        const confirmDelete =
            confirm(
                "Are you sure you want to clear all history?"
            );


        if (!confirmDelete) {

            return;

        }


        localStorage.removeItem(
            "dnaHistory"
        );


        displayHistory();

    }
);


/* =========================================
   LOAD HISTORY WHEN PAGE OPENS
========================================= */

displayHistory();