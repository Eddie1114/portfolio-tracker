
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import openai
import requests
import os

app = FastAPI()

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/api/summary")
async def get_ai_summary():
    prompt = "Summarize recent changes in my crypto portfolio. BTC is up 5%, ETH is down 2%."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"summary": response.choices[0].message["content"]}

@app.get("/api/gemini/balances")
async def get_gemini_balances(api_key: str, api_secret: str):
    url = "https://api.gemini.com/v1/balances"
    headers = {
        "X-GEMINI-APIKEY": api_key,
        "X-GEMINI-PAYLOAD": "",  # Add encoded payload
        "X-GEMINI-SIGNATURE": ""  # Add HMAC signature
    }
    # Note: You must add Gemini request signing logic here
    return {"error": "This is a placeholder. Implement signature and payload logic."}
