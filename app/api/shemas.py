from typing import List
from pydantic import BaseModel, ConfigDict, computed_field, Field


class BaseModelConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class SPostCreateBase(BaseModelConfig):
    title: str
    content: str
    description: str
    tags: List[str] = []

class SPostCreateWithAuthor(SPostCreateBase):
    author: int

class PostFullResponce(BaseModelConfig):
    id: int
    author: int
    title: str
    content: str
    description: str
