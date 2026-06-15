import { useState } from "react";
import Modal from "./Modal";

export default function MilestoneForm({ initial, onSave, onClose }) {
  const [name, setName] = useState(initial?.name || "");
  const [description, setDescription] = useState(initial?.description || "");
  const [startDate, setStartDate] = useState(initial?.start_date || "");
  const [expectedEnd, setExpectedEnd] = useState(initial?.expected_end_date || "");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    await onSave({
      name,
      description,
      start_date: startDate || null,
      expected_end_date: expectedEnd || null,
    });
    setBusy(false);
  };

  return (
    <Modal title={initial ? "Edit milestone" : "New milestone"} onClose={onClose}>
      <form onSubmit={submit}>
        <div className="field">
          <label>Name</label>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Electrical rough-in"
          />
        </div>
        <div className="field">
          <label>Description</label>
          <textarea
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Wiring, panel, outlets and fixtures for the ground floor"
          />
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
