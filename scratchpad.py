from openai import OpenAI
import os
import subprocess


def list_files(response):
    print(f"* Assistnat is listing files *")
    return ', '.join(os.listdir())


def ask_permission_from_user(question):
    user_input = input(f'{question}\nType yes to confirm:\n')
    if user_input.lower().strip()  == 'yes':
        return True
    else:
        return user_input


def assistant_say(*args, **kwargs):
    contents, *rest = args
    print(*([f"Assistnat: {contents}"] + rest), **kwargs)
    return "Message sent successfully."


def parse_chat(response, chat_method=assistant_say):
    return chat_method(response.strip().split('/chat ')[1].strip())


def read_file(filename):
    print(f"* Assistnat read {filename} *")
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
        (user_said := ask_permission_from_user(
            f"* Assistant wants to overwrite {filename} *")) == True):
        print(f"* Assistnat wrote {filename} *")
        with open(filename, 'w') as f:
            f.write(clean_markdown(file_contents))
        return f"The file {filename} was written successfully"
    return f"Failed to write to {filename}.\nUser:{user_said}"


def parse_write(response):
    lines = response.splitlines()
    filename = lines[0].strip().split('/write ')[1].strip()
    contents = '\n'.join(lines[1:])
    return write_file(filename, contents)


def run_file(filename):
    print(f"* Assistnat ran {filename} *")
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
You are SAM, a self-augmenting-machine.
Please don't apologize. Be confident.
You modify your own code and also write brand new code.
Use lots of emoji.
You ask at most one question at a time.
You always keep it pretty short when you chat.
Chat, read files, write files, run python and explain code. :)
Never say anything before or after an action. An action is always the first, last, and only thing in a message.
Only perform one single action per message. Never do two or more things in a message!
When you write a regular code file, you always want to write a python test file in the next message.
Test files should generate log result files so you could read them and see if the tests passed.

If a user said `help` explicitly:
Let them know what you, SAM, can do and remind them that they can leave the chat at any time with
/exit

If you do /exit, simply answer:
/exit
Do not write anything before /exit

All your code must always:
- Be highly testable.
- Include a lot of logging when needed to make debugging a breeze!
- Have clear comments and proper doccumentation in everything (also must include lots of appropriate emojis).

To chat:
/chat {message contents}
Example:
/chat Hello friend!
How are you all doing?


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


SYSTEM_SUFFIX = "Please move on directly to the next action."


MESSAGES = [
        {
            'role': 'system',
            'content': SYSTEM
        }
    ]


MODEL = "openai/gpt-4o"


EXIT = 'exit'


VERBS = {
    '/chat': parse_chat,
    '/list': list_files,   
    '/read': parse_read,   
    '/write': parse_write, 
    '/run': parse_run,
    '/exit': EXIT
}

def chat(model, messages, prompt, verbs):
    if prompt == "/exit":
        return False
    
    messages.append({
            'role': 'user',
            'content': prompt})
    
    response = client.chat.completions.create(
    model=model,
    temperature=0, # This is import for accurate answers
    top_p=0,       # Similar to temperature
    messages=messages
    ).choices[0].message.content

    messages.append({
            'role': 'assistant',
            'content': response})

    for a_verb, a_func in verbs.items():
        if response.startswith(a_verb):
            method = a_func
            if type(method) is str and method == EXIT:
                return False
            try:
                if a_verb != "/chat":
                    result = f"[Computer:]\n{method(response)}\n\n({SYSTEM_SUFFIX})"
                    #print(f"*Assistant used {a_verb[1:]}*")
                    print(result)
                    chat(model, messages, result, verbs)
                else:
                    method(response)
            except:
                result = f"C[omputer:]\nYou failed to perform:\n{a_verb[1:]}.\n==response==\n{response}\n==was invalid=="
                print(f"* Assistant failed to {a_verb[1:]} *")
            break
    else:
        print(f"Assistant:{response}")


    return True


if __name__ == "__main__":
    while chat(MODEL, MESSAGES, input('User:'), VERBS):
        pass # Run the bot until the user /exit

