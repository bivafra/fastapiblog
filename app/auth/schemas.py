from typing import Self
from pydantic import BaseModel, Field, ConfigDict, model_validator, computed_field


class UserBase(BaseModel):
    name: str = Field(min_length=3, max_length=20,
                      description="Nickname")
    model_config = ConfigDict(from_attributes=True)


class SUserRegister(UserBase):
    password: str = Field(min_length=5, max_length=50,
                          description="Password, 5 - 50 chars")
    confirm_password: str = Field(min_length=5, max_length=50,
                                  description="Repeat password")

    @model_validator(mode="after")
    def check_password(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords mismatch")
        return self


class SUserAddDB(UserBase):
    password: str = Field(min_length=5, max_length=50)


class SUserAuth(UserBase):
    password: str = Field(min_length=5, max_length=50)


class RoleModel(BaseModel):
    id: int = Field()
    name: str = Field()
    model_config = ConfigDict(from_attributes=True)


class SUserInfo(UserBase):
    id: int = Field()
    role: RoleModel = Field(exclude=True)

    @computed_field
    def role_id(self) -> int:
        return self.role.id

    @computed_field
    def role_name(self) -> str:
        return self.role.name
