from datetime import date, timedelta

from app.models import Milestone
from app.schemas import BurndownPoint, BurndownResponse


def milestone_progress(milestone: Milestone) -> float:
    """Average completion across tasks. A task marked completed counts as 100%."""
    tasks = milestone.tasks
    if not tasks:
        return 0.0
    total = 0
    for t in tasks:
        total += 100 if t.is_completed else t.completion
    return round(total / len(tasks), 1)


def build_burndown(milestone: Milestone) -> BurndownResponse:
    """
    Build a burndown of remaining tasks over time and project a finish date.

    Ideal line: linear from total_tasks at start_date to 0 at expected_end_date.
    Actual line: count of incomplete tasks at each day (using completed_at).
    Projection: based on the average completion velocity (tasks/day) so far,
    estimate when the remaining tasks will hit zero.
    """
    tasks = milestone.tasks
    total = len(tasks)
    today = date.today()

    start = milestone.start_date or today
    expected_end = milestone.expected_end_date

    points: list[BurndownPoint] = []
    projected_end: date | None = None
    on_track: bool | None = None

    if total == 0:
        return BurndownResponse(
            milestone_id=milestone.id,
            total_tasks=0,
            points=[],
            projected_end_date=None,
            expected_end_date=expected_end,
            on_track=None,
        )

    # End of the chart horizon
    horizon_end = max(today, expected_end or today, start)
    span_days = (horizon_end - start).days or 1

    # Completed dates for actual burndown
    completed_dates = sorted(
        [t.completed_at for t in tasks if t.is_completed and t.completed_at]
    )

    ideal_span = ((expected_end or horizon_end) - start).days or 1

    # Walk day by day
    d = start
    while d <= horizon_end:
        days_in = (d - start).days

        # Ideal remaining: linear down to 0 at expected_end
        if expected_end and d >= expected_end:
            ideal_remaining = 0.0
        else:
            ideal_remaining = max(
                0.0, total - (total * days_in / ideal_span)
            )

        # Actual remaining: tasks not yet completed as of day d
        completed_by_d = sum(1 for cd in completed_dates if cd <= d)
        actual_remaining = float(total - completed_by_d) if d <= today else None

        points.append(
            BurndownPoint(
                date=d,
                ideal_remaining=round(ideal_remaining, 2),
                actual_remaining=(
                    round(actual_remaining, 2)
                    if actual_remaining is not None
                    else round(ideal_remaining, 2)
                ),
            )
        )
        d += timedelta(days=1)

    # ---- Projection based on observed velocity ----
    completed_count = len(completed_dates)
    remaining = total - completed_count

    if remaining == 0:
        projected_end = completed_dates[-1] if completed_dates else today
    elif completed_count > 0:
        elapsed = (today - start).days or 1
        velocity = completed_count / elapsed  # tasks per day
        if velocity > 0:
            days_needed = remaining / velocity
            projected_end = today + timedelta(days=round(days_needed))
    else:
        projected_end = None

    if projected_end and expected_end:
        on_track = projected_end <= expected_end

    return BurndownResponse(
        milestone_id=milestone.id,
        total_tasks=total,
        points=points,
        projected_end_date=projected_end,
        expected_end_date=expected_end,
        on_track=on_track,
    )
