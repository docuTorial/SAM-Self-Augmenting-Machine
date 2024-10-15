
import logging

def setup_logger(module_name):
    # Create a custom logger for the __main__ module
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)  # Set the logging level

    # Create handlers
    file_handler = logging.FileHandler(f'logs/{module_name}.log')
    file_handler.setLevel(logging.DEBUG)

    # Create formatters and add them to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)

    return logger

if __name__ == "__main__":
    # Setup logger
    logger = setup_logger()

    # Log some messages
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
