import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    XAI_API_KEY: str = os.getenv("XAI_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_AGENT_ID: str = os.getenv("ELEVENLABS_AGENT_ID", "")
    
    PROJECT_NAME: str = "BisonHacks Backend"
    VERSION: str = "0.1.0"

    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
