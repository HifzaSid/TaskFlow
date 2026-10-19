"""Tests for TaskFlow's task workflows and HTTP routes."""

from datetime import date, timedelta

import pytest

from app.database import get_db
from app.models import ValidationError
from app.services import (
    create_task,
    delete_task,
    get_task,
    get_task_stats,
    list_tasks,
    set_task_completed,
    update_task,
)


def task_data(**overrides):
    values = {
        "title": "Write the project brief",
        "description": "Collect the key requirements",
        "priority": "high",
        "status": "pending",
        "due_date": "",
    }
    values.update(overrides)
    return values


def test_create_task_and_database_persistence(app):
    with app.app_context():
        task_id = create_task(task_data(due_date=date.today().isoformat()))
        task = get_task(task_id)
        assert task is not None
        assert task.title == "Write the project brief"
        assert task.priority == "high"
        assert task.due_date == date.today().isoformat()

    with app.app_context():
        assert get_task(task_id).description == "Collect the key requirements"


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (task_data(title="  "), "title is required"),
        (task_data(title="x" * 121), "120 characters or fewer"),
        (task_data(description="x" * 1001), "1000 characters or fewer"),
        (task_data(priority="urgent"), "valid priority"),
        (task_data(status="blocked"), "valid status"),
        (task_data(due_date="tomorrow"), "valid due date"),
    ],
)
def test_create_task_rejects_invalid_data(app, data, message):
    with app.app_context(), pytest.raises(ValidationError, match=message):
        create_task(data)


def test_update_task_changes_all_editable_fields(app):
    with app.app_context():
        task_id = create_task(task_data())
        updated = task_data(
            title="Publish the project brief",
            description="Share with the whole team",
            priority="medium",
            status="in_progress",
            due_date=(date.today() + timedelta(days=2)).isoformat(),
        )
        assert update_task(task_id, updated)
        task = get_task(task_id)
        assert task.title == "Publish the project brief"
        assert task.description == "Share with the whole team"
        assert task.priority == "medium"
        assert task.status == "in_progress"
        assert task.due_date == updated["due_date"]
        assert not update_task(999, updated)


def test_completion_can_be_reopened(app):
    with app.app_context():
        task_id = create_task(task_data())
        assert set_task_completed(task_id)
        assert get_task(task_id).status == "completed"
        assert set_task_completed(task_id, completed=False)
        assert get_task(task_id).status == "pending"
        assert not set_task_completed(999)


def test_delete_task(app):
    with app.app_context():
        task_id = create_task(task_data())
        assert delete_task(task_id)
        assert get_task(task_id) is None
        assert not delete_task(task_id)


def test_search_and_status_priority_filters(app):
    with app.app_context():
        create_task(task_data(title="Prepare launch", description="Draft the announcement"))
        create_task(task_data(title="Review budget", priority="low", status="in_progress"))
        create_task(task_data(title="Launch follow-up", status="completed"))

        assert [task.title for task in list_tasks(search="launch")] == [
            "Prepare launch",
            "Launch follow-up",
        ]
        assert [task.title for task in list_tasks(search="announcement")] == ["Prepare launch"]
        assert [task.title for task in list_tasks(status="in_progress")] == ["Review budget"]
        assert [task.title for task in list_tasks(priority="low")] == ["Review budget"]
        assert [task.title for task in list_tasks(status="completed", priority="high")] == [
            "Launch follow-up"
        ]
        with pytest.raises(ValidationError, match="valid status filter"):
            list_tasks(status="unknown")


def test_statistics_are_calculated_from_database_records(app):
    with app.app_context():
        create_task(task_data())
        create_task(task_data(title="Research options", status="in_progress"))
        create_task(task_data(title="Send recap", status="completed"))
        assert get_task_stats() == {
            "total": 3,
            "pending": 1,
            "in_progress": 1,
            "completed": 1,
        }


def test_landing_and_dashboard_routes(client):
    landing = client.get("/")
    dashboard = client.get("/dashboard")
    assert landing.status_code == 200
    assert b"Big goals." in landing.data
    assert b'href="/dashboard"' in landing.data
    assert dashboard.status_code == 200
    assert b"All tasks" in dashboard.data
    assert b">0</strong>" in dashboard.data


def test_create_update_complete_and_delete_http_routes(client, app):
    response = client.post(
        "/tasks/new",
        data=task_data(),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Task created." in response.data
    assert b"Write the project brief" in response.data

    with app.app_context():
        task_id = get_db().execute("SELECT id FROM tasks").fetchone()["id"]

    edited_page = client.get(f"/tasks/{task_id}/edit")
    assert edited_page.status_code == 200
    assert b"Write the project brief" in edited_page.data

    response = client.post(
        f"/tasks/{task_id}/edit",
        data=task_data(title="Updated brief"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Updated brief" in response.data

    response = client.post(f"/tasks/{task_id}/complete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Completed" in response.data

    response = client.post(f"/tasks/{task_id}/complete", data={"completed": "false"})
    assert response.status_code == 302
    response = client.post(f"/tasks/{task_id}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Updated brief" not in response.data


def test_http_validation_search_filters_and_missing_task(client, app):
    invalid = client.post("/tasks/new", data=task_data(title=" "), follow_redirects=True)
    assert invalid.status_code == 200
    assert b"A task title is required." in invalid.data
    with app.app_context():
        first_id = create_task(task_data(title="Findable task", priority="high"))
        create_task(task_data(title="Other work", priority="low"))

    filtered = client.get("/dashboard?q=findable&priority=high")
    assert b"Findable task" in filtered.data
    assert b"Other work" not in filtered.data
    invalid_filter = client.get("/dashboard?status=unknown", follow_redirects=True)
    assert b"Choose a valid status filter." in invalid_filter.data
    assert client.get("/tasks/999/edit").status_code == 404
    assert client.post(f"/tasks/{first_id}/delete").status_code == 302
