from database.db import get_db_connection as get_db   # noqa: F401  (re-export)
from database.db import init_db                        # noqa: F401  (re-export)


# ---------------------------------------------------------------------------
# Standalone runner — kept for convenience during development.
#
# Run from the project root:
#     python -m employee.init_db
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Minimal Flask app context so get_db_connection() / init_db() can read
    # current_app.config["DATABASE_URI"].
    import os
    from flask import Flask
    from config import config_map

    _app = Flask(__name__, instance_relative_config=True)
    _app.config.from_object(config_map[os.environ.get("FLASK_CONFIG", "default")])
    os.makedirs(_app.instance_path, exist_ok=True)

    with _app.app_context():
        init_db()
        print(f"Database initialised at {_app.config['DATABASE_URI']}")
