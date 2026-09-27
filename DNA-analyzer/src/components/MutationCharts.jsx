import { useMemo, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

import {
  getTypeDistribution,
  getScatterData,
  getPositionDensity,
  TYPE_COLORS,
} from "../utils/chartData";

// Purpose of these charts (my part of the group project):
//
// The results table (MutationResult.jsx) is great for looking up one
// mutation at a time, but it doesn't answer "big picture" questions at a
// glance — e.g. "are most mutations substitutions or deletions?" or
// "do mutations cluster in one region of the sequence, or spread evenly?".
// That's exactly what a chart is for: trading row-by-row precision for a
// shape the eye can read in a second. So this component adds two charts
// on top of the same mutation data the table already has:
//   1. Mutation Type Distribution — how many of each mutation type
//      (Substitution / Insertion / Deletion), as a Bar or Pie chart.
//   2. Mutation Position Map — where mutations fall along the sequence,
//      as a Line (density-per-region) or Scatter (individual positions)
//      chart.
// Both charts read the *filtered* mutation list passed down from
// MutationResult.jsx, so switching the existing "Filter by type" control
// updates the table and the charts together — no separate filter UI needed.

const DISTRIBUTION_VIEWS = ["Bar", "Pie"];
const POSITION_VIEWS = ["Line", "Scatter"];

function ChartTypeToggle({ options, value, onChange, label }) {
  return (
    <div className="chart-toggle" role="group" aria-label={label}>
      {options.map((option) => (
        <button
          key={option}
          type="button"
          className={`chart-toggle-btn ${value === option ? "active" : ""}`}
          onClick={() => onChange(option)}
        >
          {option}
        </button>
      ))}
    </div>
  );
}

function DistributionTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { type, count, percentage } = payload[0].payload;

  return (
    <div className="chart-tooltip">
      <strong>{type}</strong>
      <span>
        {count} mutation{count === 1 ? "" : "s"} ({percentage}%)
      </span>
    </div>
  );
}

function PositionLineTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { label, count } = payload[0].payload;

  return (
    <div className="chart-tooltip">
      <strong>Position {label} bp</strong>
      <span>
        {count} mutation{count === 1 ? "" : "s"}
      </span>
    </div>
  );
}

function PositionScatterTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { type, position, original, mutated } = payload[0].payload;

  return (
    <div className="chart-tooltip">
      <strong>{type}</strong>
      <span>
        Position {position} bp: {original} &rarr; {mutated}
      </span>
    </div>
  );
}

function EmptyChart({ message }) {
  return <div className="chart-empty">{message}</div>;
}

function MutationCharts({ mutations, isLoading, error, hasAnalyzed, typeFilter }) {
  const [distributionView, setDistributionView] = useState("Bar");
  const [positionView, setPositionView] = useState("Line");

  // --- Transform the raw mutation list into chart-ready data -------------
  // (kept in utils/chartData.js so the shape isn't re-derived per chart)
  const distributionData = useMemo(() => getTypeDistribution(mutations), [mutations]);
  const scatterData = useMemo(() => getScatterData(mutations), [mutations]);
  const densityData = useMemo(() => getPositionDensity(mutations), [mutations]);

  const hasChartableData = distributionData.some((d) => d.count > 0);

  // --- Empty / invalid data handling --------------------------------------
  // A chart with no data (or a container still mid-request, or a failed
  // request) is worse than no chart at all — Recharts will happily render
  // empty axes, which reads as broken rather than "nothing here yet". So
  // every non-normal state gets an explicit message instead of a blank
  // plot.
  let emptyMessage = null;
  if (isLoading) {
    emptyMessage = "Analyzing sequences...";
  } else if (error) {
    emptyMessage = error;
  } else if (!hasAnalyzed) {
    emptyMessage = "Charts will appear here once you analyze a sequence pair.";
  } else if (!hasChartableData) {
    emptyMessage =
      typeFilter && typeFilter !== "All"
        ? `No "${typeFilter}" mutations to chart.`
        : "No mutations detected — nothing to chart.";
  }

  const filterNote =
    typeFilter && typeFilter !== "All" ? ` (filtered: ${typeFilter})` : "";

  return (
    <div className="charts-grid">
      {/* ---- Chart 1: Mutation Type Distribution ---- */}
      <div className="mutation-box chart-card">
        <div className="mutation-header charts-header">
          <div>
            <h3>Mutation Type Distribution</h3>
            <p>Share of mutations by type{filterNote}</p>
          </div>

          {!emptyMessage && (
            <ChartTypeToggle
              label="Distribution chart type"
              options={DISTRIBUTION_VIEWS}
              value={distributionView}
              onChange={setDistributionView}
            />
          )}
        </div>

        <div className="chart-body">
          {emptyMessage ? (
            <EmptyChart message={emptyMessage} />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              {distributionView === "Bar" ? (
                <BarChart data={distributionData} margin={{ top: 10, right: 16, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#23262f" vertical={false} />
                  <XAxis dataKey="type" stroke="#94a3b8" tick={{ fontSize: 13 }} />
                  <YAxis
                    stroke="#94a3b8"
                    allowDecimals={false}
                    tick={{ fontSize: 13 }}
                    label={{ value: "Mutations", angle: -90, position: "insideLeft", fill: "#94a3b8" }}
                  />
                  <Tooltip content={<DistributionTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {distributionData.map((entry) => (
                      <Cell key={entry.type} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              ) : (
                <PieChart>
                  <Tooltip content={<DistributionTooltip />} />
                  <Legend />
                  <Pie
                    data={distributionData.filter((d) => d.count > 0)}
                    dataKey="count"
                    nameKey="type"
                    innerRadius={55}
                    outerRadius={95}
                    paddingAngle={3}
                    label={({ type, percentage }) => `${type} ${percentage}%`}
                    labelLine={false}
                  >
                    {distributionData
                      .filter((d) => d.count > 0)
                      .map((entry) => (
                        <Cell key={entry.type} fill={entry.fill} />
                      ))}
                  </Pie>
                </PieChart>
              )}
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ---- Chart 2: Mutation Position Map ---- */}
      <div className="mutation-box chart-card">
        <div className="mutation-header charts-header">
          <div>
            <h3>Mutation Position Map</h3>
            <p>Where mutations fall along the sequence (base-pair position){filterNote}</p>
          </div>

          {!emptyMessage && (
            <ChartTypeToggle
              label="Position chart type"
              options={POSITION_VIEWS}
              value={positionView}
              onChange={setPositionView}
            />
          )}
        </div>

        <div className="chart-body">
          {emptyMessage ? (
            <EmptyChart message={emptyMessage} />
          ) : positionView === "Line" ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={densityData} margin={{ top: 10, right: 16, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#23262f" vertical={false} />
                <XAxis
                  dataKey="label"
                  stroke="#94a3b8"
                  tick={{ fontSize: 11 }}
                  interval="preserveStartEnd"
                  label={{ value: "Position (bp)", position: "insideBottom", offset: -12, fill: "#94a3b8" }}
                />
                <YAxis
                  stroke="#94a3b8"
                  allowDecimals={false}
                  tick={{ fontSize: 13 }}
                  label={{ value: "Mutations", angle: -90, position: "insideLeft", fill: "#94a3b8" }}
                />
                <Tooltip content={<PositionLineTooltip />} cursor={{ stroke: "#5eeada", strokeWidth: 1 }} />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#5eeada"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: "#5eeada" }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <ScatterChart margin={{ top: 10, right: 16, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#23262f" />
                <XAxis
                  type="number"
                  dataKey="position"
                  name="Position"
                  stroke="#94a3b8"
                  tick={{ fontSize: 13 }}
                  label={{ value: "Position (bp)", position: "insideBottom", offset: -12, fill: "#94a3b8" }}
                />
                <YAxis
                  type="number"
                  dataKey="y"
                  name="Type"
                  stroke="#94a3b8"
                  tick={false}
                  width={20}
                  domain={[-0.5, 2.5]}
                  axisLine={false}
                />
                <ZAxis range={[70, 70]} />
                <Tooltip content={<PositionScatterTooltip />} cursor={{ strokeDasharray: "3 3" }} />
                <Legend
                  payload={Object.entries(TYPE_COLORS).map(([type, color]) => ({
                    value: type,
                    type: "circle",
                    color,
                  }))}
                />
                {Object.entries(TYPE_COLORS).map(([type, color]) => (
                  <Scatter
                    key={type}
                    name={type}
                    data={scatterData.filter((point) => point.type === type)}
                    fill={color}
                  />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}

export default MutationCharts;
