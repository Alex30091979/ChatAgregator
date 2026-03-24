import uvicorn
from fastapi import Depends, FastAPI

from app.config import Settings
from app.dependencies import get_settings

app = FastAPI(title="chat-aggregator-backend")


@app.get("/health")
def health(_: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)

