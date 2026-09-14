function MutationResults({ mutations }) {

  return (
    <section
      id="results"
      className="section results-section"
    >

      <div className="section-title">

        <span>02</span>

        <h2>
          Mutation Results
        </h2>

        <p>
          Detailed information about detected mutations.
        </p>

      </div>


      <div className="result-summary">

        <div className="summary-card">

          <span>
            Total Mutations
          </span>

          <strong>
            {mutations.length}
          </strong>

        </div>

      </div>


      <div className="mutation-box">

        <div className="mutation-header">

          <h3>
            Mutation Details
          </h3>

          <p>
            Detected mutation information
          </p>

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

              {mutations.length === 0 ? (

                <tr>

                  <td
                    colSpan="4"
                    className="empty"
                  >
                    No mutations detected yet.
                  </td>

                </tr>

              ) : (

                mutations.map((mutation, index) => (

                  <tr key={index}>

                    <td>
                      <span className="mutation-type">
                        {mutation.type}
                      </span>
                    </td>

                    <td>
                      {mutation.position}
                    </td>

                    <td className="base">
                      {mutation.original}
                    </td>

                    <td className="base">
                      {mutation.mutated}
                    </td>

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

export default MutationResults;