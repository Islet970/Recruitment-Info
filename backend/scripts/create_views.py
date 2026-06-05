"""Create 3 SQL views for recruit_type filtering — idempotent (safe to re-run)."""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from app.core.database import engine
from sqlalchemy import text

VIEWS = {
    "v_campus_positions": "CAMPUS",
    "v_social_positions": "SOCIAL",
    "v_intern_positions": "INTERN",
}

SQL_TEMPLATE = """
CREATE OR REPLACE VIEW {view_name} AS
SELECT
    jp.id, jp.origin_id, jp.name, jp.url, jp.company_id, jp.category_id,
    jp.recruit_type, jp.city, jp.location, jp.salary_text, jp.salary_type,
    jp.salary_min, jp.salary_max, jp.salary_month,
    jp.education_required, jp.graduation_year, jp.experience_required,
    jp.tags, jp.responsibility, jp.requirement, jp.bonus,
    jp.publish_time, jp.refresh_time, jp.source, jp.is_active,
    jp.created_at, jp.updated_at,
    c.name AS company_name,
    c.scale AS company_scale,
    c.financing_stage AS company_financing_stage,
    c.industry AS company_industry,
    jc.name AS category_name
FROM job_positions jp
LEFT JOIN companies c ON jp.company_id = c.id
LEFT JOIN job_categories jc ON jp.category_id = jc.id
WHERE jp.recruit_type = '{recruit_type}';
"""


def main():
    with engine.connect() as conn:
        for view_name, recruit_type in VIEWS.items():
            sql = SQL_TEMPLATE.format(view_name=view_name, recruit_type=recruit_type)
            conn.execute(text(sql))
            conn.commit()
            print(f"  [OK] {view_name} ({recruit_type})")

        # Verify row counts
        print("\nVerification:")
        for view_name in VIEWS:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {view_name}"))
            cnt = result.scalar()
            print(f"  {view_name}: {cnt} rows")

    print("\nDone!")


if __name__ == "__main__":
    main()
