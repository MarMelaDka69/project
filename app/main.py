from fastapi import FastAPI, HTTPException

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="3D Repository")


class Message(BaseModel):
    text: str


@app.post("/message")
def send_message(message: Message):
    return {
        "message": message.text
    }

