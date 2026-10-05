from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, Base
from app.models import Model


app = FastAPI(title="3D Repository")

Base.metadata.create_all(bind=engine)


BASE_DIR = Path(__file__).resolve().parent.parent

FILE_PATH = BASE_DIR / "data" / "messages.txt"
HTML_PATH = BASE_DIR / "app" / "static" / "static.html"



class Message(BaseModel):
    text: str


class ModelCreate(BaseModel):
    title: str
    description: str
    format: str



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

    db: Session = SessionLocal()

    try:
        models = db.query(Model).all()

        return models

    finally:
        db.close()


@app.post("/models")
def create_model(model_data: ModelCreate):

    db: Session = SessionLocal()

    try:
        model = Model(
            title=model_data.title,
            description=model_data.description,
            format=model_data.format
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        return model

    finally:
        db.close()

@app.post("/models/upload")
async def upload_model(
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...)
):
    upload_dir = BASE_DIR / "uploads"
    upload_dir.mkdir(exist_ok=True)

    file_path = upload_dir / file.filename

    with open(file_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    file_format = Path(file.filename).suffix.lower().replace(".", "")

    db: Session = SessionLocal()

    try:
        model = Model(
            title=title,
            description=description,
            format=file_format.upper(),
            file_path=f"uploads/{file.filename}"
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        return model

    finally:
        db.close()

@app.get("/models/{model_id}")
def get_model(model_id: int):

    db: Session = SessionLocal()

    try:
        model = db.query(Model).filter(
            Model.id == model_id
        ).first()

        if model is None:
            raise HTTPException(
                status_code=404,
                detail="Model not found"
            )

        return model

    finally:
        db.close()

@app.get("/models/{model_id}/download")
def download_model(model_id: int):

    db: Session = SessionLocal()

    try:
        model = db.query(Model).filter(
            Model.id == model_id
        ).first()

        if model is None:
            raise HTTPException(
                status_code=404,
                detail="Model not found"
            )

        file_path = BASE_DIR / model.file_path

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )

        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/octet-stream"
        )

    finally:
        db.close()