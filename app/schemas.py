
from pydantic import BaseModel, ConfigDict


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    format: str
    file_path: str | None
    image_path: str | None
