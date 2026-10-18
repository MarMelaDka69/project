import os

from pathlib import Path

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)

from fastapi import Request
from fastapi.responses import JSONResponse

from app.csrf import create_csrf_token, verify_csrf

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import create_session, get_current_user
from app.database import Base, engine, SessionLocal
from app.models import Model, User
from app.schemas import ModelResponse
from app.security import hash_password, verify_password

app = FastAPI(title="3D Repository")

@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        try:
            verify_csrf(request)
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )

    return await call_next(request)

# удалено для теста
#Base.metadata.create_all(bind=engine)



BASE_DIR = Path(__file__).resolve().parent.parent

FILE_PATH = BASE_DIR / "data" / "messages.txt"

HTML_PATH = BASE_DIR / "app" / "static" / "static.html"

UPLOAD_DIR = BASE_DIR / "uploads"

IMAGE_DIR = UPLOAD_DIR / "images"



UPLOAD_DIR.mkdir(exist_ok=True)

IMAGE_DIR.mkdir(exist_ok=True)




app.mount(
    "/uploads",
    StaticFiles(directory=UPLOAD_DIR),
    name="uploads"
)



class Message(BaseModel):
    text: str


class ModelCreate(BaseModel):
    title: str
    description: str
    format: str


from pydantic import Field


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    model_config = {"from_attributes": True}

class UserLogin(BaseModel):
    email: str
    password: str

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



@app.get("/models", response_model=list[ModelResponse])
def get_models():

    db: Session = SessionLocal()

    try:

        models = db.query(Model).all()

        return models

    finally:

        db.close()




@app.post("/models", response_model=ModelResponse)
def create_model(
    model_data: ModelCreate,
    current_user: User = Depends(get_current_user)
):

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



@app.post("/models/upload", response_model=ModelResponse)
async def upload_model(
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):


    file_extension = (
        Path(file.filename)
        .suffix
        .lower()
    )

    if file_extension != ".blend":

        raise HTTPException(
            status_code=400,
            detail="Разрешены только файлы .blend"
        )




    image_extension = (
        Path(image.filename)
        .suffix
        .lower()
    )

    allowed_images = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }

    if image_extension not in allowed_images:

        raise HTTPException(
            status_code=400,
            detail="Разрешены изображения JPG, JPEG, PNG и WEBP"
        )




    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )




    model_file_path = (
        UPLOAD_DIR /
        file.filename
    )


    with open(
        model_file_path,
        "wb"
    ) as buffer:

        while chunk := await file.read(1024 * 1024):

            buffer.write(chunk)




    image_file_path = (
        IMAGE_DIR /
        image.filename
    )


    with open(
        image_file_path,
        "wb"
    ) as buffer:

        while chunk := await image.read(1024 * 1024):

            buffer.write(chunk)



    file_format = (
        Path(file.filename)
        .suffix
        .lower()
        .replace(".", "")
    )




    db: Session = SessionLocal()

    try:

        model = Model(

            title=title,

            description=description,

            format=file_format.upper(),

            file_path=f"uploads/{file.filename}",

            image_path=f"uploads/images/{image.filename}"

        )

        db.add(model)

        db.commit()

        db.refresh(model)

        return model

    finally:

        db.close()



@app.get("/models/{model_id}", response_model=ModelResponse)
def get_model(model_id: int):

    db: Session = SessionLocal()

    try:

        model = (
            db.query(Model)
            .filter(Model.id == model_id)
            .first()
        )


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

        model = (
            db.query(Model)
            .filter(Model.id == model_id)
            .first()
        )


        if model is None:

            raise HTTPException(
                status_code=404,
                detail="Model not found"
            )


        if not model.file_path:

            raise HTTPException(
                status_code=404,
                detail="File path not found"
            )

#тут поменялось для теста
        # было
        # file_path = BASE_DIR / model.file_path
        # стало
        file_path = UPLOAD_DIR / Path(model.file_path).name


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


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(user_data: UserRegister):

    db: Session = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(
                (User.username == user_data.username) |
                (User.email == user_data.email)
            )
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Username or email already exists"
            )

        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            role="user"
        )

        db.add(new_user)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Username or email already exists"
            )

        db.refresh(new_user)

        return new_user

    finally:
        db.close()

@app.post("/auth/login", response_model=UserResponse)
def login_user(user_data: UserLogin, response: Response):

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == user_data.email)
            .first()
        )

        if not user or not verify_password(
            user_data.password, user.password_hash
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        token = create_session(user.id)

        cookie_secure = os.getenv(
            "COOKIE_SECURE", "true"
        ).lower() == "true"

        response.set_cookie(
            key="session",
            value=token,
            httponly=True,
            secure=cookie_secure,
            samesite="lax",
            max_age=60 * 60 * 24 * 7,
            path="/"
        )

        return user

    finally:
        db.close()


@app.get("/auth/me", response_model=UserResponse)
def get_my_profile(user: User = Depends(get_current_user)):
    return user


@app.post("/auth/logout")
def logout_user(response: Response):
    response.delete_cookie(
        key="session",
        path="/"
    )

    return {"message": "Logged out"}


@app.get("/auth/csrf")
def get_csrf(request: Request, response: Response):
    token = create_csrf_token(response, request)

    response.headers["Cache-Control"] = "no-store"

    return {"csrf_token": token}