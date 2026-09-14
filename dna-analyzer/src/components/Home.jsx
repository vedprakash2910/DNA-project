function Home() {
  return (
    <section id="home" className="hero">

      <div className="hero-content">

        <span className="badge">
          DNA MUTATION ANALYSIS
        </span>

        <h1>
          Analyze DNA Sequences
          <span>Quickly & Easily</span>
        </h1>

        <p>
          Compare reference and sample DNA sequences
          to identify mutations and view detailed
          mutation information.
        </p>

        <a
          href="#upload"
          className="primary-btn"
        >
          Start Analysis
        </a>

      </div>

    </section>
  );
}

export default Home;