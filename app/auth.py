import os

from dotenv import load_dotenv
from fastapi import HTTPException, Request
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.database import SessionLocal
from app.models import User


load_dotenv()

secret_key = os.getenv("SESSION_SECRET_KEY")

if not secret_key:
    raise RuntimeError("SESSION_SECRET_KEY is not configured")

serializer = URLSafeTimedSerializer(secret_key, salt="auth-session")

SESSION_MAX_AGE = 60 * 60 * 24 * 7


def create_session(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})


def get_current_user(request: Request) -> User:
    token = request.cookies.get("session")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
        user_id = int(data["user_id"])
    except (BadSignature, SignatureExpired, KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session"
        )

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        db.expunge(user)
        return user

    finally:
        db.close()