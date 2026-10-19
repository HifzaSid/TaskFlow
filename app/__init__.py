"""Application factory for TaskFlow."""

from pathlib import Path

from flask import Flask

from app.database import close_db, init_db


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure a TaskFlow application instance."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev-only-change-me",
        DATABASE=str(Path(app.instance_path) / "taskflow.sqlite"),
    )

    if test_config is not None:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    from app.routes import bp

    app.register_blueprint(bp)
    return app
