# from fastapi import FastAPI, HTTPException
#
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
#
# app = FastAPI(title="3D Repository")
#
#
# class Message(BaseModel):
#     text: str
#
#
# @app.post("/message")
# def send_message(message: Message):
#     return {
#         "message": message.text
#     }


from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path

app = FastAPI(title="3D Repository")


FILE_PATH = Path("data/messages.txt")


class Message(BaseModel):
    text: str


@app.post("/messages")
def add_message(message: Message):
    with open(FILE_PATH, "a", encoding="utf-8") as file:
        file.write(message.text + "\n")

    return {
        "status": "success",
        "message": message.text
    }


@app.get("/messages")
def get_messages():
    with open(FILE_PATH, "r", encoding="utf-8") as file:
        text = file.read()

    return {
        "text": text
    }

