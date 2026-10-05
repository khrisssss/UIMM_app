#from openai import OpenAI

#endpoint = ""
#deployment_name = ""
#api_key = "

#client = OpenAI(
#"    base_url=endpoint,
#    api_key=api_key
#)

#response = client.responses.create(
#    model=deployment_name,
#    input="when was the ladt update of gpt 4 in azure " \
#    ",",
#)

#print(f"answer: {response.output[0]}")

# this is just a TEST to see if i can connect to azure 



import os
from openai import AzureOpenAI

endpoint = ""
model_name = ""
deployment = ""

subscription_key = ""
api_version = "

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

response = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "what is the capital in philippines",
        }
    ],
  
    model=deployment
)

print(response.choices[0].message.content)