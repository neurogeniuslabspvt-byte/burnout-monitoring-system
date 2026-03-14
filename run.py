import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __init__ import create_app   # noqa: E402

if __name__ == "__main__":
    config = os.environ.get("FLASK_CONFIG", "development")
    app = create_app(config)
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=app.config.get("DEBUG", True),
    )
