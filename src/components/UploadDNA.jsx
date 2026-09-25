import { useState } from "react";

function UploadDNA({ onAnalyze, isLoading }) {

  const [reference, setReference] = useState("");
  const [sample, setSample] = useState("");
  const [error, setError] = useState("");

  const cleanSequence = (sequence) => {
    return sequence
      .toUpperCase()
      .replace(/\s+/g, "");
  };

  const handleAnalyze = () => {

    if (isLoading) return;

    setError("");

    const ref = cleanSequence(reference);
    const sam = cleanSequence(sample);

    if (!ref || !sam) {
      setError(
        "Please enter both DNA sequences."
      );
      return;
    }

    if (!/^[ATCG]+$/.test(ref)) {
      setError(
        "Reference sequence can contain only A, T, C and G."
      );
      return;
    }

    if (!/^[ATCG]+$/.test(sam)) {
      setError(
        "Sample sequence can contain only A, T, C and G."
      );
      return;
    }

    onAnalyze(ref, sam);
  };

  return (
    <section id="upload" className="section">

      <div className="section-title">

        <h2>
          Upload DNA Sequence
        </h2>

        <p>
          Enter reference and sample DNA sequences.
        </p>

      </div>

      <div className="upload-container">

        {/* Reference Sequence */}

        <div className="sequence-card">

          <div className="card-header">

            <div className="icon">
              🧬
            </div>

            <div>
              <h3>
                Reference Sequence
              </h3>

              <p>
                Enter the original DNA sequence
              </p>
            </div>

          </div>

          <textarea
            value={reference}
            onChange={(e) =>
              setReference(e.target.value)
            }
            placeholder="Example: ATGCTAGCTAGC"
          />

          <div className="sequence-info">
            {cleanSequence(reference).length} bases
          </div>

        </div>


        {/* Sample Sequence */}

        <div className="sequence-card sequence-card--sample">

          <div className="card-header">

            <div className="icon">
              🔬
            </div>

            <div>
              <h3>
                Sample Sequence
              </h3>

              <p>
                Enter the sample DNA sequence
              </p>
            </div>

          </div>

          <textarea
            value={sample}
            onChange={(e) =>
              setSample(e.target.value)
            }
            placeholder="Example: ATGCTGGCTAGC"
          />

          <div className="sequence-info">
            {cleanSequence(sample).length} bases
          </div>

        </div>

      </div>


      <div className="analyze-area">

        <button
          className="analyze-btn"
          onClick={handleAnalyze}
          disabled={isLoading}
        >
          {isLoading ? "Analyzing..." : "🔍 Analyze Mutation"}
        </button>

        {error && (
          <p className="error-message">
            {error}
          </p>
        )}

      </div>

    </section>
  );
}

export default UploadDNA;