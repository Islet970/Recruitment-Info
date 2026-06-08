"""Import nowcoder JSON data into MySQL."""
import json, os, sys, glob
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from app.core.database import SessionLocal, engine, Base
from app.models.company import Company
from app.models.category import JobCategory
from app.models.skill import Skill
from app.models.position import JobPosition, PositionSkill, RecruitType

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "output")

def find_file(label):
    """Find data file matching Chinese label."""
    for f in glob.glob(os.path.join(DATA_DIR, "*.json")):
        base = os.path.basename(f)
        # Files are named like "实习岗位.json", "校招岗位.json", "社招岗位.json"
        if label in base:
            return f
    return None


def parse_salary(item):
    smin = item.get("薪资下限", 0) or 0
    smax = item.get("薪资上限", 0) or 0
    stype = item.get("薪资类型", "月薪") or "月薪"
    smonth = item.get("薪资月数", 12) or 12
    if smin == 0 and smax == 9999999:
        smin, smax = 0, 0
    if "日" in stype:
        stype = "日薪"
    else:
        stype = "月薪"
    return float(smin), float(smax), stype, int(smonth)


def parse_education(item):
    edu = item.get("学历要求", "") or ""
    if "博士" in edu:
        return "博士"
    elif "硕士" in edu:
        return "硕士"
    elif "本科" in edu:
        return "本科"
    elif "大专" in edu:
        return "大专"
    return "不限"


def parse_experience(item):
    exp = item.get("经验要求", "") or ""
    if "经验不限" in exp or not exp:
        return "不限"
    return exp


def import_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        company_map = {}
        category_map = {}
        skill_map = {}
        total = 0

        for recruit_label in ["实习", "校招", "社招"]:
            filepath = find_file(recruit_label)
            if not filepath:
                print(f"File not found for: {recruit_label}")
                continue

            print(f"Reading: {filepath}")
            with open(filepath, "r", encoding="utf-8") as f:
                jobs = json.load(f)

            recruit_type = {
                "校招": RecruitType.CAMPUS,
                "社招": RecruitType.SOCIAL,
                "实习": RecruitType.INTERN,
            }[recruit_label]

            print(f"  {recruit_label}: {len(jobs)} records to import")

            for item in jobs:
                # Company
                company_name = (item.get("公司名称") or "").strip()
                if not company_name:
                    continue
                if company_name not in company_map:
                    existing = db.query(Company).filter(Company.name == company_name).first()
                    if existing:
                        company_map[company_name] = existing.id
                    else:
                        c = Company(
                            name=company_name,
                            origin_id=str(item.get("公司ID") or ""),
                            short_name=item.get("公司简称"),
                            scale=item.get("公司规模"),
                            financing_stage=item.get("融资阶段"),
                            industry=item.get("所属行业"),
                            address=item.get("公司地址"),
                            logo_url=item.get("公司Logo"),
                            website=item.get("公司网址"),
                            description=item.get("公司介绍"),
                        )
                        db.add(c)
                        db.flush()
                        company_map[company_name] = c.id

                # Category
                cat_name = (item.get("搜索关键词") or "其他").strip()
                if cat_name not in category_map:
                    existing = db.query(JobCategory).filter(JobCategory.name == cat_name).first()
                    if existing:
                        category_map[cat_name] = existing.id
                    else:
                        jc = JobCategory(name=cat_name)
                        db.add(jc)
                        db.flush()
                        category_map[cat_name] = jc.id

                # Position
                smin, smax, stype, smonth = parse_salary(item)
                def _parse_time(val):
                    if val:
                        try:
                            return datetime.strptime(val.strip(), "%Y-%m-%d %H:%M")
                        except (ValueError, AttributeError):
                            pass
                    return None
                publish_time = _parse_time(item.get("发布时间"))
                refresh_time = _parse_time(item.get("刷新时间")) or publish_time

                pos = JobPosition(
                    origin_id=str(item.get("岗位ID", "")),
                    name=(item.get("岗位名称") or "").strip(),
                    url=item.get("岗位链接"),
                    company_id=company_map[company_name],
                    category_id=category_map[cat_name],
                    recruit_type=recruit_type,
                    city=item.get("工作城市"),
                    location=item.get("工作地址"),
                    salary_text=item.get("薪资"),
                    salary_type=stype,
                    salary_min=smin,
                    salary_max=smax,
                    salary_month=smonth,
                    education_required=parse_education(item),
                    graduation_year=item.get("毕业年份"),
                    experience_required=parse_experience(item),
                    tags=item.get("岗位标签"),
                    responsibility=item.get("岗位职责"),
                    requirement=item.get("岗位要求"),
                    bonus=item.get("加分项"),
                    publish_time=publish_time,
                    refresh_time=refresh_time,
                    source="牛客网",
                    is_active=True,
                )
                db.add(pos)
                db.flush()

                # Skills
                tags_str = item.get("岗位标签", "") or ""
                if tags_str:
                    tag_names = [t.strip() for t in tags_str.split(",") if t.strip()]
                    for tag_name in tag_names:
                        if tag_name not in skill_map:
                            existing = db.query(Skill).filter(Skill.name == tag_name).first()
                            if existing:
                                skill_map[tag_name] = existing.id
                            else:
                                s = Skill(name=tag_name)
                                db.add(s)
                                db.flush()
                                skill_map[tag_name] = s.id
                        ps = PositionSkill(position_id=pos.id, skill_id=skill_map[tag_name])
                        db.add(ps)

                total += 1
                if total % 100 == 0:
                    db.commit()
                    print(f"    Imported {total} positions...")

            print(f"  Finished {recruit_label}")

        db.commit()
        print(f"\nImport complete! Total: {total} positions")
        print(f"  Companies: {len(company_map)}")
        print(f"  Categories: {len(category_map)}")
        print(f"  Skills: {len(skill_map)}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_data()
