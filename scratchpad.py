from openai import OpenAI
import os
import subprocess


def list_files(response):
    return ', '.join(os.listdir())


def ask_permission_from_user(question):
    return input(f'{question}\ntype yes to confirm:\n').lower() == 'yes'


def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()


def parse_read(response):
    return read_file(response.split('/read ')[1])


def clean_markdown(code_reply):
    if "```" in code_reply:
        return code_reply.split("```")[1]
    else:
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
    filename = lines[0].split('/write ')[1]
    contents = '\n'.join(lines[1:])
    return write_file(filename, contents)


def run_file(filename):
    # Path to the Python script you want to run
    script_path = os.path.abspath(filename)

    # Use subprocess to open a new CMD window and run the Python script
    subprocess.Popen(f'start cmd /k python "{script_path}"', shell=True)
    return f"The file {filename} was ran, please now list files and read its logs."


def parse_run(response):
    return run_file(response.split('/run ')[1])


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("SAM_OPENROUTER"))


SYSTEM = (
"""
You write, read, run and explain Python code.
All your code must:
Be highly testable.
Include a lot of logs when needed.
Comments must include appropriate emojis.
Include a lot of documentation.

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
    '/list': list_files,
    '/read': parse_read,   # read_file,
    '/write': parse_write, # write_file,
    '/run': parse_run      # run_file
}

def chat(model, messages, prompt, verbs):
    messages.append({
            'role': 'user',
            'content': prompt})
    
    response = client.chat.completions.create(
    model=model,
    temperature=0, # This is import for accurate answers
    top_p=0, # Similar to temperature
    messages=messages
    ).choices[0].message.content
    print(f'Assistant:{response}')
    messages.append({
            'role': 'assistant',
            'content': response})
    
    for a_verb, a_func in verbs.items():
        if response.startswith(a_verb):
            method = a_func
            break
    else:
        method = None
    if method is not None:
        result = method(response)
        print(result)
        chat(model, messages, result, verbs)


while True:
    chat(MODEL, MESSAGES, input('User:'), VERBS)

        
   