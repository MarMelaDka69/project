
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main
from app.database import Base


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    monkeypatch.setattr(
        main,
        "SessionLocal",
        TestingSessionLocal,
    )

    upload_dir = tmp_path / "uploads"
    image_dir = upload_dir / "images"
    data_dir = tmp_path / "data"

    upload_dir.mkdir()
    image_dir.mkdir()
    data_dir.mkdir()

    messages_file = data_dir / "messages.txt"
    messages_file.write_text("", encoding="utf-8")

    monkeypatch.setattr(main, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(main, "IMAGE_DIR", image_dir)
    monkeypatch.setattr(main, "FILE_PATH", messages_file)

    with TestClient(main.app) as client:
        yield {
            "client": client,
            "session_factory": TestingSessionLocal,
            "upload_dir": upload_dir,
            "image_dir": image_dir,
            "messages_file": messages_file,
        }

    engine.dispose()


@pytest.fixture
def client(test_env):
    return test_env["client"]
