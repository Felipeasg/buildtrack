import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createMilestone, listMilestones } from "../api";
import MilestoneForm from "../components/MilestoneForm";

function fmt(d) {
  if (!d) return "—";
  return new Date(d + "T00:00:00").toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [milestones, setMilestones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const load = () =>
    listMilestones().then((res) => {
      setMilestones(res.data);
      setLoading(false);
    });

  useEffect(() => { load(); }, []);

  const handleCreate = async (data) => {
    await createMilestone(data);
    setShowForm(false);
    load();
  };

  const overall = milestones.length
    ? Math.round(milestones.reduce((s, m) => s + m.progress, 0) / milestones.length)
    : 0;

  return (
    <div className="container">
      <div className="page-head">
        <div>
          <div className="eyebrow">Site overview</div>
          <h1>Build milestones</h1>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + New milestone
        </button>
      </div>

      {!loading && milestones.length > 0 && (
        <div className="card" style={{ marginBottom: 26 }}>
          <div className="progress-head">
            <span className="progress-label">Whole-house completion</span>
            <span className="progress-pct">{overall}%</span>
          </div>
          <div className={`bar ${overall >= 100 ? "done" : ""}`}>
            <span style={{ width: `${overall}%` }} />
          </div>
        </div>
      )}

      {loading ? (
        <p style={{ color: "var(--muted)" }}>Loading…</p>
      ) : milestones.length === 0 ? (
        <div className="empty">
          <h2>No milestones yet</h2>
          <p>Start by adding a stage of the build — like electrical, plumbing, or framing.</p>
        </div>
      ) : (
        <div className="milestone-grid">
          {milestones.map((m) => (
            <div
              key={m.id}
              className="card clickable"
              onClick={() => navigate(`/milestones/${m.id}`)}
            >
              <div className="card-top">
                <div>
                  <h2>{m.name}</h2>
                </div>
              </div>
              <p className="desc">{m.description || "No description"}</p>

              <div className="progress-wrap">
                <div className="progress-head">
                  <span className="progress-label">
                    {m.tasks.filter((t) => t.is_completed).length}/{m.tasks.length} tasks done
                  </span>
                  <span className="progress-pct">{Math.round(m.progress)}%</span>
                </div>
                <div className={`bar ${m.progress >= 100 ? "done" : ""}`}>
                  <span style={{ width: `${m.progress}%` }} />
                </div>
              </div>

              <div className="dates-row">
                <span>START <b>{fmt(m.start_date)}</b></span>
                <span>TARGET <b>{fmt(m.expected_end_date)}</b></span>
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <MilestoneForm onSave={handleCreate} onClose={() => setShowForm(false)} />
      )}
    </div>
  );
}
