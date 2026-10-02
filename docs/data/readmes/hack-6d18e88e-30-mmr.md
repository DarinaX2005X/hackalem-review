# AI Sana — TaskRank & TeamMatch

HackAlem AI Hackathon.

## Architecture

Frontend:
- React
- TypeScript
- Vite
- Zustand
- Zod

Backend:
- FastAPI
- Pydantic

AI:
- OpenAI / NVIDIA
- Local fallback

## Development

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

URLs:
- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend: [http://localhost:8000](http://localhost:8000)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)
