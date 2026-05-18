from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from bson import ObjectId

app = FastAPI()

# ─── CONFIG (USE ENV VARIABLES PROPERLY) ─────────────────────

MONGO_URI = os.environ.get("mongodb+srv://safaayedis_db_user:safa12@cluster0.onrrl8r.mongodb.net/training_db?retryWrites=true&w=majority&appName=Cluster0")
GEMINI_KEY = os.environ.get("AIzaSyD-Q1jLE7J0_E401S54ZNWCLHujY36KRmU")
EMAIL_ADDRESS = os.environ.get("hejer.ayedi12@gmail.com")
EMAIL_PASSWORD = os.environ.get("ftsf zqsu jvtg plbq")

# ─────────────────────────────────────────────────────────────

client = MongoClient(MONGO_URI)
db = client["training_db"]
collection = db["candidates"]


class Candidate(BaseModel):
    timestamp: str
    name: str
    email: str
    phone: str
    university: str
    city: str
    platform: str
    type: str


@app.get("/")
def root():
    return {"status": "API is running ✅"}



@app.get("/candidates")
def get_candidates():
    docs = list(db.candidates.find())

    for d in docs:
        d["_id"] = str(d["_id"])   # convert ObjectId to string

    return docs
# ─── REGISTER ENDPOINT ───────────────────────────────────────
@app.post("/register")
def register(candidate: Candidate):
    doc = candidate.dict()

    # ✅ Always default status
    doc["status"] = "registered_unpaid"

    # save submit time
    doc["submittedAt"] = datetime.utcnow().isoformat()

    db.candidates.insert_one(doc)

    return {"success": True, "message": "Saved to MongoDB", "status": doc["status"]}
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
