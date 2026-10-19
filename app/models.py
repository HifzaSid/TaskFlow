"""Task data model and validation helpers."""

from dataclasses import dataclass
from datetime import date
from typing import Any


PRIORITIES = ("low", "medium", "high")
STATUSES = ("pending", "in_progress", "completed")
MAX_TITLE_LENGTH = 120
MAX_DESCRIPTION_LENGTH = 1000


class ValidationError(ValueError):
    """Raised when submitted task data does not meet application rules."""


@dataclass(frozen=True)
class Task:
    """A task as stored in the database."""

    id: int
    title: str
    description: str
    priority: str
    status: str
    due_date: str | None
    created_at: str

    @classmethod
    def from_row(cls, row: Any) -> "Task":
        """Convert a SQLite row into a typed task object."""
        return cls(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            priority=row["priority"],
            status=row["status"],
            due_date=row["due_date"],
            created_at=row["created_at"],
        )


def validate_task_data(data: Any) -> dict[str, str | None]:
    """Normalize and validate fields used to create or update a task."""
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    priority = str(data.get("priority", "medium")).strip().lower()
    status = str(data.get("status", "pending")).strip().lower()
    due_date = str(data.get("due_date", "")).strip()

    if not title:
        raise ValidationError("A task title is required.")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError(f"Task titles must be {MAX_TITLE_LENGTH} characters or fewer.")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(
            f"Descriptions must be {MAX_DESCRIPTION_LENGTH} characters or fewer."
        )
    if priority not in PRIORITIES:
        raise ValidationError("Choose a valid priority.")
    if status not in STATUSES:
        raise ValidationError("Choose a valid status.")
    if due_date:
        try:
            date.fromisoformat(due_date)
        except ValueError as error:
            raise ValidationError("Enter a valid due date.") from error
    else:
        due_date = None

    return {
        "title": title,
        "description": description,
        "priority": priority,
        "status": status,
        "due_date": due_date,
    }
