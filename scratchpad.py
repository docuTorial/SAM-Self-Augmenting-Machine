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
             For instance, do not use python``` ```
             (2) Fix your python script, I wrote some comments such as TODO and FIX.
             (3) Add a clear log to help monitor everythin.
             When a user sends a message.
             When the AI thinks or decides.
             When the AI takes an action.
             Then the AI accesses data.
             All this needs to be logged to a log file named with the date.
             Each action the AI takes should be mentioned as a comment # ...
             During the conversation
             For instance: # Sam is reading a file
             # Sam is rewriting a file
             And such
             # Sam is preparing requirements
             (4) Add a simple option to exit() the chat and inform the user about it at the beginning of the conversation.
             The script allows a user and an `openai/gpt-4o` model to have natural conversation.
             (5) If the AI wants to do something like write a test or another code file:
             # Sam wants to write a test in {{filename}}
             # Sam wants to write code into {{filename}}
             (6) Sam can run tests and read their output files and report what happened.
             (7) Sam should also be able to ask to write additional helper code files.
             Code that needs to be updated:
             {open('chatbot.py').read()}
             """
            )
        }
    ]
).choices[0].message.content

print(response)
open('chatbot.py', 'w').write(response)