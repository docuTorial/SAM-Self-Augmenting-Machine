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
             (3) Add a clear log to help monitor everything.
             This includes the updated code returned from the AI
             This includes anything that is sent back and forth
             Every little detail should be logged.
             When a user sends a message.
             When the AI thinks or decides.
             When the AI takes any action.
             When the AI accesses data.
             All this needs to be logged to a log file named with the date and **time**.
             Add a DEBUG_MODE const value and if it is 1 or True:
             Each action the AI takes should be printed in a comment format # {{...}}
             During the conversation
             For instance: # Sam is reading a file
             # Sam is rewriting a file
             And such
             # Sam is preparing requirements
             (4) Add an ability AI verbs to write and save and run *new* scripts. That does not require permission.
             (5) Allow to AI to run itself in a new window after an update and kill the existing window.
                 Simply ask the user for permission before doing it.
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