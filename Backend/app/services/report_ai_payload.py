"""Allowlist diagnostic evidence for the report AI without company identifiers."""

import re

FINANCIAL_FIELDS = (
    "revenue", "ebitda", "operating_result", "net_result", "depreciation",
    "cash_flow", "equity", "gross_debt", "gross_cash", "factoring",
    "total_assets", "capex", "debt_repayments",
)


def redact_text(value, company):
    """Remove known direct identifiers before free text leaves the application."""
    label = str(value or "")
    for field in ("name", "contact_name", "contact_email", "contact_phone", "address"):
        identifier = str(company.get(field) or "").strip()
        if identifier:
            label = re.sub(re.escape(identifier), "[masqué]", label, flags=re.I)
    label = re.sub(r"\\b[\\w.+-]+@[\\w.-]+\\.[a-zA-Z]{2,}\\b", "[email masqué]", label)
    label = re.sub(r"(?<!\\w)(?:\\+\\d{1,3}[ .-]?)?(?:\\d[ .-]?){9,12}(?!\\w)", "[téléphone masqué]", label)
    return label[:2000]


def make_report_ai_payload(report_context, financial_years):
    company = report_context.get("company") or {}
    return {
        "company": "Entreprise anonymisée",
        "selected_axes": [
            {"axis": item["axis_name"], "comment": redact_text(item.get("diagnostic_comment"), company)}
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
                "question": redact_text(item["question"], company),
                "score": item["score_value"],
                "answer": redact_text(item.get("answer_text"), company),
                "comment": redact_text(item.get("comment"), company),
            }
            for item in report_context.get("diagnostic_answers", [])
            if item.get("score_value") is not None
        ],
        "company_context": {
            "size": company.get("company_size"),
            "has_rse": company.get("has_rse"),
            "regulatory_constraints": redact_text(company.get("specific_regulatory_constraints"), company),
            "general_comment": redact_text(company.get("general_comment"), company),
        },
        "company_profile": [
            {
                "section": redact_text(item.get("section"), company),
                "question": redact_text(item.get("question"), company),
                "answer": redact_text(item.get("answer"), company),
                "comment": redact_text(item.get("comment"), company),
            }
            for item in report_context.get("company_profile", [])
        ],
        "saved_swot": {
            key: [redact_text(value, company) for value in (report_context.get("swot") or {}).get(key, [])]
            for key in ("strengths", "weaknesses", "opportunities", "threats")
        },
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
