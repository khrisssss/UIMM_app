"""Build the restricted diagnostic payload sent to the SWOT AI service."""

from app.services.report_ai_payload import FINANCIAL_FIELDS, redact_text


def make_swot_ai_payload(context, financial_years):
    """Keep identifiers, contact data and arbitrary free text out of the AI request."""
    company = context.get("company") or {}
    return {
        "selected_axes": [
            {"axis": item["axis_name"], "comment": redact_text(item.get("diagnostic_comment"), company)}
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
                "question": redact_text(item.get("question_text"), company),
                "answer": redact_text(item.get("answer_text"), company),
                "comment": redact_text(item.get("comment"), company),
                "score_value": item["score_value"],
                "max_score": item["max_score"],
                "suggested_swot_type": item["suggested_swot_type"],
            }
            for item in context.get("diagnostic_answers", [])
        ],
        "company_context": {
            "size": company.get("company_size"),
            "has_rse": company.get("has_rse"),
            "regulatory_constraints": redact_text(company.get("specific_regulatory_constraints"), company),
            "general_comment": redact_text(company.get("general_comment"), company),
        },
        "company_profile": [
            {"section": redact_text(item.get("section"), company),
             "question": redact_text(item.get("question"), company),
             "answer": redact_text(item.get("answer"), company)}
            for item in context.get("company_profile", [])
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
