import os
import time
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_DIR, "index.html")

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
    return FileResponse(
        INDEX_FILE,
        media_type="text/html"
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "PocketSmart AI"
    }


@app.post("/api/budget")
def budget(data: BudgetRequest):

    total = sum(e.amount for e in data.expenses)

    balance = data.income - total

    categories = {}

    for e in data.expenses:
        categories[e.category] = (
            categories.get(e.category, 0) + e.amount
        )

    recommendations = []

    if data.income <= 0:

        recommendations.append(
            "Enter a positive monthly income."
        )

    elif total > data.income:

        recommendations.append(
            "Expenses are higher than income. "
            "Review non-essential spending."
        )

    elif balance < data.income * 0.10:

        recommendations.append(
            "Your remaining balance is below 10% of income. "
            "Consider building a small buffer."
        )

    else:

        recommendations.append(
            "Your budget has a positive balance. "
            "Consider saving part of it."
        )

    if categories:

        highest = max(
            categories,
            key=categories.get
        )

        recommendations.append(
            f"Your highest spending category is {highest}. "
            "Review it for possible savings."
        )

    return {
        "income": round(data.income, 2),
        "total_expenses": round(total, 2),
        "balance": round(balance, 2),
        "categories": {
            k: round(v, 2)
            for k, v in categories.items()
        },
        "recommendations": recommendations
    }


@app.post("/api/ai-recommendation")
def ai_recommendation(data: BudgetRequest):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        return {
            "recommendation":
            "Gemini API key is not configured."
        }

    try:

        from google import genai

        client = genai.Client(
            api_key=api_key
        )

        prompt = f"""
You are PocketSmart AI, a personal budgeting assistant.

Monthly income: ₹{data.income}

Expenses:
{[e.model_dump() for e in data.expenses]}

Give exactly 3 short and practical budgeting suggestions.

Format EXACTLY like this:

1. First suggestion
2. Second suggestion
3. Third suggestion

Rules:

- Give exactly 3 suggestions.
- Put each suggestion on a separate line.
- Use only numbers 1, 2 and 3.
- Do not use bullet points.
- Do not use Markdown.
- Do not use ** symbols.
- Keep suggestions simple.
- Do not recommend financial products or investments.
"""


        # Models are tried in order.
        # If one model is temporarily unavailable,
        # the next model will be tried.

        models = [
            "gemini-3.5-flash-lite"
        ]


        last_error = None


        for model_name in models:

            for attempt in range(2):

                try:

                    print(
                        f"Trying Gemini model: "
                        f"{model_name}, attempt {attempt + 1}"
                    )

                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )

                    if response.text:

                        print(
                            f"Gemini success using "
                            f"{model_name}"
                        )

                        return {
                            "recommendation":
                            response.text.strip()
                        }

                except Exception as e:

                    last_error = e

                    print(
                        f"Gemini error with "
                        f"{model_name}: {e}"
                    )

                    # Wait before retrying
                    time.sleep(2)


        print(
            f"All Gemini models failed: {last_error}"
        )

        return {
            "recommendation":
            "Gemini AI is temporarily unavailable. "
            "Please try again in a few seconds."
        }


    except Exception as e:

        print(
            f"Gemini connection error: {e}"
        )

        return {
            "recommendation":
            "Gemini AI is temporarily unavailable. "
            "Please try again later."
        }
