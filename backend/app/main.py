from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import FRONTEND_ORIGIN
from .i18n import language, LANGUAGES, translate
from .database import init_db
from .services.seed_service import seed_if_empty
from .routers import challenges, proposals, auth
from .services.rating_service import migrate_ratings

app = FastAPI(
    title="AI SANA Challenge Hub API",
    version="0.1.0",
    description="Hackathon MVP: business challenge quality rating and open team choice.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, FRONTEND_ORIGIN.replace('://localhost', '://127.0.0.1')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()
    seed_if_empty()
    auth.migrate_legacy_owners()
    migrate_ratings()


@app.middleware('http')
async def protect_mutations(request: Request, call_next):
    selected=request.headers.get('accept-language','ru').split(',')[0].split('-')[0].lower()
    token=language.set(selected if selected in LANGUAGES else 'ru')
    try:
        return await authorized_request(request,call_next)
    finally:
        language.reset(token)

async def authorized_request(request,call_next):
    if request.method in {'POST','PUT','PATCH','DELETE'}:
        if request.headers.get('X-Requested-With') != 'Alem':
            return JSONResponse({'detail':'Запрос должен быть отправлен из приложения'},status_code=403)
        origin=request.headers.get('origin')
        if origin and origin not in {FRONTEND_ORIGIN,FRONTEND_ORIGIN.replace('://localhost','://127.0.0.1')}:
            return JSONResponse({'detail':'Источник запроса не разрешён'},status_code=403)
    return await call_next(request)


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(challenges.router)
app.include_router(proposals.router)
app.include_router(auth.router)
