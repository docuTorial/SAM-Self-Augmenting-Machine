from openai import OpenAI
from os import getenv

client=OpenAI(
	base_url="https://openrouter.ai/api/v1",
	api_key=getenv("SAM_OPENROUTER")
    )

response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[
        {
            "role": "user",
            "content": (
             """Two words often printed by
                the first program someone writes
                in a newly learned language?"""
            )
        }
    ]
).choices[0].message.content

print(response)