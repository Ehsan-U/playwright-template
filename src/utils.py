import logging
from typing import Any

import src.settings as settings_module


############## logging setup ###############
logging.basicConfig(level=logging.WARNING,
    format='%(asctime)s [%(module)s] %(levelname)s: %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
    ])

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


############ settings ###############

class Settings:
    
    
    def __init__(self) -> None:
        self._load_settings()


    def set(self, key: str, value: Any) -> None:
        setattr(self, key, value)


    def get(self, key: str) -> Any:
        return getattr(self, key)


    def _load_settings(self):
        """ Load settings from settings.py module """
        for key in dir(settings_module):
            if key.upper():
                value = getattr(settings_module, key)
                self.set(key, value)