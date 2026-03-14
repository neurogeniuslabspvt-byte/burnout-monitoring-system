import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

from __init__ import create_app
app = create_app("development")

with app.app_context():
    from database.db import get_db_connection
    conn = get_db_connection()

    conn.execute("DELETE FROM survey_responses")
    conn.execute("DELETE FROM users")
    conn.execute("DELETE FROM employees")
    conn.execute("DELETE FROM departments")
    conn.commit()
    print("All data deleted.")