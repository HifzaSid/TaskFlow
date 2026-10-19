"""HTTP routes for the landing page and task dashboard."""

import sqlite3
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.models import PRIORITIES, STATUSES, ValidationError
from app.services import (
    create_task,
    delete_task,
    get_task,
    get_task_stats,
    list_tasks,
    set_task_completed,
    update_task,
)

bp = Blueprint("main", __name__)


@bp.get("/")
def landing():
    """Render the public product landing page."""
    return render_template("landing.html")


@bp.get("/dashboard")
def dashboard():
    """Render database-backed statistics and the filtered task list."""
    search = request.args.get("q", "")
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")
    try:
        tasks = list_tasks(search=search, status=status, priority=priority)
    except ValidationError as error:
        flash(str(error), "error")
        return redirect(url_for("main.dashboard", q=search))
    return render_template(
        "dashboard.html",
        tasks=tasks,
        stats=get_task_stats(),
        search=search,
        selected_status=status,
        selected_priority=priority,
        today=date.today().isoformat(),
    )


@bp.route("/tasks/new", methods=("GET", "POST"))
def new_task():
    """Display and process the create-task form."""
    if request.method == "POST":
        try:
            create_task(request.form)
        except ValidationError as error:
            flash(str(error), "error")
        except sqlite3.Error:
            flash("The task could not be saved. Please try again.", "error")
        else:
            flash("Task created.", "success")
            return redirect(url_for("main.dashboard"))
        return redirect(url_for("main.new_task"))
    return render_template("task_form.html", task=None, priorities=PRIORITIES, statuses=STATUSES)


@bp.route("/tasks/<int:task_id>/edit", methods=("GET", "POST"))
def edit_task(task_id: int):
    """Display and process the edit form for an existing task."""
    task = get_task(task_id)
    if task is None:
        abort(404)
    if request.method == "POST":
        try:
            updated = update_task(task_id, request.form)
        except ValidationError as error:
            flash(str(error), "error")
        except sqlite3.Error:
            flash("The task could not be updated. Please try again.", "error")
        else:
            if not updated:
                abort(404)
            flash("Task updated.", "success")
            return redirect(url_for("main.dashboard"))
        return redirect(url_for("main.edit_task", task_id=task_id))
    return render_template("task_form.html", task=task, priorities=PRIORITIES, statuses=STATUSES)


@bp.post("/tasks/<int:task_id>/complete")
def complete_task(task_id: int):
    """Complete a task or reopen a completed task."""
    completed = request.form.get("completed") != "false"
    if not set_task_completed(task_id, completed):
        abort(404)
    flash("Task marked complete." if completed else "Task reopened.", "success")
    return redirect(url_for("main.dashboard"))


@bp.post("/tasks/<int:task_id>/delete")
def remove_task(task_id: int):
    """Delete a task after its form explicitly requests deletion."""
    if not delete_task(task_id):
        abort(404)
    flash("Task deleted.", "success")
    return redirect(url_for("main.dashboard"))
