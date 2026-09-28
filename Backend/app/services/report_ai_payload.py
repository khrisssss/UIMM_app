"""Allowlist the data sent to the external AI report service.

This intentionally excludes company identity, company IDs, arbitrary notes,
comments, answers and SWOT prose, which can contain identifying details.
"""

FINANCIAL_FIELDS = (
    "revenue", "ebitda", "operating_result", "net_result", "depreciation",
    "cash_flow", "equity", "gross_debt", "gross_cash", "factoring",
    "total_assets", "capex", "debt_repayments",
)


def make_report_ai_payload(report_context, financial_years):
    return {
        "company": "Entreprise anonymisée",
        "scores": [
            {
                "axis": item["axis_name"],
                "percentage": item["score_percentage"],
                "answered_questions": item["answered_questions"],
                "total_questions": item["total_questions"],
            }
            for item in report_context.get("scores", [])
        ],
        "financial_years": [
            {
                "year": row.year,
                "kind": row.kind,
                **{
                    field: str(value) if value is not None else None
                    for field in FINANCIAL_FIELDS
                    for value in (getattr(row, field),)
                },
            }
            for row in financial_years
        ],
    }
