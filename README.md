# TaskFlow

TaskFlow is a small, complete task-management web application built with Python, Flask, SQLite, Jinja templates, CSS, and vanilla JavaScript. It is designed as a learning project for exploring application structure, database-backed features, tests, and Git workflows. No account or external service is required.

## Features

- A responsive product landing page that links to the real task dashboard.
- Database-backed task statistics and task list.
- Create, edit, complete/reopen, and delete tasks.
- Optional descriptions and due dates, plus low, medium, or high priority.
- Search by title or description and filter by status and priority.
- Server-side validation and parameterized SQLite queries.
- Isolated pytest fixtures that use a temporary database.

## Requirements

- Python 3.10 or newer
- Windows PowerShell (commands below), or a terminal with Python available

## Set up on Windows PowerShell

Open PowerShell in the project directory, then create and activate a virtual environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts, allow scripts for this terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install the application and test dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Start the app

```powershell
python run.py
```

Open <http://127.0.0.1:5000/> in your browser. The dashboard is available at <http://127.0.0.1:5000/dashboard>. The SQLite database is created automatically at `instance/taskflow.sqlite`; it is local development data and is ignored by Git.

## Run the tests

```powershell
python -m pytest
```

The pytest app fixture puts its database in pytest's temporary directory, so tests do not read or modify your development database.

## Project structure

```text
app/
  __init__.py          Flask application factory
  database.py          SQLite connection and schema setup
  models.py            Task data model and input validation
  services.py          Task persistence and business operations
  routes.py            Browser routes and HTTP form handling
  templates/           Shared layout, landing page, dashboard, task form
  static/
    css/styles.css     Responsive interface styles
    js/app.js          Delete confirmation interaction
tests/
  conftest.py          Temporary-database fixtures
  test_tasks.py        Task, persistence, filtering, and route tests
run.py                 Local development entry point
```

## How a request becomes a page

When a browser requests `/dashboard`, Flask matches the URL and HTTP method to the dashboard function in `app/routes.py`. The route reads the search and filter values, then calls `app/services.py`, which applies validation and builds the matching task query. Database operations use the request-scoped SQLite connection in `app/database.py`; SQL values are passed as parameters, not pasted into query strings. The service converts returned rows to `Task` objects and calculates the dashboard counts from the database.

Flask then renders `dashboard.html` with those task objects and statistics. That page extends `base.html`, so the shared navigation, flash messages, page title, stylesheet, and JavaScript are included consistently. Jinja escapes task-provided text when it inserts it into HTML. The browser separately loads `static/css/styles.css` for responsive layout and `static/js/app.js` for the delete-confirmation interaction. When a form is submitted, the browser sends another HTTP request to a Flask route, and the same route → service → SQLite flow persists the change before redirecting back to the dashboard.
