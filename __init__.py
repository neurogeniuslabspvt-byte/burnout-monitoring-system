import os
from flask import Flask, redirect, url_for


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        instance_relative_config=True,
    )

    _load_config(app, config_name)
    _init_extensions(app)
    _init_database(app)
    _register_blueprints(app)

    return app


def _load_config(app: Flask, config_name: str | None) -> None:
    from config import config_map, _validate_production_config

    name = config_name or os.environ.get("FLASK_CONFIG", "default")
    if name not in config_map:
        raise KeyError(
            f"Unknown config name '{name}'. Valid: {list(config_map.keys())}"
        )

    app.config.from_object(config_map[name])
    os.makedirs(app.instance_path, exist_ok=True)


    if name == "production":
        _validate_production_config(app)


def _init_extensions(app: Flask) -> None:
    from database.db import close_db_connection
    app.teardown_appcontext(close_db_connection)


def _init_database(app: Flask) -> None:
    from database.db import init_db
    with app.app_context():
        init_db()


def _register_blueprints(app: Flask) -> None:
    from auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from employee.routes import employee_bp
    app.register_blueprint(employee_bp)

    from manager.routes import manager_bp
    app.register_blueprint(manager_bp)

    @app.route("/")
    def index():
        return redirect(url_for("auth.login_page"))
