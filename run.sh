#!/bin/bash
# Start Runway (backend + frontend)
echo "Starting Runway..."

cd "$(dirname "$0")"

# Ensure Ollama is running
if ! curl -sf http://localhost:11434 > /dev/null 2>&1; then
    if command -v ollama > /dev/null 2>&1; then
        echo "Starting Ollama..."
        ollama serve &
        OLLAMA_PID=$!
        sleep 2
    else
        echo "Warning: Ollama not found. AI parsing will fall back to heuristics."
    fi
fi

# Start backend (activate venv if present)
cd backend
if [ -d .venv ]; then source .venv/bin/activate; fi
uvicorn app.main:app --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID ${OLLAMA_PID:-} 2>/dev/null" EXIT
wait
