.PHONY: install run-backend run-frontend run-all clean

# Install dependencies for both backend and frontend
install:
	@echo "Installing Backend Dependencies..."
	cd backend && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	@echo "Installing Frontend Dependencies..."
	cd frontend && npm install

# Run Backend (FastAPI)
run-backend:
	@echo "Starting Backend..."
	cd backend && . venv/bin/activate && uvicorn app.main:app --reload --port 9000

# Run Frontend (Vite)
run-frontend:
	@echo "Starting Frontend..."
	cd frontend && npm run dev

# Run Both (requires parallel execution support like make -j2)
# Usage: make -j2 run-all
run-all: run-backend run-frontend

# Clean up venv and node_modules
clean:
	rm -rf backend/venv
	rm -rf frontend/node_modules
