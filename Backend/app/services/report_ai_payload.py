"""Prepares the information for AI report generation. Its redact_text() function hides known company names, contact names, emails, phones and addresses in the text."""

import re

def redact_text(value, company):
    """Hide the company's name, contact name, email, phone and address
    when they appear in the text (function masks those details inside answers and comments), before sending it to the AI agent."""    
    #example 
    # Original:
    #“ABC Industrie, managed by Marie Dupont, wants to recruit.”
    #Sent to AI:
    #“[masqué], managed by [masqué], wants to recruit.”


    label = str(value or "")
    for field in ("name", "contact_name", "contact_email", "contact_phone", "address"):
        identifier = str(company.get(field) or "").strip()
        if identifier:
            label = re.sub(re.escape(identifier), "[masqué]", label, flags=re.I)
    label = re.sub(r"\\b[\\w.+-]+@[\\w.-]+\\.[a-zA-Z]{2,}\\b", "[email masqué]", label)
    label = re.sub(r"(?<!\\w)(?:\\+\\d{1,3}[ .-]?)?(?:\\d[ .-]?){9,12}(?!\\w)", "[téléphone masqué]", label)
    return label[:2000]
    # label = str(value or ""): converts the value into text; missing values become ""
 # it will loop The for field ... loop looks for the company’s saved name, contact name, email, phone and address inside that text. then it will masque

def make_report_ai_payload(report_context):
    """It means only diagnostic answers that have a score are included. 
    A score of 0 is included, but an answer with no score is excluded—even 
    if it contains useful text or a comment."""
    company = report_context.get("company") or {}
    return {
        "company": "Entreprise anonymisée", # Uses a generic name instead of the real name.
        "selected_axes": [  # Axes selected for the diagnostic and their comments. example Stratégie — “La vision doit être mieux partagée.”
            {"axis": item["axis_name"], "comment": redact_text(item.get("diagnostic_comment"), company)}
            for item in report_context.get("selected_axes", [])
        ],
        "scores": [ # Overall result and completion for each axis. example Stratégie: 70%, 8 questions answered out of 10.
            {
                "axis": item["axis_name"],
                "percentage": item["score_percentage"],
                "answered_questions": item["answered_questions"],
                "total_questions": item["total_questions"],
            }
            for item in report_context.get("scores", [])
        ],
        "diagnostic_questions": [ #Individual questions, answers, scores and comments. example : “La stratégie est-elle écrite ?” → “Oui”, 4/5.
            {
                "axis": item["axis"],
                "question": redact_text(item["question"], company),
                "score": item["score_value"],
                "answer": redact_text(item.get("answer_text"), company),
                "comment": redact_text(item.get("comment"), company),
            }
            for item in report_context.get("diagnostic_answers", [])
            if item.get("score_value") is not None # only diagnostic answers that have a score are included. A score of 0 is included, but an answer with no score is excluded—even if it contains useful text or a comment. 
                                                    #However, in the application if you add a comment to a question you will receive a notif that you need to add a score too 
        ],
        "company_context": { # Company size, RSE status, constraints and general comment. example 11–50 employees; RSE: yes
            "size": company.get("company_size"),
            "has_rse": company.get("has_rse"),
            "regulatory_constraints": redact_text(company.get("specific_regulatory_constraints"), company),
            "general_comment": redact_text(company.get("general_comment"), company),
        },
        "company_profile": [ # Profile questions, answers and comments, grouped by section. exapmle Activity → “Fabrication de pièces métalliques.” 
            {
                "section": redact_text(item.get("section"), company),
                "question": redact_text(item.get("question"), company),
                "answer": redact_text(item.get("answer"), company),
                "comment": redact_text(item.get("comment"), company),
            }
            for item in report_context.get("company_profile", [])
        ],
        "saved_swot": { # Strengths, weaknesses, opportunities and threats already saved. exapme Force → “Équipe expérimentée.”
            key: [redact_text(value, company) for value in (report_context.get("swot") or {}).get(key, [])]
            for key in ("strengths", "weaknesses", "opportunities", "threats")
        },
    }
