from typing import Optional
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.api.shemas import PostFullResponce
from app.dao.base import BaseDAO
from app.api.models import Post, Tag, PostTag


class PostDAO(BaseDAO):
    model = Post

    @classmethod
    async def get_post_list(cls, session: AsyncSession, author_id: Optional[int] = None, tag: Optional[str] = None,
                            page: int = 1, page_size: int = 10) -> dict:
        """
        Obtains list of published posts with optional filters and paging.

        Args:
            session: Async SQLAlchemy session
            author_id (optional): Author's id for filtering
            tag (optional): Tag for filtering
            page (optional): Page number (starting from 1)
            page_size(optinal): Number of posts per page(from 3 to 100)

        Returns:
            Dict with info about number of posts, pages, list of posts
        """
        # params restrictions
        page_size = max(3, min(page_size, 100))
        page = max(1, page)

        # load tables
        base_query = select(Post).options(
            joinedload(Post.user),
            selectinload(Post.tags)
        ).filter_by(status="published")

        # filtering by author
        if author_id is not None:
            base_query = base_query.filter_by(author=author_id)

        # filteing by tag
        if tag:
            base_query = base_query.join(Post.tags).filter(
                Post.tags.any(
                    Tag.name.ilike(f"%{tag.lower()}%")
                )
            )

        # count rows
        count_query = select(func.count()).select_from(base_query.subquery())
        number_of_rows = await session.scalar(count_query)

        # Return empty page if nothing found in db
        if not number_of_rows:
            return {
                "page": page,
                "total_pages": 0,
                "number_of_rows": 0,
                "posts": []
            }

        # Ceiled number of pages
        total_pages = (number_of_rows + page_size - 1) // page_size

        # Select required page
        offset = (page - 1) * page_size
        paginated_query = base_query.offset(offset).limit(page_size)

        # Perfom constructed query
        result = await session.execute(paginated_query)
        posts = result.scalars().all()
        posts = [PostFullResponce.model_validate(post) for post in posts]

        # Loggin
        filters = []
        if author_id is not None:
            filters.append(f"author_id={author_id}")
        if tag:
            filters.append(f"tag={tag}")
        filter_str = " & ".join(filters) if filters else "no filters"

        logger.info(
            f"Page {page} fetched with {
                len(posts)} posts, filters: {filter_str}")

        return {
            "page": page,
            "total_pages": total_pages,
            "number_of_rows": number_of_rows,
            "posts": posts
        }

    @classmethod
    async def get_full_post_info(
            cls, session: AsyncSession, post_id: int, user_id: Optional[int] = None):
        """
        Returns full post information.
        If post is public - info is available for all users.
        For drafts info is available only for author.
        """
        # Query with loading data about user(author) and tags
        query = (
            select(Post)
            .options(
                joinedload(Post.user),
                selectinload(Post.tags)
            )
            .filter_by(id=post_id)
        )

        result = await session.execute(query)
        post = result.scalar_one_or_none()

        # If post not found
        if not post:
            return {
                "message": f"Post with ID {post_id} not found.",
                "status": "error"
            }

        # Check whether user is the author in casee of draft
        if post.status == "draft" and (user_id != post.author):
            return {
                "message": "This post is a draft and only authors have access to it",
                "status": "error"
            }

        return post

    @classmethod
    async def change_post_status(
            cls, session: AsyncSession, post_id: int, new_status: str, user_id: int) -> dict:
        """
        Changes the post's status. Available only for post's author.

        Args:
            session: Async SQLAlchemy session
            post_id: Id of post to change
            new_status: New post status - allowed values are "published", "draft"
            user_id: Id of user that tries change the status

        Returns:
            Dict with info about operation
        """

        if new_status not in ["draft", "published"]:
            return {
                "message": "Недопустимый статус. Используйте 'draft' или 'published'.",
                "status": "error"
            }

        try:
            # Find post by id
            query = select(Post).filter_by(id=post_id)
            result = await session.execute(query)
            post = result.scalar_one_or_none()

            if not post:
                return {
                    "message": f"Post with ID {post_id} not found.",
                    "status": "error"
                }

            # Check whether the user is the author of the post
            if post.author != user_id:
                return {
                    "message": "You haven't permissions to change this post",
                    "status": "error"
                }

            # Если текущий статус совпадает с новым, возвращаем сообщение без
            # изменений
            if post.status == new_status:
                return {
                    "message": f"Post already has status '{new_status}'.",
                    "status": "info",
                    "post_id": post_id,
                    "current_status": new_status
                }

            # Change post status
            post.status = new_status
            await session.flush()

            return {
                "message": f"Post's status has successfully changed to {new_status}'.",
                "status": "success",
                "post_id": post_id,
                "new_status": new_status
            }

        except SQLAlchemyError as e:
            await session.rollback()
            return {
                "message": f"Internal error occured while changing post's status: {str(e)}",
                "status": "error"
            }

    @classmethod
    async def delete_post(cls, session: AsyncSession,
                          post_id: int, user_id: int) -> dict:
        """
        Deletes given post. Available only for post's author.

        Args:
            session: Async SQLAlchemy session
            post_id: Id of post to delete
            user_id: Id of user that tries to delete post

        Returns:
            Dict with info about operation
        """
        try:
            # Find post by id
            query = select(Post).filter_by(id=post_id)
            result = await session.execute(query)
            post = result.scalar_one_or_none()

            if not post:
                return {
                    'message': f"Post with ID {post_id} not found.",
                    'status': 'error'
                }

            # Checks whether the user is the post's author
            if post.author != user_id:
                return {
                    'message': "You haven't permissions to delete this post",
                    'status': 'error'
                }

            # Remove post
            await session.delete(post)
            await session.flush()

            return {
                'message': f"Post with ID {post_id} has been successfully deleted.",
                'status': 'success'
            }

        except SQLAlchemyError as e:
            await session.rollback()
            return {
                'message': f"Internal error occured while deleting the post: {str(e)}",
                'status': 'error'
            }


class TagDAO(BaseDAO):
    model = Tag

    @classmethod
    async def add_tags(cls, session: AsyncSession,
                       tag_names: list[str]) -> list[int]:
        """
        Adds tags to the database.

        Args:
            session: Async SQLAlchemy session
            tag_name: List of tag names to add

        Returns:
            List of tags id
        """
        tag_ids = []
        for tag_name in tag_names:
            # Only lower case is allowed
            tag_name = tag_name.lower()

            # Find tag in the db
            query = select(Tag).filter_by(name=tag_name)
            result = await session.execute(query)
            tag = result.scalar_one_or_none()

            # If tag exists - simply add it to the return list
            if tag:
                tag_ids.append(tag.id)

            # Otherwise add to db and add its id to the return list
            else:
                new_tag = Tag(name=tag_name)
                session.add(new_tag)
                try:
                    await session.flush()
                    logger.info(
                        f"Tag '{tag_name}' has been successfully added to the database.")
                    tag_ids.append(new_tag.id)

                except SQLAlchemyError as e:
                    await session.rollback()
                    logger.error(
                        f"Internal error occured while adding the tag '{tag_name}': {e}")
                    raise e

        return tag_ids


class PostTagDAO(BaseDAO):
    model = PostTag

    @classmethod
    async def add_post_tags(cls, session: AsyncSession,
                            post_tag_pairs: list[dict]) -> None:
        """
        Method for multiple linkage post-tag in the database.

        Args:
            session: Async SQLAlchemy session
            post_tag_pairs: List of dicts-pairs with keys 'post_id' and 'tag_id'
        """
        # Create all instanses
        post_tag_insts = []
        for pair in post_tag_pairs:
            post_id = pair.get('post_id')
            tag_id = pair.get('tag_id')

            if post_id and tag_id:
                post_tag = PostTag(post_id=post_id, tag_id=tag_id)
                post_tag_insts.append(post_tag)

            else:
                logger.warning(f"Skipped a parametr in pair: {pair}")

        if not post_tag_insts:
            logger.warning("No valid or any data to add in PostTag")
            return

        session.add_all(post_tag_insts)
        try:
            await session.flush()
            logger.info(
                f"{len(post_tag_insts)} pairs post-tag successfully added.")

        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(
                f"Internall error while addid pairs post-tag in database: {e}")
            raise e
