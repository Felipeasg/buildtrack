import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function fmtDate(d) {
  if (!d) return "—";
  return new Date(d + "T00:00:00").toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export default function Burndown({ data }) {
  if (!data || data.total_tasks === 0) {
    return (
      <div className="burndown-panel">
        <div className="empty" style={{ border: "none", padding: "30px 0" }}>
          Add tasks with dates to see the projection.
        </div>
      </div>
    );
  }

  const today = new Date().toISOString().slice(0, 10);
  const chartData = data.points.map((p) => ({
    date: fmtDate(p.date),
    raw: p.date,
    Ideal: p.ideal_remaining,
    Actual: p.date <= today ? p.actual_remaining : null,
  }));

  return (
    <div className="burndown-panel">
      <div className="projection-row">
        <div className="stat">
          <div className="k">Target finish</div>
          <div className="v">{fmtDate(data.expected_end_date)}</div>
        </div>
        <div className="stat">
          <div className="k">Projected finish</div>
          <div className={`v ${data.on_track === true ? "good" : data.on_track === false ? "bad" : ""}`}>
            {fmtDate(data.projected_end_date)}
          </div>
        </div>
        <div className="stat">
          <div className="k">Status</div>
          <div className={`v ${data.on_track === true ? "good" : data.on_track === false ? "bad" : ""}`}>
            {data.on_track === true ? "On track" : data.on_track === false ? "Behind" : "—"}
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData} margin={{ top: 6, right: 12, left: -8, bottom: 0 }}>
          <CartesianGrid stroke="#2a3744" strokeDasharray="3 3" />
          <XAxis dataKey="date" stroke="#8a9aa9" fontSize={11} tickMargin={8} minTickGap={28} />
          <YAxis stroke="#8a9aa9" fontSize={11} allowDecimals={false} label={{ value: "tasks left", angle: -90, position: "insideLeft", fill: "#8a9aa9", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: "#161d26", border: "1px solid #2a3744", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#e8edf2" }}
          />
          <Line type="monotone" dataKey="Ideal" stroke="#4d8ef7" strokeWidth={2} strokeDasharray="5 4" dot={false} />
          <Line type="monotone" dataKey="Actual" stroke="#34c759" strokeWidth={2.5} dot={false} connectNulls />
          <ReferenceLine x={fmtDate(today)} stroke="#2dd4a7" strokeDasharray="2 2" label={{ value: "today", fill: "#2dd4a7", fontSize: 10, position: "top" }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
