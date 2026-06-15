import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  createTask,
  deleteMilestone,
  deleteTask,
  getBurndown,
  getMilestone,
  updateMilestone,
  updateTask,
} from "../api";
import Burndown from "../components/Burndown";
import MilestoneForm from "../components/MilestoneForm";
import TaskForm from "../components/TaskForm";

function fmt(d) {
  if (!d) return "—";
  return new Date(d + "T00:00:00").toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export default function MilestoneDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [milestone, setMilestone] = useState(null);
  const [burndown, setBurndown] = useState(null);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [editingMilestone, setEditingMilestone] = useState(false);

  const load = useCallback(async () => {
    const [m, b] = await Promise.all([getMilestone(id), getBurndown(id)]);
    setMilestone(m.data);
    setBurndown(b.data);
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const toggleTask = async (task) => {
    await updateTask(task.id, { is_completed: !task.is_completed });
    load();
  };

  const saveTask = async (data) => {
    if (editingTask) {
      await updateTask(editingTask.id, data);
    } else {
      await createTask(id, data);
    }
    setShowTaskForm(false);
    setEditingTask(null);
    load();
  };

  const removeTask = async (taskId) => {
    if (confirm("Delete this task?")) {
      await deleteTask(taskId);
      load();
    }
  };

  const saveMilestone = async (data) => {
    await updateMilestone(id, data);
    setEditingMilestone(false);
    load();
  };

  const removeMilestone = async () => {
    if (confirm("Delete this milestone and all its tasks?")) {
      await deleteMilestone(id);
      navigate("/");
    }
  };

  if (!milestone) return <div className="container"><p style={{ color: "var(--muted)" }}>Loading…</p></div>;

  return (
    <div className="container">
      <a className="back-link" onClick={() => navigate("/")}>← All milestones</a>

      <div className="page-head">
        <div>
          <div className="eyebrow">Milestone</div>
          <h1>{milestone.name}</h1>
          {milestone.description && (
            <p style={{ color: "var(--muted)", marginTop: 6, maxWidth: 600 }}>{milestone.description}</p>
          )}
          <div className="dates-row" style={{ marginTop: 12 }}>
            <span>START <b>{fmt(milestone.start_date)}</b></span>
            <span>TARGET <b>{fmt(milestone.expected_end_date)}</b></span>
          </div>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-sm" onClick={() => setEditingMilestone(true)}>Edit</button>
          <button className="btn btn-sm btn-danger" onClick={removeMilestone}>Delete</button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 8 }}>
        <div className="progress-head">
          <span className="progress-label">
            {milestone.tasks.filter((t) => t.is_completed).length}/{milestone.tasks.length} tasks complete
          </span>
          <span className="progress-pct">{Math.round(milestone.progress)}%</span>
        </div>
        <div className={`bar ${milestone.progress >= 100 ? "done" : ""}`}>
          <span style={{ width: `${milestone.progress}%` }} />
        </div>
      </div>

      <div className="section-divider">Burndown &amp; projection</div>
      <Burndown data={burndown} />

      <div className="section-divider">Tasks</div>
      <div style={{ marginBottom: 16 }}>
        <button className="btn btn-primary btn-sm" onClick={() => { setEditingTask(null); setShowTaskForm(true); }}>
          + Add task
        </button>
      </div>

      {milestone.tasks.length === 0 ? (
        <div className="empty">
          <h2>No tasks yet</h2>
          <p>Break this stage into trackable tasks.</p>
        </div>
      ) : (
        <div className="task-list">
          {milestone.tasks.map((task) => (
            <div key={task.id} className={`task-row ${task.is_completed ? "done" : ""}`}>
              <input
                type="checkbox"
                className="task-check"
                checked={task.is_completed}
                onChange={() => toggleTask(task)}
              />
              <div className="task-main">
                <div className="task-title">{task.title}</div>
                <div className="task-meta">
                  <span className="task-completion">{task.is_completed ? 100 : task.completion}%</span>
                  <div className="mini-bar">
                    <span style={{ width: `${task.is_completed ? 100 : task.completion}%` }} />
                  </div>
                  {task.tags.map((t) => (
                    <span key={t.id} className="tag" style={{ color: t.color, borderColor: t.color, background: t.color + "18" }}>
                      {t.name}
                    </span>
                  ))}
                </div>
              </div>
              <button className="btn btn-sm btn-ghost" onClick={() => { setEditingTask(task); setShowTaskForm(true); }}>Edit</button>
              <button className="btn btn-sm btn-ghost btn-danger" onClick={() => removeTask(task.id)}>✕</button>
            </div>
          ))}
        </div>
      )}

      {showTaskForm && (
        <TaskForm
          initial={editingTask}
          onSave={saveTask}
          onClose={() => { setShowTaskForm(false); setEditingTask(null); }}
        />
      )}
      {editingMilestone && (
        <MilestoneForm
          initial={milestone}
          onSave={saveMilestone}
          onClose={() => setEditingMilestone(false)}
        />
      )}
    </div>
  );
}
