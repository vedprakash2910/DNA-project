import { useMemo } from "react";

const HELIX_WIDTH = 200;
const HELIX_HEIGHT = 420;
const STEPS = 40;
const TWISTS = 2;

// Builds the point coordinates for a simple two-strand DNA helix as plain
// numbers, so the SVG below can just map over arrays instead of hard-coding
// dozens of hand-picked coordinates.
function buildHelix() {
  const strandA = [];
  const strandB = [];
  const rungs = [];

  const amplitude = HELIX_WIDTH / 2 - 14;
  const centerX = HELIX_WIDTH / 2;

  for (let i = 0; i <= STEPS; i++) {
    const y = (i / STEPS) * HELIX_HEIGHT;
    const theta = (i / STEPS) * Math.PI * 2 * TWISTS;

    const xA = centerX + amplitude * Math.sin(theta);
    const xB = centerX - amplitude * Math.sin(theta);

    strandA.push([xA, y]);
    strandB.push([xB, y]);

    if (i % 4 === 0) {
      rungs.push({ x1: xA, y1: y, x2: xB, y2: y, front: Math.sin(theta) > 0 });
    }
  }

  return { strandA, strandB, rungs };
}

function DnaHelix() {
  const { strandA, strandB, rungs } = useMemo(() => buildHelix(), []);

  const toPoints = (strand) =>
    strand.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");

  return (
    <svg
      viewBox={`0 0 ${HELIX_WIDTH} ${HELIX_HEIGHT}`}
      className="dna-helix"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="strandGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#88ff3d" />
          <stop offset="100%" stopColor="#5eeada" />
        </linearGradient>
      </defs>

      {rungs.map((r, i) => (
        <line
          key={`rung-${i}`}
          x1={r.x1}
          y1={r.y1}
          x2={r.x2}
          y2={r.y2}
          stroke="#2b2f3a"
          strokeWidth="2"
          opacity={r.front ? 0.9 : 0.35}
        />
      ))}

      <polyline
        points={toPoints(strandB)}
        fill="none"
        stroke="url(#strandGradient)"
        strokeWidth="4"
        strokeLinecap="round"
        opacity="0.55"
      />

      <polyline
        points={toPoints(strandA)}
        fill="none"
        stroke="url(#strandGradient)"
        strokeWidth="4"
        strokeLinecap="round"
      />

      {strandA
        .filter((_, i) => i % 4 === 0)
        .map(([x, y], i) => (
          <circle key={`a-${i}`} cx={x} cy={y} r="4" fill="#88ff3d" />
        ))}

      {strandB
        .filter((_, i) => i % 4 === 0)
        .map(([x, y], i) => (
          <circle key={`b-${i}`} cx={x} cy={y} r="4" fill="#5eeada" opacity="0.7" />
        ))}
    </svg>
  );
}

function MiniChart() {
  const values = [4, 7, 5, 9, 6, 11, 8, 13];
  const max = Math.max(...values);

  const points = values
    .map((v, i) => `${(i / (values.length - 1)) * 100},${40 - (v / max) * 34}`)
    .join(" ");

  return (
    <svg viewBox="0 0 100 40" className="mini-chart" width="100%" height="40">
      <polyline
        points={points}
        fill="none"
        stroke="#5eeada"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

const FEATURES = [
  {
    title: "Sequence Analysis",
    subtitle: "Quick & accurate",
    color: "#88ff3d",
    icon: (
      <path d="M12 2v20M2 12h20M6 6l12 12M18 6L6 18" strokeLinecap="round" />
    ),
  },
  {
    title: "Mutation Detection",
    subtitle: "Identify genetic variations",
    color: "#5eeada",
    icon: <path d="M12 2l7 4v6c0 5-3 8-7 10-4-2-7-5-7-10V6l7-4z" strokeLinecap="round" strokeLinejoin="round" />,
  },
  {
    title: "Visual Insights",
    subtitle: "Interactive results",
    color: "#a788fa",
    icon: (
      <>
        <path d="M4 20V10M12 20V4M20 20v-7" strokeLinecap="round" />
      </>
    ),
  },
  {
    title: "Runs Locally",
    subtitle: "Your data never leaves the page",
    color: "#88ff3d",
    icon: (
      <>
        <rect x="5" y="11" width="14" height="10" rx="2" />
        <path d="M8 11V7a4 4 0 0 1 8 0v4" strokeLinecap="round" />
      </>
    ),
  },
];

function Home({ onNavigate, hasAnalyzed, isLoading, mutationCount }) {
  return (
    <>
      <section id="home" className="hero">
        <div className="hero-inner">
          <div className="hero-content">
            <h1>
              Analyze DNA Sequences
              <span className="line-accent">Quickly &amp; Easily</span>
            </h1>

            <p>
              Compare a reference and a sample DNA sequence to identify
              mutations and view detailed, position-by-position results.
            </p>

            <div className="hero-actions">
              <button
                type="button"
                className="primary-btn"
                onClick={() => onNavigate("upload")}
              >
                Get Started →
              </button>

              <button
                type="button"
                className="secondary-btn"
                onClick={() => onNavigate("results")}
              >
                Learn More
              </button>
            </div>
          </div>

          <div className="hero-visual">
            <DnaHelix />

            <div className="floating-card">
              <h4>Sequence Overview</h4>

              <div className="sequence-strip">
                {"ATGCTAC".split("").map((base, i) => (
                  <span key={i}>{base}</span>
                ))}
              </div>

              {isLoading ? (
                <span className="status-pill pulse">
                  <span className="dot" />
                  Analyzing...
                </span>
              ) : (
                <span className="status-pill">
                  <span className="dot" />
                  {hasAnalyzed ? "Analysis complete" : "Awaiting sequence"}
                </span>
              )}

              <MiniChart />

              {hasAnalyzed && !isLoading && (
                <span
                  className={
                    mutationCount > 0 ? "result-pill found" : "result-pill clear"
                  }
                >
                  <span className="dot" />
                  {mutationCount > 0
                    ? `${mutationCount} Mutation${mutationCount === 1 ? "" : "s"} Found`
                    : "No Mutation Found"}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="feature-strip">
          {FEATURES.map((feature) => (
            <div className="feature-item" key={feature.title}>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke={feature.color}
                strokeWidth="1.8"
              >
                {feature.icon}
              </svg>

              <div>
                <h4>{feature.title}</h4>
                <p>{feature.subtitle}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

export default Home;
