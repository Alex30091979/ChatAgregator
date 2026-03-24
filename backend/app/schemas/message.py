from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    chat_id: int
    user_id: int
    body: str


class MessageUpdate(BaseModel):
    body: str
    actor_user_id: int | None = None


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id: int
    user_id: int
    body: str
    created_at: datetime

