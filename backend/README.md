# benefind.ai

`benefind.ai` is an accessibility-first SNAP support chatbot and web app.

## Features

- **SNAP eligibility estimate** using:
  - ZIP code + state (location validation)
  - Monthly household income
  - Family size
- **Location-aware resource lookup**:
  - Nearby food pantries (OpenStreetMap/Overpass when available)
  - Local food-drive events (Eventbrite when configured, referral fallback otherwise)
- **Voice-call integration path** with ElevenLabs:
  - `POST /api/voice/eligibility` returns a voice script
  - Optional MP3 output (`audio_base64`) when `ELEVENLABS_API_KEY` is set
- **Accessible web interface**:
  - Semantic headings and landmarks
  - Keyboard-friendly controls
  - ARIA live regions for dynamic updates
  - Screen-reader compatible labels and status regions

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open: `http://localhost:8000`

## Environment variables

Optional:

- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID` (defaults to a public demo voice ID)
- `EVENTBRITE_API_TOKEN` (for live food-drive event search)

## API endpoints

- `GET /health`
- `POST /api/eligibility`
- `POST /api/resources`
- `POST /api/chat`
- `POST /api/voice/eligibility`
- `GET /api/voice/integration`

## Notes

Eligibility is an estimate and final determination depends on full state review (deductions, resources, and other rules).
