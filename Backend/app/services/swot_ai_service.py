from app.services.azure_openai_service import generate_json_response
#from app.services.ollama_service import generate_ollama_json


def generate_swot_with_ai(swot_context: dict) -> dict:
    system_prompt = """
You are a professional business diagnostic consultant.

You generate a SWOT analysis from structured diagnostic data.

Rules:
- Use only the provided data.
- Do not invent facts.
- Use all provided anonymized profile, answers, comments, selected axes, scores, and financial years.
- Treat actual and forecast financial years separately; forecasts are not established results.
- Do not infer a Finance questionnaire score from financial figures.
- High scores or supported financial trends can become strengths.
- Low scores or supported financial trends can become weaknesses.
- Medium scores or supported improvement potential can become opportunities.
- Only supported risks or adverse trends can become threats.
- Leave a category empty if the available evidence does not support it.
- Write in professional French.
- Keep each item clear and concise.
- Return only valid JSON.
- Do not use markdown.

Expected JSON format:
{
  "strengths": ["..."],
  "weaknesses": ["..."],
  "opportunities": ["..."],
  "threats": ["..."]
}
"""


    return generate_json_response(
        system_prompt=system_prompt,
        user_payload=swot_context,
    )

#def normalize_swot_section(value):
#    """Store one finding per line, including axis labels when AI groups findings."""
#    if isinstance(value, dict):
#        return "\n".join(
#            f"{axis} : {item}"
#            for axis, entries in value.items()
#            for item in (entries if isinstance(entries, list) else [entries])
#            if isinstance(item, str) and item.strip()
#        )
#    if isinstance(value, list):
#        return "\n".join(item.strip() for item in value if isinstance(item, str) and item.strip())
#    return value.strip() if isinstance(value, str) else ""
