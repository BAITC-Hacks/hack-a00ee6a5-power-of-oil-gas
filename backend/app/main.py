from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import FRONTEND_ORIGIN
from .database import init_db
from .services.seed_service import seed_if_empty
from .routers import challenges, proposals

app = FastAPI(
    title="AI SANA Challenge Hub API",
    version="0.1.0",
    description="Hackathon MVP: business challenge quality rating and open team choice.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()
    seed_if_empty()


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(challenges.router)
app.include_router(proposals.router)
