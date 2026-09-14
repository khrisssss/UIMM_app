import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def get_azure_client():
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT is missing in .env")

    if not api_key:
        raise ValueError("AZURE_OPENAI_API_KEY is missing in .env")

    return OpenAI(
        api_key=api_key,
        base_url=endpoint.rstrip("/") + "/",
    )


def generate_json_response(system_prompt: str, user_payload: dict) -> dict:
    model = os.getenv("AZURE_OPENAI_MODEL")

    if not model:
        raise ValueError("AZURE_OPENAI_MODEL is missing in .env")

    client = get_azure_client()

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False),
            },
        ],
    )

    output_text = response.output_text.strip()

    if output_text.startswith("```json"):
        output_text = output_text.replace("```json", "", 1).strip()

    if output_text.startswith("```"):
        output_text = output_text.replace("```", "", 1).strip()

    if output_text.endswith("```"):
        output_text = output_text[:-3].strip()

    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        return {
            "raw_output": response.output_text,
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
        }