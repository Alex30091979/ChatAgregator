from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatCreate(BaseModel):
    client_id: int
    provider: str
    external_chat_id: str | None = None
    title: str | None = None
    operator_id: int | None = None
    status: str = "new"


class ChatUpdate(BaseModel):
    provider: str | None = None
    external_chat_id: str | None = None
    title: str | None = None
    operator_id: int | None = None
    status: str | None = None


class ChatAssignOperator(BaseModel):
    operator_id: int


class ChatStatusUpdate(BaseModel):
    status: str


class ChatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    operator_id: int | None
    provider: str
    status: str
    external_chat_id: str | None
    title: str | None
    created_at: datetime

