"""Build the restricted diagnostic payload sent to the SWOT AI service."""

from app.services.report_ai_payload import FINANCIAL_FIELDS


def make_swot_ai_payload(context, financial_years):
    """Keep identifiers, contact data and arbitrary free text out of the AI request."""
    return {
        "selected_axes": [
            {"axis": item["axis_name"]}
            for item in context.get("selected_axes", [])
        ],
        "axis_scores": [
            {
                "axis": item["axis_name"],
                "percentage": item["percentage"],
                "answered_questions": item["answered_questions"],
            }
            for item in context.get("axis_scores", [])
        ],
        "answer_scores": [
            {
                "axis": item["axis_name"],
                "score_value": item["score_value"],
                "max_score": item["max_score"],
                "suggested_swot_type": item["suggested_swot_type"],
            }
            for item in context.get("diagnostic_answers", [])
        ],
        "financial_years": [
            {
                "year": row.year,
                "kind": row.kind,
                **{
                    field: str(getattr(row, field)) if getattr(row, field) is not None else None
                    for field in FINANCIAL_FIELDS
                },
            }
            for row in financial_years
        ],
    }
