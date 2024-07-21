from enum import Enum

class ElementSelector(Enum):
    """
    Represents an element within an HTML page structure.

    Each element has two attributes:

    * `name`: A string representing the user-defined name for HTML element.
    * `value`: A string representing the element's location within the HTML structure,
              often expressed as a CSS or XPATH selector.

    """


class LoginPage(Enum):
    pass




############################

import logging


# log_directory = "logs"
# if not os.path.exists(log_directory):
#     os.makedirs(log_directory)

logging.basicConfig(level=logging.WARNING,  
    format='=> %(levelname)s - %(module)s - %(asctime)s - %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # Logs to the console
        # logging.FileHandler('logs/logs.log')  # Logs to a file
    ])

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) 