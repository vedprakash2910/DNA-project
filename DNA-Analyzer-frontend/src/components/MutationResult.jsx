import { useMemo, useState } from "react";

import MutationCharts from "./MutationCharts";

const PAGE_SIZE = 8;
const FILTER_OPTIONS = ["All", "Substitution", "Insertion", "Deletion"];

function MutationResults({ mutations, isLoading, error, hasAnalyzed }) {
  const [typeFilter, setTypeFilter] = useState("All");
  const [sortOrder, setSortOrder] = useState("asc"); // "asc" | "desc" by position
  const [currentPage, setCurrentPage] = useState(1);

  // Filtering
  const filteredMutations = useMemo(() => {
    if (typeFilter === "All") return mutations;
    return mutations.filter((mutation) => mutation.type === typeFilter);
  }, [mutations, typeFilter]);

  // Sorting (by position)
  const sortedMutations = useMemo(() => {
    const copy = [...filteredMutations];
    copy.sort((a, b) =>
      sortOrder === "asc" ? a.position - b.position : b.position - a.position
    );
    return copy;
  }, [filteredMutations, sortOrder]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(sortedMutations.length / PAGE_SIZE));

  const paginatedMutations = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return sortedMutations.slice(start, start + PAGE_SIZE);
  }, [sortedMutations, currentPage]);

  // Reset to page 1 whenever the underlying data, filter, or sort changes.
  // Adjusting state while rendering (rather than in a useEffect) avoids an
  // extra render pass — see https://react.dev/learn/you-might-not-need-an-effect
  const [resetSignature, setResetSignature] = useState({ mutations, typeFilter, sortOrder });
  if (
    resetSignature.mutations !== mutations ||
    resetSignature.typeFilter !== typeFilter ||
    resetSignature.sortOrder !== sortOrder
  ) {
    setResetSignature({ mutations, typeFilter, sortOrder });
    if (currentPage !== 1) setCurrentPage(1);
  }

  const goToPrevPage = () => setCurrentPage((p) => Math.max(1, p - 1));
  const goToNextPage = () => setCurrentPage((p) => Math.min(totalPages, p + 1));

  const toggleSortOrder = () => {
    setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
  };

  const renderTableBody = () => {
    if (isLoading) {
      return (
        <tr>
          <td colSpan="4" className="empty">
            <span className="spinner" aria-hidden="true" />
            Analyzing sequences...
          </td>
        </tr>
      );
    }

    if (error) {
      return (
        <tr>
          <td colSpan="4" className="empty error-cell">
            {error}
          </td>
        </tr>
      );
    }

    if (!hasAnalyzed) {
      return (
        <tr>
          <td colSpan="4" className="empty">
            No mutations detected yet. Upload sequences above to get started.
          </td>
        </tr>
      );
    }

    if (mutations.length === 0) {
      return (
        <tr>
          <td colSpan="4" className="empty">
            Great news — no mutations were found. The sequences are identical.
          </td>
        </tr>
      );
    }

    if (paginatedMutations.length === 0) {
      return (
        <tr>
          <td colSpan="4" className="empty">
            No mutations match the "{typeFilter}" filter.
          </td>
        </tr>
      );
    }

    return paginatedMutations.map((mutation) => (
      <tr key={`${mutation.position}-${mutation.type}`}>
        <td>
          <span className={`mutation-type mutation-type--${mutation.type.toLowerCase()}`}>
            {mutation.type}
          </span>
        </td>
        <td>{mutation.position}</td>
        <td className="base">{mutation.original}</td>
        <td className="base">{mutation.mutated}</td>
      </tr>
    ));
  };

  const showControls = hasAnalyzed && !isLoading && !error && mutations.length > 0;

  return (
    <section id="results" className="section results-section">
      <div className="section-title">
        <h2>Mutation Results</h2>
        <p>Detailed information about detected mutations.</p>
      </div>

      <div className="result-summary">
        <div className="summary-card">
          <span>Total Mutations</span>
          <strong>{mutations.length}</strong>
        </div>
      </div>

      <MutationCharts
        mutations={filteredMutations}
        isLoading={isLoading}
        error={error}
        hasAnalyzed={hasAnalyzed}
        typeFilter={typeFilter}
      />

      <div className="mutation-box">
        <div className="mutation-header">
          <h3>Mutation Details</h3>
          <p>Detected mutation information</p>
        </div>

        {showControls && (
          <div className="controls-bar">
            <label className="control">
              Filter by type
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                {FILTER_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>

            <button className="sort-btn" onClick={toggleSortOrder}>
              Sort by Position: {sortOrder === "asc" ? "↑ Ascending" : "↓ Descending"}
            </button>

            <span className="result-count">
              Showing {paginatedMutations.length} of {sortedMutations.length} mutation(s)
            </span>
          </div>
        )}

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

            <tbody>{renderTableBody()}</tbody>
          </table>
        </div>

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

export default MutationResults;
