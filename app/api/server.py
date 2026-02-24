from fastapi import FastAPI

from app.api.routes import router
from app.api.senate_dossier import router as senate_router

app = FastAPI(title="Valet Studio", version="0.1.0")
app.include_router(router)
app.include_router(senate_router)


@app.get("/health")
def health():
    return {"ok": True}
