# BeneFind – SNAP Assistance AI

An AI-powered assistant that helps people understand **SNAP (food assistance)**, check eligibility, and find nearby food resources through chat, voice, or phone.

Many eligible households never receive benefits because the process is confusing or inaccessible. Our project simplifies the experience and makes reliable information easy to access.

---

# Features

## SNAP Guidance

Users can ask questions about:
- Eligibility
- Required documents
- Application steps
- State-specific information

Responses are generated using a **Retrieval-Augmented Generation (RAG)** pipeline so answers come from verified program resources rather than generic AI guesses (limited to DMV resources for now).

---

## Food Bank Locator

The platform helps users locate nearby:
- Food banks  
- Food pantries  
- Community assistance programs  

---

## Multi-Access AI Assistant

To improve accessibility, the assistant is available through:

- Web chat  
- Voice interaction  
- Phone call interface  

Voice responses are powered by ElevenLabs, while the phone-based assistant uses Vapi.

This ensures people without reliable internet access, those with disabilities, or individuals with low digital literacy can still get help.

---

# Tech Stack

## Frontend
- React  
- TypeScript  
- Vite  

## Backend
- Python  
- FastAPI  

## AI / RAG
- LangChain  
- Google Gemini embeddings  
- MongoDB Atlas Vector Search  

## Voice
- ElevenLabs  
- Vapi  

---

# How It Works

1. Government SNAP documents and resources are collected and stored in MongoDB.
2. The documents are split into chunks and converted into embeddings.
3. Embeddings are stored in a vector database.
4. When a user asks a question:
   - The system retrieves relevant chunks
   - The AI generates an answer grounded in those sources
   - Sources are returned alongside the response.

This approach reduces hallucinations and ensures answers come from real assistance program materials.

---

# Project Structure
backend/  
ai/  
db/  
services/  
routers/

benefind.ai/  
src/


Key components:

- **Scraper** – Extracts SNAP resource content  
- **Embedding pipeline** – Converts documents into vectors  
- **RAG system** – Retrieves relevant information for responses  
- **API** – Serves responses to the frontend and voice assistant  

---

# Running Locally

## 1. Clone the repository
```
git clone <repo-url>
cd project
```

---

## 2. Backend Setup
```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
Server runs at:

http://127.0.0.1:8000

---

## 3. Frontend Setup

```
cd frontend
npm install
npm run dev
```

App runs at:

http://localhost:5173

---

# Environment Variables

Create a `.env` file in the backend directory.

Example:

```
MONGODB_URI=
GOOGLE_API_KEY=
ELEVENLABS_API_KEY=
VAPI_API_KEY=
```


---

# Accessibility

The project is designed to support users who may face barriers to traditional online services by providing:

- Voice interaction  
- Phone access  
- Simplified explanations of complex government processes  

---

# Future Improvements

- Full eligibility pre-screening  
- More states and assistance programs  
- Multilingual support  
- Expanded food bank database  
- SMS access to the assistant  

---

# Hackathon Project

Built during **BisonHacks** to improve access to food assistance and make government resources easier to understand and navigate.

