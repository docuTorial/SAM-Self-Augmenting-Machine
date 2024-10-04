# Import necessary modules
from openai import OpenAI  # For interacting with the OpenAI API
from os import getenv  # For accessing environment variables
import os  # For file operations
import sys  # For system-specific parameters and functions
import subprocess  # For running shell commands
import re  # For regular expressions to parse code blocks
from git import Repo  # For git operations using GitPython
from datetime import datetime  # For handling date and time

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
        print("Changes have been committed and pushed to git.")
    except Exception as e:
        print(f"Git commit failed: {e}")
    # User can add comments here

# Function to update or create readme.md with the provided content
def update_readme(content):
    """
    Updates the readme.md file with the assistant's explanations and recent changes.
    """
    with open('readme.md', 'w') as f:
        f.write(content)
    print("readme.md has been updated.")
    # User can add comments here

# Function to read the contents of a file
def read_file(file_path):
    """
    Reads and returns the content of a file given its path.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read()
    else:
        return f"File '{file_path}' does not exist."
    # User can add comments here

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
        print(f"Tests have been executed successfully. Results saved to '{output_file}'")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running tests. Check '{output_file}' for details.")
    # User can add comments here

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
    return assistant_response
    # User can add comments here

# Function to check if the user wants to update the code
def check_for_code_update(conversation):
    """
    Uses an AI assistant to check if the user wants to update the code.
    Returns True if code update is requested, False otherwise.
    """
    # Prepare the messages for the helper assistant
    helper_prompt = [
        {"role": "system", "content": "Return '1' if the user is asking to update the code with new features, otherwise return '0'."},
    ] + conversation[-5:]  # Include last 5 messages
    #  TODO: Extract that number `-5` to a named const value.
    # Call the helper assistant
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=helper_prompt
    )
    helper_response = response.choices[0].message.content.strip()
    # Check if '1' is in the helper's response
    if '1' in helper_response:
        return True
    else:
        return False
    # User can add comments here

# Function to get the new requirements from the conversation
def get_requirements(conversation):
    """
    Uses an AI assistant to extract a list of requirements added since the last update.
    Returns the requirements as a string.
    """
    # Prepare the messages for the requirements assistant
    requirements_prompt = [
        {"role": "system", "content": "List the new requirements added since the last code update."},
    ] + conversation[-10:]  # Include last 10 messages
    #  TODO: Extract `-10` into a named const value.
    #  TODO: Make sure to only include messages that come after the previous update to exclude requirements that are already implmented.
    # Call the requirements assistant
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=requirements_prompt
    )
    requirements_response = response.choices[0].message.content.strip()
    return requirements_response
    # User can add comments here

# Function to get the new version number using semantic versioning
def get_new_version():
    """
    Uses an AI helper to determine the new version number based on the changes.
    Returns the new version number as a string.
    """
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

    # Prepare the prompt for the version assistant
    version_prompt = f"The current version is {current_version}. Based on the recent changes, determine the next version number following semantic versioning."

    # Call the version assistant
    #  TODO: Include details about the changes to help understand their scope.
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[
            {"role": "system", "content": "Determine the next version number following semantic versioning."},
            {"role": "user", "content": version_prompt}
        ]
    )
    new_version = response.choices[0].message.content.strip()
    return new_version
    # User can add comments here

# Initialize the conversation history
conversation = [
    {"role": "system", "content": "You are a helpful assistant."}  # System prompt to the assistant
]

# Main chat loop between the user and the assistant
while True:
    # Get input from the user
    user_input = input("User: ")

    # Append the user's message to the conversation
    conversation.append({"role": "user", "content": user_input})

    # Check if the user wants to update the bot's code
    code_update_needed = check_for_code_update(conversation)

    if code_update_needed:
        # Get the requirements
        requirements = get_requirements(conversation)

        # Assistant presents the requirements to the user for approval
        print("Assistant: The following new requirements have been identified:")
        print(requirements)
        print("Do you approve these changes? Type 'yes' to approve or anything else to decline.")
        permission = input("User: ").strip().lower()
        if permission == "yes":
            # Read the existing code
            script_filename = sys.argv[0]  # Name of the current script
            with open(script_filename, 'r') as f:
                current_code = f.read()

            # Prepare the prompt for the o1-preview model
            code_update_prompt = f"""Update the following code according to the requirements below:

Requirements:
{requirements}

Code:
{current_code}

Please provide the updated code and only the code."""

            # Send the prompt to the o1-preview model
            code_response = client.chat.completions.create(
                model="openai/o1-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that updates code based on requirements."},
                    {"role": "user", "content": code_update_prompt}
                ]
            )
            #  TODO: Remove python``` ``` markup from response if it exists.
            updated_code = code_response.choices[0].message.content.strip()

            # Save the new code to the current script file
            with open(script_filename, 'w') as f:
                f.write(updated_code)
            print(f"The bot's code has been updated and saved to '{script_filename}'.")

            # Update the version number using a helper
            new_version = get_new_version()
            
            #  TODO: First update the readme and then commit the changes.
            # Commit the changes to git
            git_commit(f"Updated bot code to version {new_version} based on new requirements.")

            # Update readme.md with the assistant's explanation and new version number
            readme_content = f"# Features and Recent Changes (Version {new_version})\n\n{requirements}\n"
            update_readme(readme_content)

            # Exit the script to allow the user to restart with updated code
            print("Please restart the script to continue with the updated code.")
            sys.exit()
        else:
            # If permission is not granted
            print("Assistant: Bot code update has been canceled.")
            # Continue the conversation normally
            response = continue_conversation(conversation)
            print(f"Assistant: {response}")
            conversation.append({"role": "assistant", "content": response})
            #  FIX: In the following `elif` there seems to be a big misunderstanding here:
            """
            The assistant is allowed to ask to list all files /ls or /read a specific filename.
            The assistant does not need permission to do that. The script should simply notify:
            Sam is reading the file {{filename}} or Sam is listing files (use your own words)
            """
    elif "read" in user_input.lower() and "file" in user_input.lower():
        # Assistant requests to read a file
        # Extract the file path from the user's input
        try:
            # Assume the file path is provided after the phrase "read file"
            file_path = user_input.lower().split("read file", 1)[1].strip()
            # Read the content of the file
            content = read_file(file_path)
            print(f"Assistant: Here is the content of '{file_path}':\n{content}")
        except IndexError:
            # If no file path is provided
            print("Assistant: Please specify the file path after 'read file'.")
    else:
        # Assistant continues the conversation normally
        response = continue_conversation(conversation)
        print(f"Assistant: {response}")
        conversation.append({"role": "assistant", "content": response})

        # Check if the assistant wants to write tests and run them
        #  FIX: If the assistant wants to write, they can /write {{filename}} and it will ask the user for permission.
        """
        The user will need to answer `yes` to accept or anything else to reject.
        The assistant can ask to do this whenever they want to help the user.
        Make sure the assistant's system prompt reflects its abilities (such as read write ls)
        """
        if "write tests" in response.lower() or "test code" in response.lower():
            # Extract code blocks from the assistant's response
            code_blocks = re.findall(r'```(?:python)?\n(.*?)```', response, re.DOTALL)
            if code_blocks:
                test_code = code_blocks[0]  # Assume the first code block is the test code
                # Save the test code to a file
                test_filename = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
                with open(test_filename, 'w') as f:
                    f.write(test_code)
                print(f"Test code has been saved to '{test_filename}'.")
                # Run the test script
                run_tests(test_filename)
                # Commit the test code to git
                git_commit("Added new tests.")
            else:
                print("Assistant: No code block found in your response to run tests.")
    # User can add comments here

# User can add overall comments about the code here
#  TODO: Remove all the places for user's comments. The user can figure out where to put comments. :D