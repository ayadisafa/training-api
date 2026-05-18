from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = FastAPI()

# ─── CONFIG (USE ENV VARIABLES PROPERLY) ─────────────────────

MONGO_URI = os.environ.get("MONGO_URI")
GEMINI_KEY = os.environ.get("GEMINI_KEY")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# ─────────────────────────────────────────────────────────────

client = MongoClient(MONGO_URI)
db = client["training_db"]
collection = db["candidates"]


class Candidate(BaseModel):
    name: str
    email: str
    phone: str
    training: str


@app.get("/")
def root():
    return {"status": "API is running ✅"}


# ─── REGISTER ENDPOINT ───────────────────────────────────────
@app.post("/register")
def register(candidate: Candidate):
    try:
        doc = candidate.dict()

        # default status
        doc["status"] = "registered_unpaid"
        doc["submittedAt"] = datetime.utcnow().isoformat()

        # 1. SAVE TO MONGODB ✅
        result = collection.insert_one(doc)

        # 2. GENERATE EMAIL
        message = generate_message(candidate)

        # 3. SEND EMAIL
        send_email(candidate.email, candidate.name, message)

        return {
            "success": True,
            "message": "Saved to MongoDB successfully",
            "id": str(result.inserted_id)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── GEMINI EMAIL ───────────────────────────────────────────
def generate_message(candidate: Candidate) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

    prompt = f"""
Write a professional registration confirmation email.

Name: {candidate.name}
Program: {candidate.training}

Include:
- Welcome message
- Confirmation
- Payment instruction
- Training details after payment
"""

    response = requests.post(url, json={
        "contents": [{"parts": [{"text": prompt}]}]
    })

    data = response.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]


# ─── EMAIL SENDER ────────────────────────────────────────────
def send_email(to_email: str, name: str, body: str):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = f"Registration Confirmed – Welcome {name}"

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
