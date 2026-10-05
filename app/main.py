from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel


app = FastAPI(title="3D Repository")

BASE_DIR = Path(__file__).resolve().parent.parent
FILE_PATH = BASE_DIR / "data" / "messages.txt"
HTML_PATH = BASE_DIR / "app" / "static" / "static.html"

class Message(BaseModel):
    text: str

class Model(BaseModel):
    id: int
    title: str
    description: str
    format: str

models = [
    Model(
        id=1,
        title="Agnes Tachyon",
        description="3-Д Модель Агнес Тахион",
        format="Blend"
    ),
    Model(
        id=2,
        title="ASton Machan",
        description="3-Д Модель Астон Мачан",
        format="Blend"
    ),
    Model(
        id=3,
        title="Nice Nature",
        description="3-Д Модель Nice Nature",
        format="Blend"
    )
]


# Главная страница

@app.get("/")
def home():
    return FileResponse(HTML_PATH)

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


@app.get("/models")
def get_models():
    return models


@app.get("/models/{model_id}")
def get_model(model_id: int):

    for model in models:
        if model.id == model_id:
            return model

    raise HTTPException(
        status_code=404,
        detail="Model not found"
    )

