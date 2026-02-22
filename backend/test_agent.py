"""
Eleven Labs Conversational AI - Terminal Test Script

This script starts a persistent conversation session with your Eleven Labs agent.
It captures audio from your microphone and streams the agent's audio responses
through your speakers. Press Ctrl+C to end the session.

Requirements:
    pip install "elevenlabs[pyaudio]"
"""

import os
import signal
import sys
from dotenv import load_dotenv

load_dotenv()

from elevenlabs import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")
API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not AGENT_ID or not API_KEY:
    print("Error: ELEVENLABS_AGENT_ID and ELEVENLABS_API_KEY must be set in .env")
    sys.exit(1)

client = ElevenLabs(api_key=API_KEY)

conversation = Conversation(
    client=client,
    agent_id=AGENT_ID,
    requires_auth=False,
    audio_interface=DefaultAudioInterface(),
    callback_agent_response=lambda response: print(f"\n🤖 Agent: {response}"),
    callback_agent_response_correction=lambda original, corrected: print(f"\n🤖 Agent (corrected): {corrected}"),
    callback_user_transcript=lambda transcript: print(f"\n🎙️  You: {transcript}"),
    callback_latency_measurement=lambda latency: print(f"\n⏱️  Latency: {latency}ms"),
)

print("=" * 60)
print("  Eleven Labs Conversational AI - Terminal Test")
print("=" * 60)
print(f"  Agent ID: {AGENT_ID}")
print(f"  Status:   🟢 Starting conversation...")
print("=" * 60)
print("  Speak into your microphone. Press Ctrl+C to stop.")
print("=" * 60)

# Start the conversation (runs in a background thread)
conversation.start_session()

# Handle graceful shutdown
def shutdown(sig, frame):
    print("\n\n🔴 Ending conversation...")
    conversation_id = conversation.end_session()
    print(f"✅ Session ended. Conversation ID: {conversation_id}")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)

# Keep the main thread alive
print("\n🟢 Conversation active! Start speaking...\n")
conversation.wait_for_session_end()
print("\n✅ Session ended naturally.")
