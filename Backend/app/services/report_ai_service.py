from app.services.azure_openai_service import generate_json_response


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


def generate_report_draft(report_context: dict) -> dict:
    system_prompt = """
You are a professional business diagnostic consultant.

You write a clear, structured, and actionable company diagnostic report in French.

Use only the data provided in the report context.
Do not invent facts.
If information is missing, do not pretend it exists.
Do not mention that data is missing unless it is important for the recommendation.

The report is for a company manager and a consultant.
The writing style must be professional, clear, and easy to read.

Return only valid JSON.
Do not use markdown code fences.
Do not add text outside the JSON.

IMPORTANT:
Every value in the JSON must be a plain text string.
Do not return nested objects.
Do not return arrays/lists.
Use line breaks and bullet points inside the string when needed.

Expected JSON format:
{
  "title": "Rapport de diagnostic — Nom de l'entreprise",
  "executive_summary": "Plain text only",
  "diagnostic_summary": "Plain text only",
  "swot_summary": "Plain text only",
  "recommendations": "Plain text only",
  "conclusion": "Plain text only"
}

CONTENT RULES:

1. title
Write a short title with the company name.
Example:
"Rapport de diagnostic — Nom de l'entreprise"

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

Commentaires importants
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

Use the existing SWOT data if provided.
Do not invent SWOT elements.

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
        user_payload=report_context,
    )

    return {
        "title": convert_ai_value_to_text(
            ai_result.get("title", "Rapport de diagnostic")
        ),
        "executive_summary": convert_ai_value_to_text(
            ai_result.get("executive_summary", "")
        ),
        "diagnostic_summary": convert_ai_value_to_text(
            ai_result.get("diagnostic_summary", "")
        ),
        "swot_summary": convert_ai_value_to_text(
            ai_result.get("swot_summary", "")
        ),
        "recommendations": convert_ai_value_to_text(
            ai_result.get("recommendations", "")
        ),
        "conclusion": convert_ai_value_to_text(
            ai_result.get("conclusion", "")
        ),
    }