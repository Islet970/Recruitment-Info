import json
import re
from typing import Any

from openai import OpenAI

from app.core.config import settings


class ResumeAnalysisError(Exception):
    pass


SYSTEM_PROMPT = """你是专业的中文招聘简历分析助手。请从简历文本中提取结构化信息，用于求职推荐系统。
必须只返回合法 JSON，不要返回 Markdown、代码块或解释文字。"""

USER_PROMPT_TEMPLATE = """请分析下面的简历文本，返回以下 JSON 结构：
{
  "summary": "一句话概括候选人背景",
  "skills": ["技能1", "技能2"],
  "experience_years": 0.0,
  "education_level": "博士/硕士/本科/大专/高中/未知",
  "recommended_directions": ["方向1", "方向2"],
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["不足1", "不足2"],
  "detailed_analysis": "综合分析，说明技能、项目经验、岗位适配方向"
}

要求：
1. skills 只保留可用于岗位匹配的技能、工具、框架、语言、数据库、算法、岗位能力。
2. experience_years 必须是数字；应届生或无明确经验可填 0。
3. education_level 只填最高学历。
4. recommended_directions 给 2 到 5 个适合的岗位方向。
5. 不要编造简历中完全没有依据的经历。

简历文本：
{resume_text}"""


def analyze_resume_with_llm(resume_text: str) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        raise ResumeAnalysisError("未配置大模型 API Key")

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL or None,
    )
    prompt = USER_PROMPT_TEMPLATE.format(resume_text=resume_text[:12000])

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise ResumeAnalysisError("大模型简历分析调用失败") from exc

    content = response.choices[0].message.content or ""
    parsed = _parse_json_content(content)
    return _normalize_analysis(parsed)


def _parse_json_content(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", content)
        if not match:
            raise ResumeAnalysisError("大模型返回内容不是有效 JSON")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ResumeAnalysisError("大模型返回 JSON 解析失败") from exc


def _normalize_analysis(data: dict[str, Any]) -> dict[str, Any]:
    skills = _string_list(data.get("skills"))
    directions = _string_list(data.get("recommended_directions"))
    strengths = _string_list(data.get("strengths"))
    weaknesses = _string_list(data.get("weaknesses"))

    return {
        "summary": str(data.get("summary") or "未生成简历摘要"),
        "skills": skills,
        "experience_years": _float_value(data.get("experience_years")),
        "education_level": str(data.get("education_level") or "未知"),
        "recommended_directions": directions,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "detailed_analysis": str(data.get("detailed_analysis") or ""),
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result = []
    seen = set()
    for item in value:
        text = str(item).strip()
        key = text.lower()
        if text and key not in seen:
            result.append(text)
            seen.add(key)
    return result


def _float_value(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(number, 99.9))
