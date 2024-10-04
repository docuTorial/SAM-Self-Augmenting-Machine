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
             (2) Fix your python script,I wrote some comments such as TODO and FIX.
             
             The script allows a user and an `openai/gpt-4o` model to have natural conversation.
             Each time the user sends a message, another `openai/gpt-4o` examines the chat so far.
             It returns `1` if it appears the user is asking the AI to update its code with some new features.
             If `1` is returned by the helper, another third `openai/gpt-4o` checks the conversation and prepares
             a list of requirements add since the last update.
             Now the first AI presents these requirements to the user and asks them to approve by typing `yes`
             or to type anything else to decline and continue the conversation normally.
             If the user approves, the AI will send the existing code and requirements to a `openai/o1-preview` as a clear prompt.\
             That `o1-preview` will rewrite the code. The code it returns will overwrite the existing `chatbot.py` and will be comitted to git.
             Before that happens, the system will update a readme.md with a new version number, starting from 0.1.0 at first.
             Newer version numbers will be decided by a dedicated AI helper that will get all the needed details.
             PythonGit will be used to commit and push changes!
             
             The user will also be able to ask the assistants write *tests* and run these tests.
             Such tests can be saved in any '.py' file name.
             The tests will always outputs {{filename}}_results_{{date}}.test to test_log folder.
             You must return the python script and only the python script, no other text or markup.
             Please add comments and detailed explanations for each part of the code.
             Also, please leave a clear designated room for the user to comment on each part of the code.
             When the assistant makes changes to the code, they'll commit them to git with **PythonGit**.
             They will also create a readme.md explaining the features and the changes that were recently made and specifying a new version number.
             
             Code that needs to be updated:
             {open('chatbot.py').read()}
             """
            )
        }
    ]
).choices[0].message.content

print(response)
open('chatbot.py', 'w').write(response)