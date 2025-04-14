from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dao import PostDAO
from app.api.shemas import PostFullResponse, PostNotFound
from app.auth.models import User
from app.dependencies.auth_dep import get_current_user_optional
from app.dependencies.dao_dep import get_session_no_commit


async def get_post_info(
        post_id: int,
        session: AsyncSession = Depends(get_session_no_commit),
        user_data: User | None = Depends(get_current_user_optional)
) -> PostFullResponse | PostNotFound:
    id = user_data.id if user_data else None
    return await PostDAO.get_full_post_info(session=session, post_id=post_id, user_id=id)
