"""Pure parsing for the project-import CSV.

Expected columns (header names are matched case-insensitively, leading/trailing
space ignored): Milestone, Task, Description, Completion, Mark as completed,
Start date, End date, Tags. Rows are grouped by milestone in first-seen order;
each milestone's date range is derived from the min/max of its tasks' dates.

This module is intentionally DB-free so it can be unit-tested on raw bytes.
"""

import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime

REQUIRED_COLUMNS = {"milestone", "task"}
_TRUTHY = {"x", "yes", "y", "true", "1", "sim", "done", "completed", "✓"}
_DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")


@dataclass
class ParsedTask:
    title: str
    description: str = ""
    completion: int = 0
    is_completed: bool = False
    start_date: date | None = None
    expected_end_date: date | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class ParsedMilestone:
    name: str
    start_date: date | None = None
    expected_end_date: date | None = None
    tasks: list[ParsedTask] = field(default_factory=list)


def _parse_completion(value: str) -> int:
    value = (value or "").strip().rstrip("%").strip()
    if not value:
        return 0
    try:
        return max(0, min(100, int(float(value))))
    except ValueError:
        return 0


def _parse_bool(value: str) -> bool:
    return (value or "").strip().lower() in _TRUTHY


def _parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_tags(value: str) -> list[str]:
    # Comma is the CSV delimiter, so multiple tags in one cell use ';'.
    return [t.strip() for t in (value or "").split(";") if t.strip()]


def parse_build_csv(raw: bytes) -> list[ParsedMilestone]:
    """Parse CSV bytes into milestones with their tasks.

    Raises ValueError if required columns are missing or no usable rows exist.
    """
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV is empty")

    # Map normalised header -> actual key as it appears in each row dict.
    headers = {(name or "").strip().lower(): name for name in reader.fieldnames}
    missing = REQUIRED_COLUMNS - headers.keys()
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(sorted(missing))}")

    def cell(row: dict, key: str) -> str:
        return (row.get(headers.get(key, ""), "") or "").strip()

    milestones: dict[str, ParsedMilestone] = {}
    for row in reader:
        name = cell(row, "milestone")
        title = cell(row, "task")
        if not name or not title:
            continue  # skip blank/incomplete rows

        milestone = milestones.setdefault(name, ParsedMilestone(name=name))
        milestone.tasks.append(
            ParsedTask(
                title=title,
                description=cell(row, "description"),
                completion=_parse_completion(cell(row, "completion")),
                is_completed=_parse_bool(cell(row, "mark as completed")),
                start_date=_parse_date(cell(row, "start date")),
                expected_end_date=_parse_date(cell(row, "end date")),
                tags=_parse_tags(cell(row, "tags")),
            )
        )

    if not milestones:
        raise ValueError("No valid rows found in CSV")

    for milestone in milestones.values():
        starts = [t.start_date for t in milestone.tasks if t.start_date]
        ends = [t.expected_end_date for t in milestone.tasks if t.expected_end_date]
        milestone.start_date = min(starts) if starts else None
        milestone.expected_end_date = max(ends) if ends else None

    return list(milestones.values())
