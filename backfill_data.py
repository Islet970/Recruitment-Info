"""Backfill existing database records with full data from JSON files."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

engine = create_engine(settings.DATABASE_URL, echo=False)


def backfill():
    session = Session(engine)

    # Load all JSON jobs
    all_jobs = []
    for fname in sorted(os.listdir(OUTPUT_DIR)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(OUTPUT_DIR, fname), "r", encoding="utf-8") as f:
            jobs = json.load(f)
        for job in jobs:
            job["_recruit_type"] = fname.replace("岗位.json", "")
        all_jobs.extend(jobs)
        print(f"Loaded {fname}: {len(jobs)} jobs")

    print(f"\nTotal: {len(all_jobs)} jobs\n")

    # Phase 1: Update companies
    print("=== Updating companies ===")
    companies_updated = 0
    companies_seen = set()

    for job in all_jobs:
        company_id = str(job.get("公司ID", ""))
        company_name = job.get("公司名称", "").strip()
        if not company_id or company_id in companies_seen:
            continue
        companies_seen.add(company_id)

        # Find company by origin_id
        result = session.execute(
            text("SELECT id, short_name, scale, industry, address, logo_url, website, description FROM companies WHERE origin_id = :oid"),
            {"oid": company_id},
        )
        row = result.fetchone()
        if not row:
            # Try by name
            result = session.execute(
                text("SELECT id, short_name, scale, industry, address, logo_url, website, description FROM companies WHERE name = :name"),
                {"name": company_name},
            )
            row = result.fetchone()

        if not row:
            continue

        cid = row[0]
        updates = []
        params = {"id": cid}

        short_name = job.get("公司简称", "")
        if short_name and not row[1]:
            updates.append("short_name = :short_name")
            params["short_name"] = short_name

        scale = job.get("公司规模", "")
        if scale and not row[2]:
            updates.append("scale = :scale")
            params["scale"] = scale

        industry = job.get("所属行业", "")
        if industry and not row[3]:
            updates.append("industry = :industry")
            params["industry"] = industry

        address = job.get("公司地址", "")
        if address and not row[4]:
            updates.append("address = :address")
            params["address"] = address

        logo_url = job.get("公司Logo", "")
        if logo_url and not row[5]:
            updates.append("logo_url = :logo_url")
            params["logo_url"] = logo_url

        website = job.get("公司官网", "")
        if website and not row[6]:
            updates.append("website = :website")
            params["website"] = website

        description = job.get("公司介绍", "")
        if description and not row[7]:
            updates.append("description = :description")
            params["description"] = description

        # Also check financing_stage
        financing_stage = job.get("融资阶段", "")
        if financing_stage:
            result2 = session.execute(
                text("SELECT financing_stage FROM companies WHERE id = :id"), {"id": cid}
            )
            existing_stage = result2.fetchone()[0]
            if not existing_stage:
                updates.append("financing_stage = :financing_stage")
                params["financing_stage"] = financing_stage

        if updates:
            sql = f"UPDATE companies SET {', '.join(updates)} WHERE id = :id"
            session.execute(text(sql), params)
            companies_updated += 1

    session.commit()
    print(f"Companies updated: {companies_updated}")

    # Phase 2: Update positions (location field)
    print("\n=== Updating positions ===")
    positions_updated = 0

    for job in all_jobs:
        origin_id = str(job.get("岗位ID", ""))
        location = job.get("工作地址", "")
        if not origin_id or not location:
            continue

        result = session.execute(
            text("SELECT id, location FROM job_positions WHERE origin_id = :oid"),
            {"oid": origin_id},
        )
        row = result.fetchone()
        if not row:
            continue

        if not row[1]:  # location is NULL
            session.execute(
                text("UPDATE job_positions SET location = :loc WHERE id = :id"),
                {"loc": location, "id": row[0]},
            )
            positions_updated += 1

    session.commit()
    print(f"Positions updated: {positions_updated}")

    session.close()
    engine.dispose()
    print("\nBackfill complete!")


if __name__ == "__main__":
    backfill()
