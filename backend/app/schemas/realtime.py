from pydantic import BaseModel


class TypingEventRequest(BaseModel):
    is_typing: bool = True

