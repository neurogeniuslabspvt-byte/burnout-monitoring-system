import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __init__ import create_app
from werkzeug.security import generate_password_hash

DEPARTMENTS = ["Engineering", "HR", "Sales", "Marketing", "Operations"]

MANAGER = {
    "name":       "Admin Manager",
    "email":      "manager@company.com",
    "password":   "Manager@1234",
    "role":       "manager",
    "manager_id": "Mg1@seed",   
}


def seed():
    app = create_app("development")
    with app.app_context():
        from database.db import get_db_connection
        conn = get_db_connection()


        for dept in DEPARTMENTS:
            conn.execute(
                "INSERT OR IGNORE INTO departments (name) VALUES (?)",
                (dept,),
            )


        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (MANAGER["email"],),
        ).fetchone()

        if existing is None:
            conn.execute(
                """
                INSERT INTO users (name, email, password_hash, role, employee_id, manager_id)
                VALUES (?, ?, ?, ?, NULL, ?)
                """,
                (
                    MANAGER["name"],
                    MANAGER["email"],
                    generate_password_hash(MANAGER["password"]),
                    MANAGER["role"],
                    MANAGER["manager_id"],
                ),
            )
            print(f"  ✓ Manager account created  →  {MANAGER['email']} / {MANAGER['password']}")
            print(f"  ✓ Manager Employee ID      →  {MANAGER['manager_id']}")
        else:
            print(f"  · Manager account already exists ({MANAGER['email']}), skipped.")

        conn.commit()
        print("  ✓ Departments seeded.")
        print("\nSeed complete. Run:  python run.py")


if __name__ == "__main__":
    seed()
