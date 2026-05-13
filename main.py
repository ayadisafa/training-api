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

# ─── CONFIG ───────────────────────────────────────────────
MONGO_URI      = os.environ.get("MONGO_URI")        # set in Render env vars
GEMINI_KEY     = os.environ.get("GEMINI_API_KEY")   # set in Render env vars
EMAIL_ADDRESS  = os.environ.get("EMAIL_ADDRESS")    # your Gmail
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")   # Gmail app password
# ──────────────────────────────────────────────────────────

client = MongoClient(MONGO_URI)
db     = client["training_db"]


class Candidate(BaseModel):
    name: str
    email: str
    phone: str
    training: str


@app.get("/")
def root():
    return {"status": "API is running ✅"}


@app.post("/register")
def register(candidate: Candidate):
    try:
        # 1. Save to MongoDB
        doc = candidate.dict()
        doc["status"]      = "pending_payment"
        doc["submittedAt"] = datetime.utcnow().isoformat()
        db.candidates.insert_one(doc)

        # 2. Generate email with Gemini (free)
        message = generate_message(candidate)

        # 3. Send email
        send_email(candidate.email, candidate.name, message)

        return {"success": True, "message": "Candidate registered and email sent!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_message(candidate: Candidate) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"

    prompt = f"""Write a warm, professional registration confirmation email for:
Name: {candidate.name}
Program: {candidate.training}
Phone: {candidate.phone}

Include:
- Welcome message
- Confirm their registration
- Next step: complete payment to secure their spot
- They will receive training details after payment

Keep it friendly, concise, plain text only."""

    response = requests.post(url, json={
        "contents": [{"parts": [{"text": prompt}]}]
    })

    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def send_email(to_email: str, name: str, body: str):
    msg = MIMEMultipart()
    msg["From"]    = EMAIL_ADDRESS
    msg["To"]      = to_email
    msg["Subject"] = f"Registration Confirmed – Welcome {name}!"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
