from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text

from app.dao.database import Base, str_uniq
from app.auth.models import User


class Post(Base):
    title: Mapped[str_uniq]

    # Brief description of the post
    description: Mapped[str] = mapped_column(Text)

    content: Mapped[str] = mapped_column(Text)
    # May be published or draft
    status: Mapped[str] = mapped_column(
        default="published", server_default="published") 

    author: Mapped[int] = mapped_column(ForeignKey("user.id"),
                                        nullable=False)
    user: Mapped["User"] = relationship(back_populates="posts")

    tags: Mapped[list["Tag"]] = relationship(
        secondary="posttag",
        back_populates="posts"
    )


class Tag(Base):
    name: Mapped[str] = mapped_column(String(20), unique=True)

    posts: Mapped[list["Post"]] = relationship(
        secondary="posttag",
        back_populates="tags"
    )


class PostTag(Base):
    post_id: Mapped[int] = mapped_column(
        ForeignKey("post.id", ondelete="CASCADE"),
        nullable=False)
    tag_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tag.id",
            ondelete="CASCADE"),
        nullable=False)

    __table_args__ = (
        UniqueConstraint("post_id", "tag_id", name="uq_post_tag"),
    )
