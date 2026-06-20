import os
from dotenv import load_dotenv

# Load local .env file if present; safe because .env is ignored by git.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))


def _to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')

USE_TOMTOM = _to_bool(os.getenv('USE_TOMTOM', 'false'))
USE_MOCKS = _to_bool(os.getenv('USE_MOCKS', 'false'))
TOMTOM_API_KEY = os.getenv('TOMTOM_API_KEY', '')
TOMTOM_BASE_URL = os.getenv('TOMTOM_BASE_URL', 'https://api.tomtom.com')

# If mocks are enabled, all external integrations should default to simulated behavior.
TOMTOM_ACTIVE = USE_TOMTOM and bool(TOMTOM_API_KEY) and not USE_MOCKS

# LLM Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
LLM_MODEL = os.getenv('LLM_MODEL', 'llama-3.3-70b-versatile')
LLM_ACTIVE = bool(GROQ_API_KEY)
