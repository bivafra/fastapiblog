from typing import TYPE_CHECKING
from sqlalchemy import text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dao.database import Base, str_uniq
if TYPE_CHECKING:
    from app.api.models import Post
else:
    Post = "Post"


class Role(Base):
    name: Mapped[str_uniq]
    users: Mapped[list["User"]] = relationship(back_populates="role")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"


class User(Base):
    name: Mapped[str_uniq]
    password: Mapped[str]

    role_id: Mapped[int] = mapped_column(ForeignKey('role.id'), default=1,
                                         server_default=text("1"))
    role: Mapped["Role"] = relationship(back_populates="users", lazy="joined")

    posts: Mapped[list["Post"]] = relationship(back_populates="user")

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id})"
