import uvicorn
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.dependencies import get_db

app = FastAPI(title="chat-aggregator-backend")


@app.get("/health")
def health(
    db: Session = Depends(get_db), _: Settings = Depends(get_settings)
) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)

