from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="Valet Studio", version="0.1.0")
app.include_router(router)


@app.get("/health")
def health():
    return {"ok": True}
