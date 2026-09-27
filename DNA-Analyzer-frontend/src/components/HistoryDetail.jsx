import { useParams, Link } from "react-router-dom";

const STATUS_CLASS = {
  "Mutations Found": "status-badge--mutations",
  "No Mutations": "status-badge--clean",
  Failed: "status-badge--failed",
};

function formatDate(isoOrDisplayDate) {
  const parsed = new Date(isoOrDisplayDate);
  return Number.isNaN(parsed.getTime())
    ? isoOrDisplayDate
    : parsed.toLocaleString();
}

function buildReportText(report) {
  const lines = [
    "DNA Mutation Analysis Report",
    "=============================",
    `Date: ${formatDate(report.date)}`,
    `Status: ${report.status}`,
    `Reference length: ${report.referenceLength} bases`,
    `Sample length: ${report.sampleLength} bases`,
    `Mutation count: ${report.mutationCount}`,
    "",
    "Mutations:",
  ];

  if (!report.mutations || report.mutations.length === 0) {
    lines.push("  (none)");
  } else {
    report.mutations.forEach((m) => {
      lines.push(
        `  Position ${m.position}: ${m.type} (${m.original} -> ${m.mutated})`
      );
    });
  }

  return lines.join("\n");
}

function downloadReport(report) {
  const blob = new Blob([buildReportText(report)], { type: "text/plain" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = `dna-report-${report.id}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}

// The "selected report" screen: reached from History's "View" action via
// /history/:id. Pulls the matching record out of the history list App
// already holds in state, keyed by the id in the URL.
function HistoryDetail({ history }) {
  const { id } = useParams();
  const report = history.find((r) => String(r.id) === id);

  if (!report) {
    return (
      <section className="section">
        <div className="section-title">
          <h2>Report Not Found</h2>
          <p>
            This report may have been cleared, or the link is no longer
            valid.
          </p>
        </div>

        <div className="result-summary">
          <Link className="secondary-btn" to="/history">
            ← Back to History
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="section results-section">
      <div className="section-title">
        <h2>Report Details</h2>
        <p>{formatDate(report.date)}</p>
      </div>

      <div className="result-summary">
        <div className="summary-card">
          <span>Status</span>
          <strong>
            <span
              className={`status-badge ${STATUS_CLASS[report.status] || ""}`}
            >
              {report.status}
            </span>
          </strong>
        </div>

        <div className="summary-card">
          <span>Reference Length</span>
          <strong>{report.referenceLength} bases</strong>
        </div>

        <div className="summary-card">
          <span>Sample Length</span>
          <strong>{report.sampleLength} bases</strong>
        </div>

        <div className="summary-card">
          <span>Total Mutations</span>
          <strong>{report.mutationCount}</strong>
        </div>
      </div>

      <div className="mutation-box">
        <div className="mutation-header">
          <h3>Mutation Details</h3>
          <p>Full breakdown for this report</p>

          <div className="history-actions">
            <button
              type="button"
              className="download-btn"
              onClick={() => downloadReport(report)}
            >
              Download
            </button>
            <Link className="view-btn" to="/history">
              ← Back to History
            </Link>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Mutation Type</th>
                <th>Position</th>
                <th>Original Base</th>
                <th>Mutated Base</th>
              </tr>
            </thead>

            <tbody>
              {!report.mutations || report.mutations.length === 0 ? (
                <tr>
                  <td colSpan="4" className="empty">
                    No mutations were recorded for this report.
                  </td>
                </tr>
              ) : (
                report.mutations.map((mutation) => (
                  <tr key={`${mutation.position}-${mutation.type}`}>
                    <td>
                      <span
                        className={`mutation-type mutation-type--${mutation.type.toLowerCase()}`}
                      >
                        {mutation.type}
                      </span>
                    </td>
                    <td>{mutation.position}</td>
                    <td className="base">{mutation.original}</td>
                    <td className="base">{mutation.mutated}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

export default HistoryDetail;
