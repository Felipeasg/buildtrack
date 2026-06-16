"""Unit tests for the pure CSV parser and integration tests for the
/api/import/csv endpoint."""

from datetime import date

import pytest

from app.core.csv_import import parse_build_csv

# Mirrors the real file: BOM-less utf-8 with CRLF, DD/MM/YYYY dates, '%' suffix.
SAMPLE = (
    "Milestone,Task,Description,Completion,Mark as completed,Start date,End date,Tags\r\n"
    "Fachada,Cobogó,,0%,,15/06/2026,15/07/2026,\r\n"
    "Fachada,Jardim,Front garden,50%,,16/06/2026,20/07/2026,outdoor;urgent\r\n"
    "Cozinha,Fogão,,100%,x,01/06/2026,10/06/2026,\r\n"
).encode("utf-8")


# ---------- parser unit tests ----------
def test_parse_groups_by_milestone_in_order():
    milestones = parse_build_csv(SAMPLE)
    assert [m.name for m in milestones] == ["Fachada", "Cozinha"]
    assert len(milestones[0].tasks) == 2
    assert len(milestones[1].tasks) == 1


def test_parse_task_fields():
    fachada = parse_build_csv(SAMPLE)[0]
    jardim = fachada.tasks[1]
    assert jardim.title == "Jardim"
    assert jardim.description == "Front garden"
    assert jardim.completion == 50
    assert jardim.is_completed is False
    assert jardim.start_date == date(2026, 6, 16)
    assert jardim.expected_end_date == date(2026, 7, 20)
    assert jardim.tags == ["outdoor", "urgent"]


def test_parse_completed_flag():
    fogao = parse_build_csv(SAMPLE)[1].tasks[0]
    assert fogao.is_completed is True
    assert fogao.completion == 100


def test_milestone_date_range_from_tasks():
    fachada = parse_build_csv(SAMPLE)[0]
    assert fachada.start_date == date(2026, 6, 15)  # min of task starts
    assert fachada.expected_end_date == date(2026, 7, 20)  # max of task ends


def test_blank_rows_skipped():
    raw = (
        "Milestone,Task,Start date,End date\r\n"
        "Sala,,,\r\n"  # missing task -> skipped
        ",Orphan,,\r\n"  # missing milestone -> skipped
        "Sala,Sofá,,\r\n"
    ).encode("utf-8")
    milestones = parse_build_csv(raw)
    assert len(milestones) == 1 and len(milestones[0].tasks) == 1


def test_missing_required_column_raises():
    with pytest.raises(ValueError, match="Missing required column"):
        parse_build_csv(b"Task,Description\r\nFoo,bar\r\n")


def test_no_rows_raises():
    with pytest.raises(ValueError, match="No valid rows"):
        parse_build_csv(b"Milestone,Task\r\n")


# ---------- endpoint integration tests ----------
def _upload(client, token, content=SAMPLE, filename="build.csv"):
    return client.post(
        "/api/import/csv",
        files={"file": (filename, content, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_import_requires_auth(client):
    res = client.post(
        "/api/import/csv", files={"file": ("build.csv", SAMPLE, "text/csv")}
    )
    assert res.status_code == 401


def test_import_creates_milestones_and_tasks(client, auth_token):
    res = _upload(client, auth_token)
    assert res.status_code == 201, res.text
    assert res.json() == {"milestones_created": 2, "tasks_created": 3}

    # Imported data is visible through the normal milestones API.
    listed = client.get(
        "/api/milestones", headers={"Authorization": f"Bearer {auth_token}"}
    ).json()
    names = {m["name"] for m in listed}
    assert {"Fachada", "Cozinha"} <= names


def test_import_applies_completion_invariant(client, auth_token):
    _upload(client, auth_token)
    listed = client.get(
        "/api/milestones", headers={"Authorization": f"Bearer {auth_token}"}
    ).json()
    cozinha = next(m for m in listed if m["name"] == "Cozinha")
    fogao = cozinha["tasks"][0]
    assert fogao["is_completed"] is True
    assert fogao["completion"] == 100
    assert fogao["completed_at"] is not None  # stamped by _sync_completion


def test_import_creates_shared_tags(client, auth_token):
    _upload(client, auth_token)
    tags = client.get(
        "/api/tags", headers={"Authorization": f"Bearer {auth_token}"}
    ).json()
    assert {"outdoor", "urgent"} <= {t["name"] for t in tags}


def test_import_scoped_to_owner(client, auth_token):
    _upload(client, auth_token)
    other = client.post(
        "/api/auth/register",
        json={"email": "other@example.com", "password": "secret123", "full_name": "O"},
    ).json()["access_token"]
    listed = client.get(
        "/api/milestones", headers={"Authorization": f"Bearer {other}"}
    ).json()
    assert listed == []


def test_import_rejects_bad_csv(client, auth_token):
    res = _upload(client, auth_token, content=b"Task,Description\r\nFoo,bar\r\n")
    assert res.status_code == 400
    assert "Missing required column" in res.json()["detail"]
