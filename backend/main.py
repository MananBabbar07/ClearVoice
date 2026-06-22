import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(dotenv_path="E:/ClearVoice/.env", override=True)

app = FastAPI(title="ClearVoice API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ClearVoice API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}