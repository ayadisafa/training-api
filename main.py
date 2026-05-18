from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
import requests

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
    
# Register candidate and save to MongoDB
@app.post("/register")
def register(candidate: Candidate):
    try:
        doc = candidate.dict()

        # default status
        doc["status"] = "registered_unpaid"
        doc["submittedAt"] = datetime.utcnow().isoformat()

        result = collection.insert_one(doc)

        return {
            "success": True,
            "message": "Candidate saved successfully",
            "id": str(result.inserted_id),
            "status": doc["status"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
