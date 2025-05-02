import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.settings import settings
from app.middleware.auth import verify_jwt_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configuration des loggers
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.info("Application starting up...")
    yield
    logging.info("Application shutting down...")


app = FastAPI(
    title="AI Product Copilot API",
    description="API pour l'analyse de feedback utilisateur via LangGraph et Supabase",
    version="0.1.0",
    lifespan=lifespan,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware d'authentification JWT
app.middleware("http")(verify_jwt_middleware)

# Inclusion des routes API
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
