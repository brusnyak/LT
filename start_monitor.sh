#!/bin/bash
# Combined startup: Backend + Signal Bot (with button callbacks)

echo "🚀 Starting SMC Trading Monitor"
echo ""

cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f backend/.env ]; then
    echo "❌ Error: backend/.env not found"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $BACKEND_PID $BOT_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend in background
echo "1️⃣ Starting backend on port 9000..."
cd backend
source venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --port 9000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "   Waiting for backend..."
for i in {1..30}; do
    if curl -s http://localhost:9000/api/stats/summary > /dev/null 2>&1; then
        echo "   ✅ Backend ready"
        break
    fi
    sleep 1
done

# Start signal bot (with active polling for button callbacks)
echo ""
echo "2️⃣ Starting Signal Bot..."
python signal_bot.py &
BOT_PID=$!

echo ""
echo "✅ All services running!"
echo "   Backend: http://localhost:9000"
echo "   Bot: Active (buttons will work)"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait
