# Loading environment variables from .env file
import os
from dotenv import load_dotenv
load_dotenv()

# Deepgram API key
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")