from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import values
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_409_CONFLICT, HTTP_500_INTERNAL_SERVER_ERROR

from app.api.dao import PostDAO, PostTagDAO, TagDAO
from app.api.shemas import SPostCreateBase, SPostCreateWithAuthor
from app.auth.models import User
from app.dependencies.auth_dep import get_current_user
from app.dependencies.dao_dep import get_session_with_commit
from app.exceptions import PostAlreadyExists

router = APIRouter(prefix="/api", tags=["API"])

@router.post("/posts", summary="Adding a new post with tags")
async def add_post(
        add_data: SPostCreateBase,
        user_data: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session_with_commit)
):
    post_dict = add_data.model_dump()
    post_dict["author"] = user_data.id
    tags = post_dict.pop("tags", [])

    try:
        post = await PostDAO.add(session=session, 
                                 values=SPostCreateWithAuthor.model_validate(post_dict))
        post_id = post.id

        if tags:
            tag_ids = await TagDAO.add_tags(session=session,
                                            tag_names=tags)
            await PostTagDAO.add_post_tags(session=session,
                                           post_tag_pairs=[{
                                           "post_id": post_id, "tag_id": id }for id in tag_ids
                                           ])
        return {"status": "success", "message": f"Post with ID {post_id} has been successfully added"}

    except IntegrityError as e:
        if "UNIQUE constraint failed" in str(e.orig):
            raise PostAlreadyExists

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Some went wrong while adding post")
