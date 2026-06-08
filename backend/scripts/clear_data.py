"""Drop SQL views, then delete all data from all tables in FK-safe order."""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from app.core.database import SessionLocal, engine
from sqlalchemy import text

VIEWS = ["v_campus_positions", "v_social_positions", "v_intern_positions"]
# Order matters: child tables first, parent tables last
TABLES = [
    "position_skills",
    "user_favorites",
    "resume_analyses",
    "resumes",
    "job_positions",
    "companies",
    "job_categories",
    "skills",
    "users",
]

def clear_data():
    with engine.connect() as conn:
        # Drop views
        for v in VIEWS:
            conn.execute(text(f"DROP VIEW IF EXISTS {v}"))
            print(f"  [OK] Dropped view {v}")

        # Disable FK checks, truncate all tables
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for t in TABLES:
            conn.execute(text(f"TRUNCATE TABLE {t}"))
            print(f"  [OK] Truncated table {t}")
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        conn.commit()

    print(f"\nAll {len(TABLES)} tables cleared, {len(VIEWS)} views dropped.")


if __name__ == "__main__":
    clear_data()