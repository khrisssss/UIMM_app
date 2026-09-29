"""Allowlist diagnostic evidence for the report AI without company identifiers."""

import re

FINANCIAL_FIELDS = (
    "revenue", "ebitda", "operating_result", "net_result", "depreciation",
    "cash_flow", "equity", "gross_debt", "gross_cash", "factoring",
    "total_assets", "capex", "debt_repayments",
)


def safe_question_label(value, company):
    """Use question wording only, removing known identity strings and contact patterns."""
    label = str(value or "")
    for field in ("name", "contact_name", "contact_email", "contact_phone", "address"):
        identifier = str(company.get(field) or "").strip()
        if identifier:
            label = re.sub(re.escape(identifier), "[masqué]", label, flags=re.I)
    label = re.sub(r"\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b", "[email masqué]", label)
    label = re.sub(r"(?<!\w)(?:\+\d{1,3}[ .-]?)?(?:\d[ .-]?){9,12}(?!\w)", "[téléphone masqué]", label)
    return label[:300]


def make_report_ai_payload(report_context, financial_years):
    company = report_context.get("company") or {}
    return {
        "company": "Entreprise anonymisée",
        "selected_axes": [
            {"axis": item["axis_name"]}
            for item in report_context.get("selected_axes", [])
        ],
        "scores": [
            {
                "axis": item["axis_name"],
                "percentage": item["score_percentage"],
                "answered_questions": item["answered_questions"],
                "total_questions": item["total_questions"],
            }
            for item in report_context.get("scores", [])
        ],
        "diagnostic_questions": [
            {
                "axis": item["axis"],
                "question": safe_question_label(item["question"], company),
                "score": item["score_value"],
            }
            for item in report_context.get("diagnostic_answers", [])
            if item.get("score_value") is not None
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
