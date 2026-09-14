# import os
# import json
# import requests
# from dotenv import load_dotenv

# load_dotenv()

# OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")


# def call_ollama(prompt: str) -> str:
#     url = f"{OLLAMA_BASE_URL}/api/generate"

#     payload = {
#         "model": OLLAMA_MODEL,
#         "prompt": prompt,
#         "stream": False,
#         "options": {
#             "temperature": 0.3,
#         },
#     }

#     try:
#         response = requests.post(url, json=payload, timeout=500)
#         response.raise_for_status()
#     except requests.exceptions.RequestException as error:
#         raise RuntimeError(f"Ollama request failed: {error}")

#     data = response.json()

#     if "response" not in data:
#         raise RuntimeError("Ollama response did not contain a 'response' field.")

#     return data["response"]


# def extract_json_from_text(text: str) -> dict:
#     try:
#         return json.loads(text)
#     except json.JSONDecodeError:
#         pass

#     start_index = text.find("{")
#     end_index = text.rfind("}")

#     if start_index == -1 or end_index == -1 or end_index <= start_index:
#         raise ValueError("No valid JSON object found in Ollama response.")

#     json_text = text[start_index : end_index + 1]

#     return json.loads(json_text)