import os
from __init__ import create_app

app = create_app(os.environ.get("FLASK_CONFIG", "production"))
