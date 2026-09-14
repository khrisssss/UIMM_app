from app.services.azure_openai_service import generate_json_response
#from app.services.ollama_service import generate_ollama_json


def generate_swot_with_ai(swot_context: dict) -> dict:
    system_prompt = """
You are a professional business diagnostic consultant.

You generate a SWOT analysis from structured diagnostic data.

Rules:
- Use only the provided data.
- Do not invent facts.
- Use the questionnaire scores, comments, axis scores, and company profile.
- High scores and positive comments can become strengths.
- Low scores and negative comments can become weaknesses.
- Medium scores or improvement comments can become opportunities.
- Risks, blocking points, very low scores, or risk comments can become threats.
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