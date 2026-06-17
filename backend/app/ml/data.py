import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[3] / "output"
JSON_FILES = ["校招岗位.json", "社招岗位.json", "实习岗位.json"]

CATEGORICAL_FEATURES = [
    "city",
    "education",
    "recruit_type",
    "company_scale",
    "financing_stage",
    "industry",
    "category",
]
NUMERIC_FEATURES = ["salary_month", "text_length", "skill_count"]
MODEL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def parse_education(value: Any) -> str:
    edu = str(value or "")
    if "博士" in edu:
        return "博士"
    if "硕士" in edu:
        return "硕士"
    if "本科" in edu:
        return "本科"
    if "大专" in edu:
        return "大专"
    return "不限"


def clean_value(value: Any, default: str = "未知") -> str:
    text = str(value or "").strip()
    return text if text else default


def split_tags(value: Any) -> list[str]:
    tags = []
    for tag in str(value or "").replace("，", ",").split(","):
        normalized = tag.strip().lower()
        if normalized and normalized not in tags:
            tags.append(normalized)
    return tags


def get_output_files() -> list[Path]:
    return [DATA_DIR / name for name in JSON_FILES if (DATA_DIR / name).exists()]


def data_signature() -> dict[str, float]:
    return {path.name: path.stat().st_mtime for path in get_output_files()}


def load_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in get_output_files():
        with path.open("r", encoding="utf-8") as f:
            jobs = json.load(f)
        recruit_type = path.stem.replace("岗位", "")
        for idx, item in enumerate(jobs):
            records.append(normalize_record(item, recruit_type, f"{path.stem}-{idx}"))
    return records


def normalize_record(item: dict[str, Any], recruit_type: str, record_id: str) -> dict[str, Any]:
    salary_min = float(item.get("薪资下限") or 0)
    salary_max = float(item.get("薪资上限") or 0)
    salary_type = clean_value(item.get("薪资类型"), "月薪")
    salary_month = int(float(item.get("薪资月数") or 12))
    if "日" in salary_type:
        salary_type = "日薪"
        salary_month = 1
    else:
        salary_type = "月薪"
    salary_mid = (salary_min + salary_max) / 2 if salary_min > 0 and salary_max > 0 and salary_max < 999999 else 0
    text = " ".join(str(item.get(k) or "") for k in ["岗位名称", "岗位职责", "岗位要求", "加分项"])
    tags = split_tags(item.get("岗位标签"))
    return {
        "id": record_id,
        "name": clean_value(item.get("岗位名称"), "未命名岗位"),
        "company": clean_value(item.get("公司名称"), "未知公司"),
        "salary_text": clean_value(item.get("薪资"), "未知"),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_mid": salary_mid,
        "salary_type": salary_type,
        "salary_month": salary_month,
        "city": clean_value(item.get("工作城市")),
        "education": parse_education(item.get("学历要求")),
        "recruit_type": recruit_type,
        "company_scale": clean_value(item.get("公司规模")),
        "financing_stage": clean_value(item.get("融资阶段")),
        "industry": clean_value(item.get("所属行业")),
        "category": clean_value(item.get("搜索关键词"), "其他"),
        "tags": tags,
        "text_length": len(text),
        "skill_count": len(tags),
    }


def salary_training_records() -> list[dict[str, Any]]:
    return [r for r in load_records() if r["salary_mid"] > 0 and r["salary_type"] == "月薪"]


def feature_options() -> dict[str, list[str]]:
    records = load_records()
    options: dict[str, list[str]] = {}
    for feature in CATEGORICAL_FEATURES:
        values = sorted({r[feature] for r in records if r.get(feature)})
        options[feature] = values[:300]
    tags = sorted({tag for r in records for tag in r["tags"]})
    options["tags"] = tags[:500]
    return options
