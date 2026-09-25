import os
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="PocketSmart AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Expense(BaseModel):
    name: str
    amount: float
    category: str

class BudgetRequest(BaseModel):
    income: float
    expenses: List[Expense]

@app.get("/")
def home():
    return 
    FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/health")
def health():
    return {"status": "ok", "service": "PocketSmart AI"}

@app.post("/api/budget")
def budget(data: BudgetRequest):
    total = sum(e.amount for e in data.expenses)
    balance = data.income - total
    categories = {}
    for e in data.expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount

    recommendations = []
    if data.income <= 0:
        recommendations.append("Enter a positive monthly income.")
    elif total > data.income:
        recommendations.append("Expenses are higher than income. Review non-essential spending.")
    elif balance < data.income * 0.10:
        recommendations.append("Your remaining balance is below 10% of income. Consider building a small buffer.")
    else:
        recommendations.append("Your budget has a positive balance. Consider saving part of it.")

    if categories:
        highest = max(categories, key=categories.get)
        recommendations.append(f"Your highest spending category is {highest}. Review it for possible savings.")

    return {
        "income": round(data.income, 2),
        "total_expenses": round(total, 2),
        "balance": round(balance, 2),
        "categories": {k: round(v, 2) for k, v in categories.items()},
        "recommendations": recommendations
    }

@app.post("/api/ai-recommendation")
def ai_recommendation(data: BudgetRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"recommendation": "Gemini API key is not configured. Review your highest expense category and keep part of your balance for savings."}

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""You are PocketSmart AI, a personal budgeting assistant.
Monthly income: {data.income}
Expenses: {[e.model_dump() for e in data.expenses]}
Give 3 short, practical budgeting suggestions. Do not recommend financial products or investments."""
        response = model.generate_content(prompt)
        return {"recommendation": response.text}
    except Exception:
        return {"recommendation": "AI service is temporarily unavailable. Use the local budget summary and review your largest spending category."}
