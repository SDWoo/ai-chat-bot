@echo off
echo ========================================
echo AI Chatbot - Frontend Server Start
echo ========================================
echo.

cd frontend

echo Checking Node.js environment...
node --version
npm --version
echo.

echo Starting Vite development server...
echo Server will be available at: http://localhost:5173
echo.

npm run dev
