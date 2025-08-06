from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

@app.get("/books")
def get_book_by_isbn(isbn: str):
    if not GOOGLE_API_KEY:
        return {"error": "Missing Google Books API key"}

    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    return response.json()
