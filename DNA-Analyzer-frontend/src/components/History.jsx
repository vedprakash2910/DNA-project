import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

const PAGE_SIZE = 5;
const STATUS_OPTIONS = ["All", "Mutations Found", "No Mutations", "Failed"];

const STATUS_CLASS = {
  "Mutations Found": "status-badge--mutations",
  "No Mutations": "status-badge--clean",
  Failed: "status-badge--failed",
};

function formatDate(isoOrDisplayDate) {
  const parsed = new Date(isoOrDisplayDate);
  // Older records (pre-upgrade) may already be stored as a display string;
  // fall back to showing them as-is if they don't parse as a real date.
  return Number.isNaN(parsed.getTime())
    ? isoOrDisplayDate
    : parsed.toLocaleString();
}

// Builds a small, human-readable text report for the download action.
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

function History({ history, onClear }) {
  const [statusFilter, setStatusFilter] = useState("All");
  const [dateSearch, setDateSearch] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  // Filtering by status and by a free-text date search
  const filteredHistory = useMemo(() => {
    return history.filter((report) => {
      const matchesStatus =
        statusFilter === "All" || report.status === statusFilter;

      const matchesDate =
        dateSearch.trim() === "" ||
        formatDate(report.date)
          .toLowerCase()
          .includes(dateSearch.trim().toLowerCase());

      return matchesStatus && matchesDate;
    });
  }, [history, statusFilter, dateSearch]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filteredHistory.length / PAGE_SIZE));

  const paginatedHistory = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredHistory.slice(start, start + PAGE_SIZE);
  }, [filteredHistory, currentPage]);

  // Reset to page 1 whenever the underlying data or filters change, without
  // an extra render pass (see MutationResults for the same pattern).
  const [resetSignature, setResetSignature] = useState({
    history,
    statusFilter,
    dateSearch,
  });
  if (
    resetSignature.history !== history ||
    resetSignature.statusFilter !== statusFilter ||
    resetSignature.dateSearch !== dateSearch
  ) {
    setResetSignature({ history, statusFilter, dateSearch });
    if (currentPage !== 1) setCurrentPage(1);
  }

  const goToPrevPage = () => setCurrentPage((p) => Math.max(1, p - 1));
  const goToNextPage = () => setCurrentPage((p) => Math.min(totalPages, p + 1));

  const showControls = history.length > 0;

  return (
    <section id="history" className="section">
      <div className="section-title">
        <h2>History / Reports</h2>
        <p>Previous DNA mutation analysis reports.</p>
      </div>

      <div className="history-box">
        <div className="history-header">
          <h3>Analysis History</h3>

          <button className="clear-btn" onClick={onClear}>
            Clear History
          </button>
        </div>

        {showControls && (
          <div className="controls-bar">
            <label className="control">
              Filter by status
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>

            <label className="control">
              Filter by date
              <input
                type="text"
                placeholder="e.g. 2026 or Sep"
                value={dateSearch}
                onChange={(e) => setDateSearch(e.target.value)}
              />
            </label>

            <span className="result-count">
              Showing {paginatedHistory.length} of {filteredHistory.length}{" "}
              record(s)
            </span>
          </div>
        )}

        {history.length === 0 ? (
          <div className="no-history">No previous reports available.</div>
        ) : filteredHistory.length === 0 ? (
          <div className="no-history">
            No reports match the current filters.
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Reference</th>
                  <th>Sample</th>
                  <th>Status</th>
                  <th>Mutations</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {paginatedHistory.map((report) => (
                  <tr key={report.id}>
                    <td>{formatDate(report.date)}</td>
                    <td>{report.referenceLength} bases</td>
                    <td>{report.sampleLength} bases</td>
                    <td>
                      <span
                        className={`status-badge ${
                          STATUS_CLASS[report.status] || ""
                        }`}
                      >
                        {report.status}
                      </span>
                    </td>
                    <td className="history-count">{report.mutationCount}</td>
                    <td>
                      <div className="history-actions">
                        <Link
                          className="view-btn"
                          to={`/history/${report.id}`}
                        >
                          View
                        </Link>
                        <button
                          type="button"
                          className="download-btn"
                          onClick={() => downloadReport(report)}
                        >
                          Download
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {showControls && totalPages > 1 && (
          <div className="pagination">
            <button
              onClick={goToPrevPage}
              disabled={currentPage === 1}
              className="page-btn"
            >
              ← Prev
            </button>

            <span className="page-indicator">
              Page {currentPage} of {totalPages}
            </span>

            <button
              onClick={goToNextPage}
              disabled={currentPage === totalPages}
              className="page-btn"
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

export default History;
