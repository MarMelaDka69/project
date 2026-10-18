import os
import secrets
import hmac

from fastapi import HTTPException, Request, Response
from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature,
)

from app.auth import secret_key


CSRF_MAX_AGE = 60 * 60
CSRF_COOKIE_NAME = "csrf_token"

csrf_serializer = URLSafeTimedSerializer(
    secret_key,
    salt="csrf-protection",
)


def create_csrf_token(response: Response, request: Request) -> str:
    existing_token = request.cookies.get(CSRF_COOKIE_NAME)

    if existing_token:
        try:
            csrf_serializer.loads(
                existing_token,
                max_age=CSRF_MAX_AGE,
            )
            return existing_token
        except BadSignature:
            pass

    token = csrf_serializer.dumps(
        secrets.token_urlsafe(32)
    )

    cookie_secure = os.getenv(
        "COOKIE_SECURE", "true"
    ).lower() == "true"

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=cookie_secure,
        samesite="lax",
        max_age=CSRF_MAX_AGE,
        path="/",
    )

    return token


def verify_csrf(request: Request) -> None:
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get("X-CSRF-Token")

    if not cookie_token or not header_token:
        raise HTTPException(
            status_code=403,
            detail="CSRF token missing",
        )

    if not hmac.compare_digest(cookie_token, header_token):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token",
        )

    try:
        csrf_serializer.loads(
            cookie_token,
            max_age=CSRF_MAX_AGE,
        )
    except BadSignature:
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired CSRF token",
        )