from openai import OpenAI
import os
import subprocess


def list_files(response):
    return ', '.join(os.listdir())


def ask_permission_from_user(question):
    return input(f'{question}\nType yes to confirm:\n').lower().strip() == 'yes'


def assistant_say(*args, **kwargs):
    print(*args, **kwargs)


def chat_say(contents, chat_method=assistant_say):
    return chat_method(contents)


def parse_chat(response, chat_method):
    return chat_say(response.strip().split('/chat ')[1].strip(), chat_method)


def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()


def parse_read(response):
    return read_file(response.strip().split('/read ')[1].strip())


def clean_markdown(code_reply):
    PYTHON = 'python'
    if "```" in code_reply:
        code_reply = code_reply.split("```")[1]
    if code_reply.startswith(PYTHON):
        code_reply = code_reply[len(PYTHON):]
    return code_reply


def write_file(filename, file_contents):
    if (not os.path.exists(filename) or
        ask_permission_from_user(
            f"Do you allow me to overwrite {filename}?")):
        with open(filename, 'w') as f:
            f.write(clean_markdown(file_contents))
        return f"The file {filename} was written successfully"
    return f"Failed to write to {filename}"


def parse_write(response):
    lines = response.splitlines()
    filename = lines[0].strip().split('/write ')[1].strip()
    contents = '\n'.join(lines[1:])
    return write_file(filename, contents)


def run_file(filename):
    # Path to the Python script you want to run
    script_path = os.path.abspath(filename)

    # Use subprocess to open a new CMD window and run the Python script
    subprocess.Popen(f'start cmd /k python "{script_path}"', shell=True)
    return f"The file {filename} was ran, please now list files and read its logs."


def parse_run(response):
    return run_file(response.strip().split('/run ')[1].strip())


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("SAM_OPENROUTER"))


SYSTEM = (
"""
You chat, read, write, run and explain Python code.
Only do one action at a time. Never do two or more things!

All your code must always:
- Be highly testable.
- Include a lot of logging when needed to make debugging a breeze!
- Have clear comments and proper doccumentation (both must include appropriate emojis).

To chat simply write your message or:
/chat
To explicitly say somethin (always better to simply say something).

To list files in the current directory:
/list

To read a file do:
/read {filename}
For example:
/read bobo.txt

To write a file do:
/write {filename}
{file contents}
File contents can be multiple lines long
Example:
/write bobo.py
print('Bobo is a great guy!')
print('Have a great day, Bobo.')

To run a file:
/run {filename}
Example:
/run bobo.py
""")


MESSAGES = [
        {
            'role': 'system',
            'content': SYSTEM
        }
    ]


MODEL = "openai/gpt-4o"


VERBS = {
    '/chat': chat_say,
    '/list': list_files,   
    '/read': parse_read,   
    '/write': parse_write, 
    '/run': parse_run      
}

def chat(model, messages, prompt, verbs):
    messages.append({
            'role': 'user',
            'content': prompt})
    
    response = client.chat.completions.create(
    model=model,
    temperature=0, # This is import for accurate answers
    top_p=0,       # Similar to temperature
    messages=messages
    ).choices[0].message.content
    print(f'Assistant:{response}')
    messages.append({
            'role': 'assistant',
            'content': response})


    for a_verb, a_func in verbs.items():
        if response.startswith(a_verb):
            method = a_func
            result = method(response)
            print(f"*Assistant used {a_verb[1:]}*")
            print(result)
            chat(model, messages, result, verbs)
            break


print(__name__)
if __name__ == "main":
    while True:
        chat(MODEL, MESSAGES, input('User:'), VERBS)

        
   