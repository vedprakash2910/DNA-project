function History({ history, onClear }) {

  return (
    <section
      id="history"
      className="section"
    >

      <div className="section-title">

        <h2>
          History / Reports
        </h2>

        <p>
          Previous DNA mutation analysis reports.
        </p>

      </div>


      <div className="history-box">

        <div className="history-header">

          <h3>
            Analysis History
          </h3>

          <button
            className="clear-btn"
            onClick={onClear}
          >
            Clear History
          </button>

        </div>


        {history.length === 0 ? (

          <div className="no-history">
            No previous reports available.
          </div>

        ) : (

          history.map((report) => (

            <div
              className="history-item"
              key={report.id}
            >

              <div>

                <h4>
                  DNA Mutation Analysis
                </h4>

                <p>
                  {report.date}
                  {" | "}
                  Reference: {report.referenceLength} bases
                  {" | "}
                  Sample: {report.sampleLength} bases
                </p>

              </div>

              <div className="history-count">

                {report.mutationCount}
                {" mutation(s)"}

              </div>

            </div>

          ))

        )}

      </div>

    </section>
  );
}

export default History;