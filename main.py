import os
import time
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel


# --------------------------------------------------
# BASIC APP SETUP
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_DIR, "index.html")

app = FastAPI(title="PocketSmart AI")


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# DATA MODELS
# --------------------------------------------------

class Expense(BaseModel):
    name: str
    amount: float
    category: str


class BudgetRequest(BaseModel):
    income: float
    expenses: List[Expense]


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():
    return FileResponse(
        INDEX_FILE,
        media_type="text/html"
    )


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "PocketSmart AI"
    }


# --------------------------------------------------
# BUDGET CALCULATION
# --------------------------------------------------

@app.post("/api/budget")
def budget(data: BudgetRequest):

    total = sum(
        e.amount
        for e in data.expenses
    )

    balance = data.income - total

    categories = {}

    for e in data.expenses:
        categories[e.category] = (
            categories.get(e.category, 0)
            + e.amount
        )

    recommendations = []

    # Check income
    if data.income <= 0:

        recommendations.append(
            "Enter a positive monthly income."
        )

    # Check overspending
    elif total > data.income:

        recommendations.append(
            "Expenses are higher than income. "
            "Review non-essential spending."
        )

    # Check low balance
    elif balance < data.income * 0.10:

        recommendations.append(
            "Your remaining balance is below 10% of income. "
            "Consider building a small buffer."
        )

    # Positive balance
    else:

        recommendations.append(
            "Your budget has a positive balance. "
            "Consider saving part of it."
        )

    # Find highest spending category
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


# --------------------------------------------------
# GEMINI AI RECOMMENDATION
# --------------------------------------------------

@app.post("/api/ai-recommendation")
def ai_recommendation(data: BudgetRequest):

    api_key = os.getenv("GEMINI_API_KEY")

    # Check API key
    if not api_key:

        return {
            "recommendation":
            "Gemini API key is not configured."
        }

    try:

        from google import genai

        # Create Gemini client
        client = genai.Client(
            api_key=api_key
        )

        # --------------------------------------------------
        # PROMPT
        # --------------------------------------------------

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

        # --------------------------------------------------
        # GEMINI MODELS
        # --------------------------------------------------
        # Try lightweight model first.
        # If it fails, try the next model.
        #
        # IMPORTANT:
        # We do NOT retry a quota error repeatedly.
        # This prevents unnecessary API requests.
        # --------------------------------------------------

        models = [
            "gemini-3.5-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.8-flash"
        ]

        last_error = None

        # --------------------------------------------------
        # TRY EACH MODEL ONCE
        # --------------------------------------------------

        for model_name in models:

            try:

                print(
                    f"Trying Gemini model: {model_name}"
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

                print(
                    f"Gemini returned no text using "
                    f"{model_name}"
                )

            except Exception as e:

                last_error = e

                error_text = str(e)

                print(
                    f"Gemini error with "
                    f"{model_name}: {e}"
                )

                # --------------------------------------------------
                # 429 = QUOTA / RATE LIMIT
                # --------------------------------------------------

                if (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED"
                    in error_text
                    or "quota"
                    in error_text.lower()
                ):

                    print(
                        f"Quota limit reached for "
                        f"{model_name}. "
                        f"Trying next model."
                    )

                    continue

                # --------------------------------------------------
                # 503 = TEMPORARY SERVER OVERLOAD
                # --------------------------------------------------

                if (
                    "503" in error_text
                    or "UNAVAILABLE"
                    in error_text
                ):

                    print(
                        f"Gemini temporarily unavailable "
                        f"for {model_name}."
                    )

                    # Wait before trying next model
                    time.sleep(3)

                    continue

                # --------------------------------------------------
                # OTHER ERROR
                # --------------------------------------------------

                print(
                    f"Unexpected Gemini error. "
                    f"Trying next model."
                )

                continue

        # --------------------------------------------------
        # ALL MODELS FAILED
        # --------------------------------------------------

        print(
            f"All Gemini models failed: "
            f"{last_error}"
        )

        # Return a safe fallback instead of crashing
        return {
            "recommendation":
            "1. Review your highest spending category.\n"
            "2. Reduce unnecessary expenses where possible.\n"
            "3. Keep some money aside from your remaining balance."
        }

    # --------------------------------------------------
    # GENERAL CONNECTION ERROR
    # --------------------------------------------------

    except Exception as e:

        print(
            f"Gemini connection error: {e}"
        )

        return {
            "recommendation":
            "1. Review your highest spending category.\n"
            "2. Reduce unnecessary expenses where possible.\n"
            "3. Keep some money aside from your remaining balance."
        }                         
