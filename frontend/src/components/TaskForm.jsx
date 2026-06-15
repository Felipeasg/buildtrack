import { useEffect, useState } from "react";
import Modal from "./Modal";
import { createTag, listTags } from "../api";

export default function TaskForm({ initial, onSave, onClose }) {
  const [title, setTitle] = useState(initial?.title || "");
  const [description, setDescription] = useState(initial?.description || "");
  const [completion, setCompletion] = useState(initial?.completion ?? 0);
  const [isCompleted, setIsCompleted] = useState(initial?.is_completed || false);
  const [startDate, setStartDate] = useState(initial?.start_date || "");
  const [expectedEnd, setExpectedEnd] = useState(initial?.expected_end_date || "");
  const [tags, setTags] = useState([]);
  const [selectedTagIds, setSelectedTagIds] = useState(
    initial?.tags?.map((t) => t.id) || []
  );
  const [newTag, setNewTag] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    listTags().then((res) => setTags(res.data));
  }, []);

  const toggleTag = (id) =>
    setSelectedTagIds((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );

  const addTag = async () => {
    if (!newTag.trim()) return;
    const palette = ["#f5a524", "#4d8ef7", "#2dd4a7", "#f76d6d", "#a78bfa", "#f472b6"];
    const color = palette[tags.length % palette.length];
    const res = await createTag({ name: newTag.trim(), color });
    setTags((prev) => (prev.find((t) => t.id === res.data.id) ? prev : [...prev, res.data]));
    setSelectedTagIds((prev) => (prev.includes(res.data.id) ? prev : [...prev, res.data.id]));
    setNewTag("");
  };

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    await onSave({
      title,
      description,
      completion: Number(completion),
      is_completed: isCompleted,
      start_date: startDate || null,
      expected_end_date: expectedEnd || null,
      tag_ids: selectedTagIds,
    });
    setBusy(false);
  };

  return (
    <Modal title={initial ? "Edit task" : "New task"} onClose={onClose}>
      <form onSubmit={submit}>
        <div className="field">
          <label>Title</label>
          <input
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Run conduit for kitchen circuits"
          />
        </div>
        <div className="field">
          <label>Description</label>
          <textarea
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        <div className="field">
          <label>Completion — {completion}%</label>
          <input
            type="range"
            min={0}
            max={100}
            value={completion}
            disabled={isCompleted}
            onChange={(e) => setCompletion(e.target.value)}
          />
        </div>

        <div className="field">
          <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={isCompleted}
              onChange={(e) => setIsCompleted(e.target.checked)}
              style={{ width: 18, height: 18 }}
            />
            Mark as completed
          </label>
        </div>

        <div className="field-row">
          <div className="field">
            <label>Start date</label>
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div className="field">
            <label>Expected end</label>
            <input type="date" value={expectedEnd} onChange={(e) => setExpectedEnd(e.target.value)} />
          </div>
        </div>

        <div className="field">
          <label>Tags</label>
          <div className="tag-picker">
            {tags.map((t) => (
              <button
                type="button"
                key={t.id}
                className={`tag-pick ${selectedTagIds.includes(t.id) ? "active" : ""}`}
                style={selectedTagIds.includes(t.id) ? { color: t.color } : {}}
                onClick={() => toggleTag(t.id)}
              >
                {t.name}
              </button>
            ))}
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <input
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              placeholder="Add a new tag"
              onKeyDown={(e) => {
                if (e.key === "Enter") { e.preventDefault(); addTag(); }
              }}
            />
            <button type="button" className="btn btn-sm" onClick={addTag}>Add</button>
          </div>
        </div>

        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" disabled={busy}>
            {busy ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
