import subprocess
import os
from makelog import setup_logger
# Configure logging
logging = setup_logger(__name__)

def improved_run_file(filename):
    """
    Runs a Python file and captures its output and errors.

    Args:
        filename (str): The name of the file to run.

    Returns:
        str: The output and errors from running the file.
    """
    logging.info(f"Attempting to run the file: {filename}")
    
    # Ensure the file exists
    if not os.path.isfile(filename):
        error_message = f"File not found: {filename}"
        logging.error(error_message)
        return error_message

    try:
        # Run the file and capture output and errors
        result = subprocess.run(['python', filename], capture_output=True, text=True, check=True)
        logging.info(f"File {filename} ran successfully.")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running file {filename}: {e.stderr}")
        return e.stderr

# Example usage
if __name__ == "__main__":
    output = improved_run_file('example_script.py')
    print(output)