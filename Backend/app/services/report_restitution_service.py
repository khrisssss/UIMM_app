"""SWOT findings per axis, shown in the « Restitution » part of the report page."""
import ast
import json

from app.models.axis import Axis
from app.models.company import Company
from app.models.company_axis import CompanyAxis
from app.models.reports import Report
from app.models.score import Score
from app.models.swot import SWOT


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def parse_swot_value(value):
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("{", "[")):
            for loader in (json.loads, ast.literal_eval):
                try:
                    return loader(text)
                except (ValueError, SyntaxError, TypeError):
                    pass
    return value


def split_lines(value):
    value = parse_swot_value(value)
    if isinstance(value, dict):
        return [
            axis + " : " + item
            for axis, values in value.items()
            for item in split_lines(values)
        ]
    if isinstance(value, (list, tuple)):
        return [item for value_item in value for item in split_lines(value_item)]
    text = clean_text(value)
    if not text:
        return []
    return [
        line.strip().lstrip("-•").strip()
        for line in text.replace("•", "\n").splitlines()
        if line.strip().lstrip("-•").strip()
    ]


def axis_swot_items(value, axis_name):
    parsed = parse_swot_value(value)
    if isinstance(parsed, dict):
        return split_lines(next(
            (items for name, items in parsed.items() if name.casefold() == axis_name.casefold()),
            [],
        ))
    return [
        item for item in split_lines(parsed)
        if item.casefold().startswith(axis_name.casefold() + " :")
    ]


def limit_items(items, maximum=6):
    clean_items = []

    for item in items:
        cleaned_item = clean_text(item)

        if cleaned_item:
            clean_items.append(cleaned_item)

    return clean_items[:maximum]


def get_axis_scores(db, company_id):
    rows = (
        db.query(Score, Axis)
        .join(Axis, Score.axis_id == Axis.id)
        .join(CompanyAxis, CompanyAxis.axis_id == Axis.id)
        .filter(Score.company_id == company_id, CompanyAxis.company_id == company_id, CompanyAxis.is_selected == True, Axis.is_active.is_(True))
        .order_by(Axis.order_index)
        .all()
    )

    scores = []

    for score, axis in rows:
        scores.append(
            {
                "axis_id": axis.id,
                "axis_name": axis.name,
                "score_percentage": round(float(score.score_percentage or 0), 1),
                "score_obtained": float(score.score_total or 0),
                "score_maximum": float(score.score_max or 0),
            }
        )

    return scores


def get_selected_report_axes(db, company_id, scores):
    """SWOT coverage follows selected axes, independently of score availability."""
    rows = (
        db.query(Axis)
        .join(CompanyAxis, CompanyAxis.axis_id == Axis.id)
        .filter(CompanyAxis.company_id == company_id, CompanyAxis.is_selected == True, Axis.is_active.is_(True))
        .order_by(Axis.order_index)
        .all()
    )
    scores_by_id = {item["axis_id"]: item for item in scores}
    return [
        {
            "axis_id": axis.id,
            "axis_name": axis.name,
            "score_percentage": scores_by_id.get(axis.id, {}).get("score_percentage"),
        }
        for axis in rows
    ]


def get_axis_comments(db, company_id):
    rows = (
        db.query(CompanyAxis, Axis)
        .join(Axis, CompanyAxis.axis_id == Axis.id)
        .filter(CompanyAxis.company_id == company_id, Axis.is_active.is_(True))
        .order_by(Axis.order_index)
        .all()
    )

    comments = {}

    for company_axis, axis in rows:
        comments[axis.name] = clean_text(company_axis.diagnostic_comment)

    return comments


def get_latest_swot(db, company_id):
    return (
        db.query(SWOT)
        .filter(SWOT.company_id == company_id, SWOT.axis_id.is_(None))
        .order_by(SWOT.created_at.desc())
        .first()
    )


def build_swot_by_axis_from_global_swot(swot, scores, axis_comments, axis_analysis):
    swot_by_axis = []
    for score in scores:
        axis_name = score["axis_name"]
        findings = next((value for name, value in axis_analysis.items()
                         if name.casefold() == axis_name.casefold()), {})
        if not isinstance(findings, dict):
            findings = {}
        swot_by_axis.append({
            "axis_name": axis_name,
            "score_percentage": score["score_percentage"],
            "comment": axis_comments.get(axis_name, ""),
            **{
                category: (
                    limit_items(findings[category], 5)
                    if category in findings
                    else limit_items(axis_swot_items(getattr(swot, category, None), axis_name), 5)
                )
                for category in ("strengths", "weaknesses", "opportunities", "threats")
            },
        })
    return swot_by_axis


def build_report_swot_by_axis(db, company: Company, report: Report):
    """For each selected axis: its score, the consultant's comment and its SWOT findings."""
    try:
        axis_analysis = json.loads(report.axis_analysis or "{}")
    except (ValueError, TypeError):
        axis_analysis = {}
    if not isinstance(axis_analysis, dict):
        axis_analysis = {}

    scores = get_axis_scores(db, company.id)
    return build_swot_by_axis_from_global_swot(
        swot=get_latest_swot(db, company.id),
        scores=get_selected_report_axes(db, company.id, scores),
        axis_comments=get_axis_comments(db, company.id),
        axis_analysis=axis_analysis,
    )
