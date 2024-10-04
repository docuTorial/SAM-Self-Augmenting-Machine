from openai import OpenAI
from os import getenv

client=OpenAI(
	base_url="https://openrouter.ai/api/v1",
	api_key=getenv("SAM_OPENROUTER")
    )

response = client.chat.completions.create(
    model="openai/o1-preview",
    messages=[
        {
            "role": "user",
            "content": (
             f"""
             (1) Reply only with python code and no other text or markup.
             (2) Fix your python script, I wrote some comments such as TODO and FIX.
             (3) Add an option for the AI to /exec some python code if the user requests.
             (4) There is a bug:
                 updated_code = re.sub(r'.*?\n(.*?)
                 That line of code is completely broken. Fix it.

             {open('chatbot.py').read()}
             """
            )
        }
    ]
).choices[0].message.content

print(response)
open('chatbot.py', 'w').write(response)