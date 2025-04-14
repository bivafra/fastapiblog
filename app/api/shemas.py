from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict, Field, computed_field


class BaseModelConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SPostCreateBase(BaseModelConfig):
    title: str
    content: str
    description: str
    tags: List[str] = []


class SPostCreateWithAuthor(SPostCreateBase):
    author: int


class UserBase(BaseModelConfig):
    id: int
    name: str


class TagResponse(BaseModelConfig):
    id: int
    name: str


class PostFullResponse(BaseModelConfig):
    id: int
    author: int
    title: str
    content: str
    description: str
    created_at: datetime
    status: str
    tags: List[TagResponse]
    user: UserBase = Field(exclude=True)

    @computed_field
    @property
    def author_id(self) -> int | None:
        return self.user.id if self.user else None

    @computed_field
    @property
    def author_name(self) -> str | None:
        return self.user.name if self.user else None


class PostNotFound(BaseModelConfig):
    message: str
    status: str
