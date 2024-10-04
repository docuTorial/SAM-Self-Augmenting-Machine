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
        if DEBUG_MODE:
            # Great work Sam!
            print("# Sam has committed and pushed changes to git.")
    except Exception as e:
        logging.error(f"Git commit failed: {e}")
        print(f"Git commit failed: {e}")

# Function to update or create readme.md with the provided content
def update_readme(content):
    """
    Updates the readme.md file with the assistant's explanations and recent changes.
    """
    with open('readme.md', 'w') as f:
        f.write(content)
    logging.info("readme.md has been updated.")
    if DEBUG_MODE:
        # Wonderful!
        print("# Sam has updated readme.md.")

# Function to read the contents of a file
def read_file(file_path):
    """
    Reads and returns the content of a file given its path.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        logging.info(f"Read content from '{file_path}'.")
        if DEBUG_MODE:
            print(f"# Sam is reading the file {file_path}")
        return content
    else:
        logging.warning(f"File '{file_path}' does not exist.")
        if DEBUG_MODE:
            print(f"# Sam attempted to read non-existent file '{file_path}'")
        return None  # Return None instead of the error message

# Function to list files in the current directory
def list_files():
    """
    Lists files in the current directory.
    """
    files = os.listdir('.')
    logging.info("Listed files in the current directory.")
    if DEBUG_MODE:
        print("# Sam is listing files in the current directory.")
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
        if DEBUG_MODE:
            print(f"# Sam has executed tests in '{test_file}' and saved results to '{output_file}'.")
        # Read the test output
        with open(output_file, 'r') as f:
            test_results = f.read()
        return test_results
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while running tests in '{test_file}'. Check '{output_file}' for details.")
        if DEBUG_MODE:
            print(f"# Sam encountered an error while running tests in '{test_file}'. See '{output_file}' for details.")
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
    if DEBUG_MODE:
        print("# Sam is checking if code update is needed.")
    # Call the helper assistant
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=helper_prompt
    )
    helper_response = response.choices[0].message.content.strip()
    logging.info(f"Helper response: {helper_response}")
    # Check if '1' is in the helper's response
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
    if DEBUG_MODE:
        print("# Sam is extracting new requirements.")
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
    version_prompt = f"""The current version is {current_version}. Based on the recent changes described below, determine the next version number following semantic versioning.

Recent changes:

{requirements}

"""
    logging.info("Determining new version number.")
    if DEBUG_MODE:
        print("# Sam is determining new version number.")
    # Call the version assistant
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[
            {"role": "system", "content": "Determine the next version number following semantic versioning."},
            {"role": "user", "content": version_prompt}
        ]
    )
    new_version = response.choices[0].message.content.strip()
    logging.info(f"New version determined: {new_version}")
    return new_version

# Function to write a new script
def write_script(script_name, script_code):
    """
    Writes a new script with the given name and code.
    """
    with open(script_name, 'w') as f:
        f.write(script_code)
    logging.info(f"New script '{script_name}' has been written.")
    if DEBUG_MODE:
        print(f"# Sam has written a new script '{script_name}'.")

# Function to run a script
def run_script(script_name):
    """
    Runs the script with the given name.
    """
    try:
        subprocess.run(["python", script_name], check=True)
        logging.info(f"Script '{script_name}' has been executed.")
        if DEBUG_MODE:
            print(f"# Sam has executed the script '{script_name}'.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while running script '{script_name}'.")
        if DEBUG_MODE:
            print(f"# Sam encountered an error while running script '{script_name}'.")

# Initialize the conversation history
conversation = [
    {"role": "system", "content": "You are a helpful assistant. You can read files, list files, write and run scripts, and propose code updates as needed without requiring permission. Use commands like '/read filename', '/write filename', '/execute filename', and '/ls' to perform these actions."}
]

last_update_index = 0  # Index in conversation where the last code update happened

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
        print("Assistant: The following new requirements have been identified:")
        print(requirements)
        print("Do you approve these changes? Type 'yes' to approve or anything else to decline.")
        permission = input("User: ").strip().lower()

        if permission == "yes":
            logging.info("User approved code update.")
            if DEBUG_MODE:
                print("# Sam is updating the code based on approved requirements.")
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
            updated_code = re.sub(r'.*?\n(.*?)            logging.info("Received updated code from AI assistant.")

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
            logging.info(f"The bot's code has been updated and saved to '{script_filename}'.")
            if DEBUG_MODE:
                print(f"# Sam has updated the bot's code and saved to '{script_filename}'.")

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
            git_commit(f"Updated bot code to version {new_version} based on new requirements.")

            # Update the last update index
            last_update_index = len(conversation)

            # Ask user for permission to restart the script
            print("Assistant: The bot's code has been updated. Do you want to restart with the updated code? Type 'yes' to proceed or anything else to continue without restarting.")
            permission = input("User: ").strip().lower()

            if permission == "yes":
                logging.info("User approved restarting the script.")
                if DEBUG_MODE:
                    print("# Sam is restarting the script.")
                # Run the updated script in a new process and exit the current one
                subprocess.Popen([sys.executable, script_filename])
                logging.info("Started new instance of the script.")
                sys.exit()
            else:
                logging.info("User declined to restart the script.")
                if DEBUG_MODE:
                    print("# Sam will continue without restarting.")

        else:
            # If permission is not granted
            logging.info("User declined code update.")
            print("Assistant: Bot code update has been canceled.")
            if DEBUG_MODE:
                print("# Sam is continuing the conversation without code update.")
            # Continue the conversation normally
            response = continue_conversation(conversation)
            print(f"Assistant: {response}")
            conversation.append({"role": "assistant", "content": response})

    else:
        # Assistant continues the conversation normally
        response = continue_conversation(conversation)
        print(f"Assistant: {response}")
        conversation.append({"role": "assistant", "content": response})

        # Check if the assistant wants to perform any commands in its response
        if "/read" in response.lower():
            # Assistant requests to read a file
            # Extract the file path from the assistant's response
            try:
                # Assume the file path is provided after the command "/read"
                file_path = response.strip().split("/read",1)[1].strip()
                # Read the content of the file
                content = read_file(file_path)
                if content is not None:
                    print(f"Assistant: Here is the content of '{file_path}':\n{content}")
                else:
                    print(f"Assistant: The file '{file_path}' does not exist.")
            except IndexError:
                # If no file path is provided
                print("Assistant: Please specify the file path after '/read'.")

        elif "/ls" in response.lower():
            # Assistant requests to list files
            files = list_files()
            print("Assistant: Here are the files in the current directory:")
            for file in files:
                print(file)

        elif "/write" in response.lower():
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
                    print(f"Assistant: I have written the script '{filename}'. Do you want to execute it? Type 'yes' to proceed or anything else to cancel.")
                    permission = input("User: ").strip().lower()
                    if permission == "yes":
                        logging.info(f"User approved executing the script '{filename}'.")
                        run_script(filename)
                    else:
                        logging.info(f"User declined to execute the script '{filename}'.")
                        if DEBUG_MODE:
                            print(f"# Sam will not execute the script '{filename}'.")
                else:
                    print("Assistant: Please specify the filename and code content after '/write'.")
            except Exception as e:
                logging.error(f"An error occurred while writing the script: {e}")
                print(f"Assistant: An error occurred: {e}")

        elif "/execute" in response.lower():
            # Assistant requests to execute a script
            try:
                # Assume the script name is provided after the command "/execute"
                script_name = response.strip().split("/execute",1)[1].strip()
                # Run the script
                run_script(script_name)
            except IndexError:
                # If no script name is provided
                print("Assistant: Please specify the script name after '/execute'.")
        else:
            # Check if the assistant wants to write tests and run them
            if "write tests" in response.lower() or "test code" in response.lower():
                # Extract code blocks from the assistant's response
                code_blocks = re.findall(r'(?:python)?\n(.*?)                if code_blocks:
                    test_code = code_blocks[0]  # Assume the first code block is the test code
                    # Save the test code to a file
                    test_filename = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
                    with open(test_filename, 'w') as f:
                        f.write(test_code)
                    logging.info(f"Test code has been saved to '{test_filename}'.")
                    if DEBUG_MODE:
                        print(f"# Sam has saved test code to '{test_filename}'.")
                    # Run the test script and get test results
                    test_results = run_tests(test_filename)
                    # Report the test results
                    print(f"Assistant: Here are the test results from '{test_filename}':\n{test_results}")
                    # Commit the test code to git
                    git_commit("Added new tests.")
                else:
                    print("Assistant: No code block found in my response to run tests.")

