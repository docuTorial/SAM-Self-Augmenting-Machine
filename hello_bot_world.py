from openai import OpenAI
from os import getenv

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=getenv("SAM_OPENROUTER"))


REQUEST = (
"""
The correct reply is only two words.
It is a famous pair of words often printed by a first program.
The first word is like "hi".
The second word is kind of like "planet".
Please reply with only the correct two words. :)
"""
)


response = client.chat.completions.create(
    model="openai/gpt-4o",
    temperature=0, # This is import for accurate answers
    top_p=0, # Similar to temperature
    messages=[
        {
            "role": "user",
            "content": REQUEST
        }]
    ).choices[0].message.content

print(response)