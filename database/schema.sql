-- =============================================================================
-- Daily Pulse — Database Schema
-- =============================================================================
-- This file is the single source of truth for the database structure.
-- database/db.py reads and executes it during init_db().
--
-- Rules:
--   • Every CREATE TABLE uses IF NOT EXISTS — safe to run on every startup.
--   • Foreign keys are declared but enforcement is enabled at connection time
--     inside db.py (PRAGMA foreign_keys = ON).
--   • Column order: primary key → required fields → optional fields → timestamps.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. departments
--    Lookup table that stores department names.
--    Managers can later filter and analyse burnout trends by department without
--    duplicating the name string across every employee row.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE          -- e.g. "Engineering", "Sales"
);


-- -----------------------------------------------------------------------------
-- 2. employees
--    One row per registered employee.
--    `department_id` is a nullable FK to departments so the column works even
--    before the manager module and department list are populated.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees (
    id            TEXT    PRIMARY KEY,                       -- e.g. "EMP001"
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    department_id INTEGER REFERENCES departments(id)
                          ON DELETE SET NULL,                -- keep employee if dept removed
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- -----------------------------------------------------------------------------
-- 3. survey_responses
--    One row per daily survey submission.
--    The (employee_id, date) pair is UNIQUE — enforces the one-per-day rule at
--    the database level as a safety net alongside the application-level check.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS survey_responses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id   TEXT    NOT NULL REFERENCES employees(id)
                          ON DELETE CASCADE,                 -- remove responses if employee deleted
    date          DATE    NOT NULL,
    -- ── Survey inputs (all validated in routes.py before insertion) ──────
    happiness     INTEGER NOT NULL CHECK (happiness  BETWEEN 1 AND 10),
    motivation    INTEGER NOT NULL CHECK (motivation BETWEEN 1 AND 10),
    stress        INTEGER NOT NULL CHECK (stress     BETWEEN 1 AND 10),
    caffeine      INTEGER NOT NULL CHECK (caffeine   BETWEEN 0 AND 6),
    -- ── ML API outputs (NULL when the API was unreachable) ───────────────
    burnout_score REAL,                                      -- 0.0 – 100.0
    burnout_label TEXT,                                      -- "Low" | "Medium" | "High"

    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Enforce the one-survey-per-day rule at the DB level
    UNIQUE (employee_id, date)
);


-- -----------------------------------------------------------------------------
-- 4. users
--    One row per registered user (employees AND managers).
--    Separates authentication credentials from employee profile data so that
--    managers (who have no row in the employees table) can also log in.
--
--    Design decisions
--    ----------------
--    • role is enforced at the DB level with a CHECK constraint so no
--      application-layer mistake can store an invalid role.
--    • employee_id is a nullable FK to employees.id — set for users with
--      role='employee', NULL for managers.  ON DELETE SET NULL keeps the
--      auth record even if the employee profile is removed, so the manager
--      can still log in after an admin error.
--    • email is stored here (not re-used from employees) so that a manager
--      account can be created without a corresponding employees row.
--    • password_hash stores the Werkzeug/bcrypt output — never a plaintext
--      password.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('employee', 'manager')),
    employee_id   TEXT    REFERENCES employees(id)
                          ON DELETE SET NULL,                -- nullable: only set for role='employee'
    manager_id    TEXT    UNIQUE,                            -- nullable: only set for role='manager'; no FK (managers have no employees row)
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- -----------------------------------------------------------------------------
-- Indexes
-- -----------------------------------------------------------------------------

-- Speeds up the two most common query patterns used by repository.py:
--   • "fetch today's response for employee X"          → idx_responses_emp_date
--   • "fetch this week's responses for employee X"     → idx_responses_emp_date
-- A single composite index covers both queries.
CREATE INDEX IF NOT EXISTS idx_responses_emp_date
    ON survey_responses (employee_id, date);

-- Speeds up the login lookup (find_user_by_email) and duplicate-check
-- (email_exists) — both query users.email.
CREATE INDEX IF NOT EXISTS idx_users_email
    ON users (email);
