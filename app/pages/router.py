from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dao import PostDAO
from app.api.shemas import PostFullResponse, PostNotFound
from app.auth.models import User
from app.dependencies.auth_dep import get_current_user_optional
from app.dependencies.dao_dep import get_session_no_commit
from app.dependencies.post_dep import get_post_info


router = APIRouter(tags=["Frontend"])

templates = Jinja2Templates(directory="app/templates")


@router.get('/posts/{post_id}/')
async def get_post(
        request: Request,
        post_id: int,
        post_info: PostFullResponse | PostNotFound = Depends(get_post_info),
        user_data: User | None = Depends(get_current_user_optional)
):
    if isinstance(post_info, dict):
        return templates.TemplateResponse(
            "404.html", {"request": request, "post_id": post_id}
        )

    post = PostFullResponse.model_validate(post_info).model_dump()
    return templates.TemplateResponse(
        "post.html",
        {"request": request,
         "article": post,
         "current_user_id": user_data.id if user_data else None}
    )


@router.get('/posts')
async def get_posts(
    request: Request,
    author_id: int | None = None,
    tag: str | None = None,
    page: int = 1,
    page_size: int = 3,
    session: AsyncSession = Depends(get_session_no_commit)
):
    posts = await PostDAO.get_post_list(
        session=session,
        author_id=author_id,
        tag=tag,
        page=page,
        page_size=page_size
    )

    return templates.TemplateResponse(
        "posts.html",
        {
            "request": request,
            "article": posts,
            "filters": {
                "author_id": author_id,
                "tag": tag
            }
        }
    )
