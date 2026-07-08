from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routers import customers, advisor

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Wealth Advisor API")

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "https://idbi-frontend.vercel.app",
    "https://idbi-frontend-dqqi1d75t-utkarsh542s-projects.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(advisor.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "Welcome to IDBI AI Wealth Advisor API"}
