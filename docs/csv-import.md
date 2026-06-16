# Importing a project from CSV

BuildTrack can bulk-create a whole set of milestones and tasks from a single CSV
file. Each distinct **Milestone** value becomes a milestone owned by the
logged-in user, and each row becomes a **task** under that milestone.

A ready-to-use example lives at
[`data/Gerenciamento_execução_de_obra.csv`](../data/Gerenciamento_execução_de_obra.csv).

---

## Importing from the UI

> **You must be signed in first.** The import button is on the Dashboard, which
> is only shown to authenticated users. If you are not logged in you will see
> the Login page instead — register or sign in, and the Dashboard appears.

1. Open the app (http://localhost:3000 with the default Docker setup) and
   **log in** (or create an account).
2. On the **Dashboard** ("Build milestones"), look at the top-right corner.
   Next to **+ New milestone** there is an **Import CSV** button.
3. Click **Import CSV** and choose your `.csv` file.
4. While the file uploads the button reads **Importing…**. When it finishes, a
   message appears (e.g. *"Imported 16 milestones and 113 tasks."*) and the
   milestone list refreshes with the new data.

**Don't see the button?**
- Make sure you are **logged in** — it does not appear on the Login page.
- Do a hard refresh (`Ctrl/Cmd + Shift + R`) in case the browser cached an
  older build of the app.
- Confirm the frontend is up to date (`docker compose up -d --build frontend`).

---

## CSV format

- **Encoding:** UTF-8 (a byte-order mark / BOM is fine). Accented characters
  such as `Suíte master` are supported.
- **Line endings:** Windows (CRLF) or Unix (LF) both work.
- **Header row is required.** Column names are matched case-insensitively and
  surrounding spaces are ignored, so `Milestone` and `MIlestone ` both work.

### Columns

| Column              | Required | Format / notes                                                        |
| ------------------- | -------- | --------------------------------------------------------------------- |
| `Milestone`         | **Yes**  | Milestone name. Rows are grouped by this value.                       |
| `Task`              | **Yes**  | Task title.                                                           |
| `Description`       | No       | Free text.                                                            |
| `Completion`        | No       | `0`–`100`, with or without a `%` (e.g. `50%`). Defaults to `0`.       |
| `Mark as completed` | No       | Truthy values mark the task done: `x`, `yes`, `y`, `true`, `1`, `sim`, `done`, `completed`, `✓`. Anything else (incl. blank) is "not done". |
| `Start date`        | No       | `DD/MM/YYYY` (e.g. `15/06/2026`) or `YYYY-MM-DD`. Blank allowed.       |
| `End date`          | No       | Same formats as `Start date`.                                         |
| `Tags`              | No       | Separate multiple tags with a **semicolon** `;` (e.g. `outdoor;urgent`). Commas can't be used because they are the CSV column separator. |

### How values are interpreted

- **Grouping:** all rows sharing a `Milestone` name become one milestone; the
  order milestones first appear in the file is preserved.
- **Milestone dates:** a milestone has no dates of its own in the CSV — its
  start date is the **earliest** task start date and its end date is the
  **latest** task end date.
- **Completion vs. done:** if `Mark as completed` is truthy the task is forced
  to `100%` and stamped with today's completion date. Otherwise a `100%`
  completion is capped at `99%` so a task can't read as "done" without the flag.
- **Tags are global and shared** across all users. An imported tag name that
  already exists is reused rather than duplicated.
- **Skipped rows:** any row missing a `Milestone` **or** a `Task` value is
  ignored. A file with no usable rows is rejected.

### Minimal example

```csv
Milestone,Task,Description,Completion,Mark as completed,Start date,End date,Tags
Fachada,Cobogó,,0%,,15/06/2026,15/07/2026,
Fachada,Jardim,Front garden,50%,,16/06/2026,20/07/2026,outdoor;urgent
Cozinha,Fogão,,100%,x,01/06/2026,10/06/2026,
```

This creates two milestones (`Fachada` with 2 tasks, `Cozinha` with 1) and the
`outdoor` and `urgent` tags.

---

## Importing via the API (alternative)

The button calls `POST /api/import/csv` — a multipart file upload that requires
a bearer token. You can call it directly, e.g. with curl:

```bash
# 1. Get a token (register or log in)
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d 'username=you@example.com&password=yourpassword' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

# 2. Upload the CSV
curl -X POST http://localhost:8000/api/import/csv \
  -H "Authorization: Bearer $TOKEN" \
  -F 'file=@data/Gerenciamento_execução_de_obra.csv;type=text/csv'
```

A successful import returns the counts:

```json
{ "milestones_created": 16, "tasks_created": 113 }
```

You can also import interactively from the Swagger UI at
http://localhost:8000/docs — expand **POST /api/import/csv**, click
**Authorize** to paste your token, then **Try it out** and choose a file.

### Responses

| Status | Meaning                                                              |
| ------ | ------------------------------------------------------------------- |
| `201`  | Import succeeded; body contains `milestones_created` / `tasks_created`. |
| `400`  | The CSV is malformed (e.g. missing the `Milestone`/`Task` column, or no usable rows). The `detail` field explains what went wrong. |
| `401`  | Missing or invalid token — log in first.                            |

---

## Notes & limits

- Imported milestones and tasks belong to the **user who uploads them**; other
  users never see them.
- Each import **always creates new** milestones and tasks. It does not merge
  with or update milestones you already have, so importing the same file twice
  produces duplicates.
- The whole file is read into memory and created in one database transaction —
  fine for typical build checklists (hundreds of rows).
