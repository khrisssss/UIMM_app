import json

from app.services.azure_openai_service import generate_json_response
from app.services.report_ai_payload import make_report_ai_payload


def convert_ai_value_to_text(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        lines = []

        for item in value:
            if isinstance(item, str):
                lines.append(f"- {item.strip()}")
            else:
                lines.append(f"- {convert_ai_value_to_text(item)}")

        return "\n".join(lines).strip()

    if isinstance(value, dict):
        lines = []

        for key, item_value in value.items():
            lines.append(str(key))

            if isinstance(item_value, list):
                for item in item_value:
                    lines.append(f"- {convert_ai_value_to_text(item)}")
            else:
                text_value = convert_ai_value_to_text(item_value)
                if text_value:
                    lines.append(text_value)

            lines.append("")

        return "\n".join(lines).strip()

    return str(value).strip()


def generate_report_draft(report_context: dict, financial_years=()) -> dict:
    system_prompt = """
You are a professional business diagnostic consultant.

You write a clear, structured, and actionable company diagnostic report in French.

Use all anonymized evidence provided: company context, profile answers, diagnostic answers and comments, selected-axis comments, scores, saved SWOT, and financial years. Synthesize these into conclusions; do not reproduce a questionnaire as question and answer.
Do not invent facts.
If information is missing, do not pretend it exists.
Do not mention that data is missing unless it is important for the recommendation.

The report is for a company manager and a consultant.
The writing style must be professional, clear, and easy to read.

Return only valid JSON.
Do not use markdown code fences.
Do not add text outside the JSON.

IMPORTANT:
All fields except axis_analysis and presentation_content must be plain text strings.
axis_analysis is an object keyed by each supplied axis name; each axis has arrays of concise French findings.
presentation_content is an object of short narrative paragraphs for the presentation and enjeux slides.
Use line breaks and bullet points inside the string when needed.

Expected JSON format:
{
  "title": "Rapport de diagnostic — Entreprise anonymisée",
  "executive_summary": "Plain text only",
  "diagnostic_summary": "Plain text only",
  "axis_analysis": {"Stratégie": {"strengths": ["Statement"], "weaknesses": [], "opportunities": [], "threats": []}},
  "presentation_content": {"history": "", "activity": "", "managers": "", "initial_expectation": "", "situation": "", "governance": "", "future": ""},
  "swot_summary": "Plain text only",
  "recommendations": "Plain text only",
  "conclusion": "Plain text only"
}

CONTENT RULES:

1. title
Write a generic title without identifying details.
Example:
"Rapport de diagnostic — Entreprise anonymisée"

2. executive_summary
Write a short executive summary.
Maximum 2 short paragraphs.
It should explain:
- the general situation of the company
- the main diagnostic message
- the main point of attention

3. diagnostic_summary
Write a structured diagnostic summary as plain text.
Use this style:

Analyse globale
Short paragraph.

Axes les plus solides
- bullet point
- bullet point

Axes à renforcer
- bullet point
- bullet point

Constats étayés par les données
- bullet point
- bullet point

4. swot_summary
Write a clear SWOT summary as plain text.
Use this style:

Forces
- bullet point

Faiblesses
- bullet point

Opportunités
- bullet point

Menaces
- bullet point

The saved SWOT is provided for context and added locally after your response. Do not invent SWOT elements.

For presentation_content, synthesize the profile and diagnostic evidence into natural French prose.
Use history, activity, managers, initial_expectation, situation, governance, and future only when the supplied evidence supports them.
Do not copy question wording, fabricate names, or infer historical facts from scores. Use an empty string if absent.
Keep each paragraph short enough for a presentation slide.

For axis_analysis, write professional conclusions in French, as in a consultant's restitution.
Never repeat the question wording, show a score in a finding, or format as a question and answer.
Ground each finding in the supplied answers, comments, scores, profile, SWOT, or financial figures. Explain the business implication rather than merely restating a score.
Do not turn a question into a factual claim solely because it was asked.
Use only the six selected diagnostic axes: Stratégie, Performance, Marketing, RH, Digitalisation and RSE. Do not add a Finance axis.
At most two short findings per SWOT category and axis, each under 140 characters. If an axis has no usable evidence, use empty arrays. Do not invent interviews.

5. recommendations
Write concrete and actionable recommendations as plain text.
Use this style:

Priorité 1 — Actions à court terme
- action
- action

Priorité 2 — Actions à moyen terme
- action
- action

Priorité 3 — Actions de consolidation
- action
- action

6. conclusion
Write one short professional closing paragraph.
"""

    ai_result = generate_json_response(
        system_prompt=system_prompt,
        user_payload=make_report_ai_payload(report_context, financial_years),
    )

    raw_axes = ai_result.get("axis_analysis")
    axis_names = {
        item["axis_name"] for item in report_context.get("selected_axes", [])
    }
    axis_analysis = {}
    if isinstance(raw_axes, dict):
        for axis_name in axis_names:
            findings = raw_axes.get(axis_name)
            if isinstance(findings, dict):
                axis_analysis[axis_name] = {
                    key: [str(value).strip() for value in findings.get(key, []) if isinstance(value, str) and value.strip()][:5]
                    if isinstance(findings.get(key), list) else []
                    for key in ("strengths", "weaknesses", "opportunities", "threats")
                }

    raw_presentation = ai_result.get("presentation_content")
    raw_presentation = raw_presentation if isinstance(raw_presentation, dict) else {}
    presentation_content = {
        key: convert_ai_value_to_text(raw_presentation.get(key, ""))[:1000]
        for key in ("history", "activity", "managers", "initial_expectation", "situation", "governance", "future")
    }

    saved_swot = report_context.get("swot") or {}
    swot_sections = (
        ("Forces", "strengths"), ("Faiblesses", "weaknesses"),
        ("Opportunités", "opportunities"), ("Menaces", "threats"),
    )
    local_swot_summary = "\n\n".join(
        heading + "\n" + "\n".join("- " + str(item) for item in saved_swot.get(key, []) if str(item).strip())
        for heading, key in swot_sections
    ) if saved_swot else ""

    return {
        "title": convert_ai_value_to_text(
            ai_result.get("title", "Rapport de diagnostic")
        ),
        "executive_summary": convert_ai_value_to_text(
            ai_result.get("executive_summary", "")
        ),
        "axis_analysis": json.dumps(axis_analysis, ensure_ascii=False),
        "presentation_content": json.dumps(presentation_content, ensure_ascii=False),
        "diagnostic_summary": convert_ai_value_to_text(
            ai_result.get("diagnostic_summary", "")
        ),
        "swot_summary": local_swot_summary or convert_ai_value_to_text(
            ai_result.get("swot_summary", "")
        ),
        "recommendations": convert_ai_value_to_text(
            ai_result.get("recommendations", "")
        ),
        "conclusion": convert_ai_value_to_text(
            ai_result.get("conclusion", "")
        ),
    }