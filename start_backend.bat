@echo off
echo ========================================
echo AI Chatbot - Backend Server Start
echo ========================================
echo.

cd backend

echo Checking Python environment...
python --version
echo.

echo Starting FastAPI server with hot reload...
echo Server will be available at: http://localhost:8000
echo API docs will be available at: http://localhost:8000/docs
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
