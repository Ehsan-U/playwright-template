from enum import Enum



class ElementSelector(Enum):
    """
    Represents an element within an HTML page structure.

    Each element has two attributes:

    * `name`: A string representing the user-defined name for the selector.
    * `value`: A string representing the element's location within the HTML structure,
              often expressed as a CSS or XPATH selector.

    """