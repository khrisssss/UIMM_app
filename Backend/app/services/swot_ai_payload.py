"""Prepares the information to send to the AI for SWOT generation, (readact_text)hiding company and contact details."""

from app.services.report_ai_payload import FINANCIAL_FIELDS, redact_text # redact text hides the name of the company before sending it to ai 


def make_swot_ai_payload(context, financial_years):
    """Prepare diagnostic and financial information for AI SWOT generation,
    masking [masqué] known company names, contact names, emails, phones and addresses
    when they appear in the text."""
    #example 
    #Before: “ABC Métal wants to recruit.”
    #After:  “[masqué] wants to recruit.”
    #Other detected emails and phone numbers are replaced with [email masqué] and [téléphone masqué].
    company = context.get("company") or {}
    has_diagnostic_evidence = any(
        item.get("score_value") is not None or item.get("answer_text") or item.get("comment")
        for item in context.get("diagnostic_answers", [])
    )
    public_only = not has_diagnostic_evidence and any(
        "recherche documentaire publique" in str(item.get("question", "")).casefold()
        for item in context.get("company_profile", [])
    )
    return {
        "evidence_basis": {
            "mode": "public_sources_only" if public_only else "diagnostic",
            "assessment_status": "not_assessed" if public_only else "to_review",
            "note": "Pré-analyse documentaire publique à valider ; aucune réponse interne ni maturité déduite des données manquantes." if public_only else "Constats limités aux éléments fournis.",
        },
        "selected_axes": [ # Which axes did you select? Includes the general comment written for each axis. #examplke Stratégie — “La stratégie doit être mieux partagée.” 
            {"axis": item["axis_name"], "comment": redact_text(item.get("diagnostic_comment"), company)}
            for item in context.get("selected_axes", [])
        ],
        "axis_scores": [ # What is the overall result for each axis? example Stratégie: 70%, with 10 questions answered.
            {
                "axis": item["axis_name"],
                "percentage": item["percentage"],
                "answered_questions": item["answered_questions"],
            }
            for item in context.get("axis_scores", [])
            if (item.get("answered_questions") or 0) > 0
        ],
        "answer_scores": [ #What did you answer for each question? example “La stratégie est-elle écrite ?” → “Oui, mais elle n’est pas actualisée.” Score: 3 out of 5. Comment: “Dernière mise à jour en 2023.”
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
        "company_context": { # Basic information about the company’s situation. example Size: 11–50 employees. RSE approach: yes. General comment: “L’entreprise souhaite se développer.”
            "size": company.get("company_size"),
            "has_rse": None if public_only else company.get("has_rse"),
            "regulatory_constraints": redact_text(company.get("specific_regulatory_constraints"), company),
            "general_comment": redact_text(company.get("general_comment"), company),
        },
        "company_profile": [ # Your answers to the company profile questions. example “Quelle est l’activité de l’entreprise ?” → “Fabrication de pièces métalliques.”
            {"section": redact_text(item.get("section"), company),
             "question": redact_text(item.get("question"), company),
             "answer": redact_text(item.get("answer"), company)}
            for item in context.get("company_profile", [])
        ],
        "financial_years": [ # The financial numbers you saved example 2025, actual: revenue €2,400,000. 2026, forecast: revenue €2,600,000.
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
