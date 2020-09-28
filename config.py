import os
from dotenv import load_dotenv

class Config:
    load_dotenv()

    TOKEN = os.environ.get("TOKEN")
