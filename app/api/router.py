from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dao import PostDAO, PostTagDAO, TagDAO
from app.api.shemas import PostFullResponse, PostNotFound, SPostCreateBase, SPostCreateWithAuthor
from app.auth.models import User
from app.dependencies.auth_dep import get_current_user
from app.dependencies.dao_dep import get_session_no_commit, get_session_with_commit
from app.dependencies.post_dep import get_post_info
from app.exceptions import PostAlreadyExists

router = APIRouter(prefix="/api", tags=["Posts"])


@router.post("/posts", summary="Add a new post with tags")
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
                                               "post_id": post_id, "tag_id": id} for id in tag_ids
                                           ])
        return {"status": "success",
                "message": f"Post with ID {post_id} has been successfully added"}

    except IntegrityError as e:
        if "UNIQUE constraint failed" in str(e.orig):
            raise PostAlreadyExists

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while adding post")


@router.get("/posts/{post_id}", summary="Get post's info")
async def get_post(
        post_id: int,
        post_info: PostFullResponse | PostNotFound = Depends(get_post_info)
) -> PostFullResponse | PostNotFound:
    return post_info


@router.get("/posts", summary="Get all published posts")
async def get_posts(
    author_id: int | None = None,
    tag: str | None = None,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(
        default=3,
        ge=3,
        le=100,
        description="Posts in a page"),
    session: AsyncSession = Depends(get_session_no_commit)
):
    try:
        result = await PostDAO.get_post_list(session=session, author_id=author_id,
                                             tag=tag, page=page, page_size=page_size)
        return result if result["posts"] else PostNotFound(
            message="Posts not found", status="error")
    except Exception as e:
        logger.error(f"Error while receiving posts: {e}")
        # For consistensy there should be HTTPException here, but for learning
        # purpose i tried this
        return JSONResponse(status_code=500, content={
                            "detail": "Internal server error"})


@router.delete("/posts/{post_id}", summary="Delete post")
async def delete_post(
        post_id: int,
        session: AsyncSession = Depends(get_session_with_commit),
        current_user: User = Depends(get_current_user)
):
    result = await PostDAO.delete_post(session=session, post_id=post_id, user_id=current_user.id)
    if result["status"] == "error":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=result["message"]
                            )
    return result


@router.patch("/posts/{post_id}", summary="Change post status")
async def change_post_status(
        post_id: int,
        new_status: str,
        session: AsyncSession = Depends(get_session_with_commit),
        current_user: User = Depends(get_current_user)
):
    result = await PostDAO.change_post_status(session=session, post_id=post_id,
                                              new_status=new_status, user_id=current_user.id)
    if result["status"] == "error":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=result["message"]
                            )
    return result
