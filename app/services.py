"""Task business logic and database operations."""

from typing import Any

from app.database import get_db
from app.models import PRIORITIES, STATUSES, Task, ValidationError, validate_task_data


def create_task(data: Any) -> int:
    """Validate and persist a new task, returning its database ID."""
    task = validate_task_data(data)
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO tasks (title, description, priority, status, due_date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (task["title"], task["description"], task["priority"], task["status"], task["due_date"]),
    )
    db.commit()
    return int(cursor.lastrowid)


def update_task(task_id: int, data: Any) -> bool:
    """Validate and update a task; return whether a task with that ID existed."""
    task = validate_task_data(data)
    db = get_db()
    cursor = db.execute(
        """
        UPDATE tasks
        SET title = ?, description = ?, priority = ?, status = ?, due_date = ?
        WHERE id = ?
        """,
        (
            task["title"],
            task["description"],
            task["priority"],
            task["status"],
            task["due_date"],
            task_id,
        ),
    )
    db.commit()
    return cursor.rowcount > 0


def get_task(task_id: int) -> Task | None:
    """Find a task by ID, returning None when it does not exist."""
    row = get_db().execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return Task.from_row(row) if row is not None else None


def list_tasks(
    search: str = "", status: str = "", priority: str = ""
) -> list[Task]:
    """Return tasks matching optional search, status, and priority filters."""
    search = search.strip()
    status = status.strip().lower()
    priority = priority.strip().lower()
    if status and status not in STATUSES:
        raise ValidationError("Choose a valid status filter.")
    if priority and priority not in PRIORITIES:
        raise ValidationError("Choose a valid priority filter.")

    conditions: list[str] = []
    parameters: list[str] = []
    if search:
        conditions.append("(title LIKE ? OR description LIKE ?)")
        term = f"%{search}%"
        parameters.extend((term, term))
    if status:
        conditions.append("status = ?")
        parameters.append(status)
    if priority:
        conditions.append("priority = ?")
        parameters.append(priority)

    query = "SELECT * FROM tasks"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY CASE status WHEN 'pending' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END, "
    query += "CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, "
    query += "due_date IS NULL, due_date, id DESC"
    rows = get_db().execute(query, parameters).fetchall()
    return [Task.from_row(row) for row in rows]


def set_task_completed(task_id: int, completed: bool = True) -> bool:
    """Mark a task complete or reopen it; return whether it existed."""
    status = "completed" if completed else "pending"
    db = get_db()
    cursor = db.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    db.commit()
    return cursor.rowcount > 0


def delete_task(task_id: int) -> bool:
    """Delete a task and return whether it existed."""
    db = get_db()
    cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return cursor.rowcount > 0


def get_task_stats() -> dict[str, int]:
    """Calculate dashboard statistics directly from persisted task records."""
    row = get_db().execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) AS in_progress,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed
        FROM tasks
        """
    ).fetchone()
    return {key: int(row[key] or 0) for key in ("total", "pending", "in_progress", "completed")}
