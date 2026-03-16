#!/bin/bash
# Start Runway (backend + frontend)
echo "Starting Runway..."

cd "$(dirname "$0")"

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

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
