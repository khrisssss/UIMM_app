from openai import OpenAI

endpoint = ""
deployment_name = ""
api_key = ""

client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

response = client.responses.create(
    model=deployment_name,
    input="What is the capital of Philippines?",
)

print(f"answer: {response.output[0]}")

# this is just a text to see if i can connect to azure 