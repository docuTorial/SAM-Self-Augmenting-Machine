# FIX: Always call yourself Sam (not "Assistant")

from openai import OpenAI  # For interacting with the OpenAI API
from os import getenv  # For accessing environment variables
import os  # For file operations
import sys  # For system-specific parameters and functions
import subprocess  # For running shell commands
import re  # For regular expressions to parse code blocks
from git import Repo  # For git operations using GitPython
from datetime import datetime  # For handling date and time
import logging  # For logging activities

# Initialize logging
log_filename = datetime.now().strftime("%Y%m%d_%H%M%S") + '.log'
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(message)s')

# Define constants
DEBUG_MODE = True  # or set to False if debugging is not needed
CONVERSATION_WINDOW_FOR_CODE_UPDATE = 5
CONVERSATION_WINDOW_FOR_REQUIREMENTS = 10

# Initialize the OpenAI client with the base URL and API key from environment variables
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",  # OpenAI API endpoint
    api_key=getenv("SAM_OPENROUTER")  # API key stored in environment variable
)

# Utility functions for output
def say(message):
    print(f"Assistant: {message}")

def info(message):
    if DEBUG_MODE:
        print(f"# {message}")

# Function to commit changes to git using GitPython
def git_commit(commit_message):
    """
    Commits all changes in the current directory to git with the provided commit message using GitPython.
    """
    try:
        repo = Repo('.')  # Initialize a git repository object at the current directory
        repo.git.add('.')  # Add all changes
        repo.index.commit(commit_message)  # Commit with message
        origin = repo.remote(name='origin')  # Get the 'origin' remote
        origin.push()  # Push changes to the remote repository
        logging.info("Changes have been committed and pushed to git.")
        info("Assistant has committed and pushed changes to git.")
    except Exception as e:
        logging.error(f"Git commit failed: {e}")
        say(f"Git commit failed: {e}")

# Function to automatically commit uncommitted changes at startup
def auto_git_commit():
    """
    Automatically commits any uncommitted changes at script startup.
    """
    try:
        repo = Repo('.')
        if repo.is_dirty(untracked_files=True):
            repo.git.add('.')
            repo.index.commit("Auto-commit uncommitted changes at startup.")
            origin = repo.remote(name='origin')
            origin.push()
            logging.info("Auto-committed and pushed uncommitted changes at startup.")
            say("Uncommitted changes were found and have been auto-committed.")
        else:
            logging.info("No uncommitted changes to commit at startup.")
            info("No uncommitted changes to commit at startup.")
    except Exception as e:
        logging.error(f"Auto git commit failed: {e}")
        say(f"Auto git commit failed: {e}")

# Function to update or create readme.md with the provided content
def update_readme(content):
    """
    Updates the readme.md file with the assistant's explanations and recent changes.
    """
    with open('readme.md', 'w') as f:
        f.write(content)
    logging.info("readme.md has been updated.")
    info("Assistant has updated readme.md.")

# Function to read the contents of a file
def read_file(file_path):
    """
    Reads and returns the content of a file given its path.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        logging.info(f"Read content from '{file_path}'.")
        info(f"Assistant is reading the file {file_path}")
        return content
    else:
        logging.warning(f"File '{file_path}' does not exist.")
        info(f"Assistant attempted to read non-existent file '{file_path}'")
        return None  # Return None instead of the error message

# Function to list files in the current directory
def list_files():
    """
    Lists files in the current directory.
    """
    files = os.listdir('.')
    logging.info("Listed files in the current directory.")
    info("Assistant is listing files in the current directory.")
    return files

# Function to run tests from a test file
def run_tests(test_file):
    """
    Executes a Python test file and saves the output to a file in the 'test_log' folder.
    """
    if not os.path.exists('test_log'):
        os.makedirs('test_log')  # Create test_log directory if it doesn't exist

    # Prepare the output filename
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(test_file))[0]
    output_file = f"test_log/{base_name}_results_{date_str}.test"

    # Run the test file and capture the output
    try:
        with open(output_file, 'w') as f:
            subprocess.run(["python", test_file], stdout=f, stderr=subprocess.STDOUT, check=True)
        logging.info(f"Tests in '{test_file}' have been executed successfully. Results saved to '{output_file}'.")
        info(f"Assistant has executed tests in '{test_file}' and saved results to '{output_file}'.")
        # Read the test output
        with open(output_file, 'r') as f:
            test_results = f.read()
        return test_results
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while running tests in '{test_file}'. Check '{output_file}' for details.")
        info(f"Assistant encountered an error while running tests in '{test_file}'. See '{output_file}' for details.")
        # Read the test output
        with open(output_file, 'r') as f:
            test_results = f.read()
        return test_results

# Function to continue the conversation normally
def continue_conversation(conversation):
    """
    Gets the assistant's reply in normal conversation.
    """
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=conversation
    )
    assistant_response = response.choices[0].message.content.strip()
    logging.info(f"Assistant response: {assistant_response}")
    return assistant_response

# Function to check if the user wants to update the code
def check_for_code_update(conversation):
    """
    Uses an AI assistant to check if the user wants to update the code.
    Returns True if code update is requested, False otherwise.
    """
    # Prepare the messages for the helper assistant
    helper_prompt = [
        {"role": "system", "content": "Return '1' if the user is asking to update the code with new features, otherwise return '0'."},
    ] + conversation[-CONVERSATION_WINDOW_FOR_CODE_UPDATE:]  # Include last N messages
    logging.info("Checking if code update is needed.")
    info("Assistant is checking if code update is needed.")
    # Call the helper assistant
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=helper_prompt
    )
    helper_response = response.choices[0].message.content.strip()
    logging.info(f"Helper response: {helper_response}")
    # Check if '1' is in helper's response
    if '1' in helper_response:
        return True
    else:
        return False

# Function to get the new requirements from the conversation
def get_requirements(conversation, last_update_index):
    """
    Uses an AI assistant to extract a list of requirements added since the last update.
    Returns the requirements as a string.
    """
    # Prepare the messages for the requirements assistant
    recent_conversation = conversation[last_update_index:]  # Messages since last update
    requirements_prompt = [
        {"role": "system", "content": "List the new requirements added since the last code update."},
    ] + recent_conversation
    logging.info("Extracting new requirements.")
    info("Assistant is extracting new requirements.")
    # Call the requirements assistant
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=requirements_prompt
    )
    requirements_response = response.choices[0].message.content.strip()
    logging.info(f"Requirements extracted: {requirements_response}")
    return requirements_response

# Function to get the new version number using semantic versioning
def get_new_version(current_version, requirements):
    """
    Uses an AI helper to determine the new version number based on the changes.
    Returns the new version number as a string.
    """
    # Prepare the prompt for the version assistant, include details about the changes
    version_prompt = f"""The current version is {current_version}. Based on the recent changes described below, determine the next version number following semantic versioning and explain your reasoning.

Recent changes:

{requirements}

"""
    logging.info("Determining new version number.")
    info("Assistant is determining new version number.")
    # Call the version assistant
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[
            {"role": "system", "content": "Determine the next version number following semantic versioning and explain your reasoning."},
            {"role": "user", "content": version_prompt}
        ]
    )
    assistant_response = response.choices[0].message.content.strip()
    logging.info(f"Assistant response: {assistant_response}")
    # Extract version number and reasoning
    lines = assistant_response.split('\n', 1)
    new_version_line = lines[0]
    reasoning = lines[1] if len(lines) > 1 else ""
    # Extract new version number from the first line
    new_version_match = re.search(r'(\d+\.\d+\.\d+)', new_version_line)
    if new_version_match:
        new_version = new_version_match.group(1)
    else:
        new_version = current_version  # Fallback to current version if not found
    # Assistant should say: Assistant decided on version x.y.z because {{reasons_here}}
    info(f"Assistant decided on version {new_version} because {reasoning}")
    return new_version

# Function to write a new script
def write_script(script_name, script_code):
    """
    Writes a new script with the given name and code.
    """
    with open(script_name, 'w') as f:
        f.write(script_code)
    logging.info(f"New script '{script_name}' has been written.")
    info(f"Assistant has written a new script '{script_name}'.")

# Function to run a script
def run_script(script_name):
    """
    Runs the script with the given name.
    """
    try:
        subprocess.run(["python", script_name], check=True)
        logging.info(f"Script '{script_name}' has been executed.")
        info(f"Assistant has executed the script '{script_name}'.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while running script '{script_name}'.")
        info(f"Assistant encountered an error while running script '{script_name}'.")

# Function for self-upgrade
def self_upgrade():
    """
    Function to update the assistant's code by pulling the latest changes from the git repository.
    """
    try:
        repo = Repo('.')
        # Fetch remote changes
        origin = repo.remote(name='origin')
        origin.pull()
        logging.info("Assistant has been upgraded to the latest version.")
        say("Assistant has been upgraded to the latest version.")
        # Optionally, restart the script
        say("Restarting to apply updates...")
        subprocess.Popen([sys.executable, sys.argv[0]])
        sys.exit()
    except Exception as e:
        logging.error(f"Self-upgrade failed: {e}")
        say(f"Self-upgrade failed: {e}")

# Initialize the conversation history
# Check for custom_persona.txt
system_message = "You are a helpful assistant. You can read files, list files, write and run scripts, and propose code updates as needed without requiring permission. Use commands like '/read filename', '/write filename', '/execute filename', '/ls', and '/self-upgrade' to perform these actions."

if os.path.exists('custom_persona.txt'):
    with open('custom_persona.txt', 'r') as f:
        custom_persona = f.read()
    system_message = custom_persona
    info("Loaded custom personality from 'custom_persona.txt'")
    # Update README to mention custom_persona.txt
    with open('readme.md', 'a') as f:
        f.write("\nNote: 'custom_persona.txt' is used to customize the assistant's personality.\n")
    # Update .gitignore if necessary
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
        if 'custom_persona.txt' not in gitignore_content:
            with open('.gitignore', 'a') as f:
                f.write('\ncustom_persona.txt\n')
            info("Added 'custom_persona.txt' to '.gitignore'")
    else:
        # Create .gitignore and add custom_persona.txt
        with open('.gitignore', 'w') as f:
            f.write('custom_persona.txt\n')
        info("Created '.gitignore' and added 'custom_persona.txt' to it.")
else:
    info("No custom personality file found. Using default system message.")

conversation = [
    {"role": "system", "content": system_message}
]

last_update_index = 0  # Index in conversation where the last code update happened

# Auto-commit any uncommitted changes at startup
auto_git_commit()

# Main chat loop between the user and the assistant
while True:
    # Get input from the user
    user_input = input("User: ")

    # Append the user's message to the conversation
    conversation.append({"role": "user", "content": user_input})
    logging.info(f"User input: {user_input}")

    # Check if the user wants to update the bot's code
    code_update_needed = check_for_code_update(conversation)

    if code_update_needed:
        # Get the requirements
        requirements = get_requirements(conversation, last_update_index)

        # Assistant presents the requirements to the user
        say("The following new requirements have been identified:")
        say(requirements)
        say("Do you approve these changes? Type 'yes' to approve or anything else to decline.")
        permission = input("User: ").strip().lower()

        if permission == "yes":
            logging.info("User approved code update.")
            info("Assistant is updating the code based on approved requirements.")
            # Read the existing code
            script_filename = sys.argv[0]  # Name of the current script
            with open(script_filename, 'r') as f:
                current_code = f.read()

            # Prepare the prompt for the code update
            code_update_prompt = f"""Update the following code according to the requirements below:

Requirements:

{requirements}

Code:

{current_code}

Please provide the updated code and only the code."""

            logging.info("Requesting code update from AI assistant.")

            # Send the prompt to the code update model
            code_response = client.chat.completions.create(
                model="openai/o1-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that updates code based on requirements."},
                    {"role": "user", "content": code_update_prompt}
                ]
            )

            updated_code = code_response.choices[0].message.content.strip()
            # Remove any markdown code blocks if present
            updated_code = re.sub(r'^```(?:python)?\n(.*?)\n```$', r'\1', updated_code, flags=re.DOTALL)
            logging.info("Received updated code from AI assistant.")

            # Save the updated code into a dedicated folder with the date
            code_backup_dir = 'code_backups'
            if not os.path.exists(code_backup_dir):
                os.makedirs(code_backup_dir)

            backup_filename = f"{os.path.splitext(script_filename)[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            backup_file_path = os.path.join(code_backup_dir, backup_filename)

            with open(backup_file_path, 'w') as f:
                f.write(updated_code)
            logging.info(f"The updated code has been saved to '{backup_file_path}'.")

            # Save the new code to the current script file
            with open(script_filename, 'w') as f:
                f.write(updated_code)
            logging.info(f"The assistant's code has been updated and saved to '{script_filename}'.")
            info(f"Assistant has updated the bot's code and saved to '{script_filename}'.")

            # Update the version number
            # Read the current version from readme.md or default to '0.1.0'
            if os.path.exists('readme.md'):
                with open('readme.md', 'r') as f:
                    content = f.read()
                    match = re.search(r'Version (\d+\.\d+\.\d+)', content)
                    if match:
                        current_version = match.group(1)
                    else:
                        current_version = '0.1.0'
            else:
                current_version = '0.1.0'

            # Get the new version number
            new_version = get_new_version(current_version, requirements)

            # Update readme.md with the assistant's explanation and new version number
            readme_content = f"# Features and Recent Changes (Version {new_version})\n\n{requirements}\n"
            update_readme(readme_content)

            # Commit the changes to git
            git_commit(f"Updated assistant code to version {new_version} based on new requirements.")

            # Update the last update index
            last_update_index = len(conversation)

            # Ask user for permission to restart the script
            say("The assistant's code has been updated. Do you want to restart with the updated code? Type 'yes' to proceed or anything else to continue without restarting.")
            permission = input("User: ").strip().lower()

            if permission == "yes":
                logging.info("User approved restarting the script.")
                info("Assistant is restarting the script.")
                # Run the updated script in a new process and exit the current one
                subprocess.Popen([sys.executable, script_filename])
                logging.info("Started new instance of the script.")
                sys.exit()
            else:
                logging.info("User declined to restart the script.")
                info("Assistant will continue without restarting.")

        else:
            # If permission is not granted
            logging.info("User declined code update.")
            say("Assistant: Code update has been canceled.")
            info("Assistant is continuing the conversation without code update.")
            # Continue the conversation normally
            response = continue_conversation(conversation)
            say(response)
            conversation.append({"role": "assistant", "content": response})

    else:
        # Assistant continues the conversation normally
        response = continue_conversation(conversation)
        say(response)
        conversation.append({"role": "assistant", "content": response})

        # Check if the assistant wants to perform any commands in its response
        lower_response = response.lower()
        if "/read" in lower_response:
            # Assistant requests to read a file
            # Extract the file path from the assistant's response
            try:
                # Assume the file path is provided after the command "/read"
                file_path = response.strip().split("/read",1)[1].strip()
                # Read the content of the file
                content = read_file(file_path)
                if content is not None:
                    say(f"Here is the content of '{file_path}':\n{content}")
                else:
                    say(f"The file '{file_path}' does not exist.")
            except IndexError:
                # If no file path is provided
                say("Please specify the file path after '/read'.")

        elif "/ls" in lower_response:
            # Assistant requests to list files
            files = list_files()
            say("Here are the files in the current directory:")
            for file in files:
                say(file)

        elif "/write" in lower_response:
            # Assistant requests to write a file
            try:
                # Extract filename and code content from the assistant's response
                # Assume the format is "/write filename\n<code>"
                parts = response.strip().split("/write",1)[1].strip().split('\n',1)
                if len(parts) >= 2:
                    filename = parts[0].strip()
                    code_content = parts[1]
                    # Write the script
                    write_script(filename, code_content)
                    # Assistant can ask if they want to run the script
                    say(f"I have written the script '{filename}'. Do you want to execute it? Type 'yes' to proceed or anything else to cancel.")
                    permission = input("User: ").strip().lower()
                    if permission == "yes":
                        logging.info(f"User approved executing the script '{filename}'.")
                        run_script(filename)
                    else:
                        logging.info(f"User declined to execute the script '{filename}'.")
                        info(f"Assistant will not execute the script '{filename}'.")
                else:
                    say("Please specify the filename and code content after '/write'.")
            except Exception as e:
                logging.error(f"An error occurred while writing the script: {e}")
                say(f"An error occurred: {e}")

        elif "/execute" in lower_response:
            # Assistant requests to execute a script
            try:
                # Assume the script name is provided after the command "/execute"
                script_name = response.strip().split("/execute",1)[1].strip()
                # Run the script
                run_script(script_name)
            except IndexError:
                # If no script name is provided
                say("Please specify the script name after '/execute'.")
        elif "/self-upgrade" in lower_response:
            # Assistant requests to perform self-upgrade
            self_upgrade()
        else:
            # Check if the assistant wants to write tests and run them
            if "write tests" in lower_response or "test code" in lower_response:
                # Extract code blocks from the assistant's response
                code_blocks = re.findall(r'(?:python)?\n(.*?)')
                if code_blocks:
                    test_code = code_blocks[0]  # Assume the first code block is the test code
                    # Save the test code to a file
                    test_filename = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
                    with open(test_filename, 'w') as f:
                        f.write(test_code)
                    logging.info(f"Test code has been saved to '{test_filename}'.")
                    info(f"Assistant has saved test code to '{test_filename}'.")
                    # Run the test script and get test results
                    test_results = run_tests(test_filename)
                    # Report the test results
                    say(f"Here are the test results from '{test_filename}':\n{test_results}")
                    # Commit the test code to git
                    git_commit("Added new tests.")
                else:
                    say("No code block found in my response to run tests.")