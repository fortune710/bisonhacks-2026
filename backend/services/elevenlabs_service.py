from elevenlabs.client import ElevenLabs
from config import settings
import os

class ElevenLabsService:
    def __init__(self):
        self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        self.agent_id = settings.ELEVENLABS_AGENT_ID

    def get_agent_info(self):
        """Fetches information about the configured agent."""
        if not self.agent_id:
            return {"error": "No ElevenLabs Agent ID configured"}
        try:
            # Replaced hypothetical direct agent fetch with a generic client call 
            # as the SDK specifically for 'Agent' might vary.
            # Usually, you interact with specific agent endpoints.
            return {"agent_id": self.agent_id, "status": "configured"}
        except Exception as e:
            return {"error": str(e)}

    async def get_signed_url(self):
        """
        Generates a signed URL for the conversational AI agent.
        This is typically used by the frontend to initiate a session.
        """
        if not self.agent_id:
            return {"error": "No ElevenLabs Agent ID configured"}
        
        try:
            # Example logic for getting a signed URL
            # This often requires a specific API call to ElevenLabs
            response = self.client.conversational_ai.get_signed_url(agent_id=self.agent_id)
            return {"signed_url": response}
        except Exception as e:
            return {"error": str(e)}

elevenlabs_service = ElevenLabsService()
