# PocketSmart AI – Smart Budget & Recommendation Assistant

A student-friendly AI budgeting web app built with FastAPI and a simple HTML/CSS/JavaScript frontend.

## Features
- Add income and expenses
- Calculate remaining balance
- Categorize expenses
- Show spending summary
- Generate simple budget recommendations
- Optional Google Gemini API integration
- FastAPI backend
- Responsive web UI

## Run locally
1. Install Python 3.10+.
2. Run: `pip install -r requirements.txt`
3. Optional: set `GEMINI_API_KEY` as an environment variable.
4. Run: `uvicorn backend.main:app --reload`
5. Open: `http://127.0.0.1:8000`

Never upload a real API key to GitHub.
