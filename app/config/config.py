import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

config = Config()