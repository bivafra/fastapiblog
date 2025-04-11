from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dao import UsersDAO
from app.dependencies.dao_dep import get_session_no_commit
from app.exceptions import CookieNotFound, ForbiddenException, UserNotFoundException
from app.auth.models import User

def get_access_token(request: Request) -> str:
    """
    Extract access_token from cookie header
    """
    token = request.cookies.get("user_access_token")
    if not token:
        raise CookieNotFound
    return token

async def get_current_user(
        token: str = Depends(get_access_token),
        session: AsyncSession = Depends(get_session_no_commit)
) -> User:
    """Checks whether current user is registered"""
    user_id = int(token)
    user = await UsersDAO.find_one_or_none_by_id(session=session, data_id=user_id)
    if not user: 
        raise UserNotFoundException
    return user

async def get_current_admin_user(cur_user: User = Depends(get_current_user)):
    """Checks whether current user have admin permissions and returns it"""
    if cur_user.role_id in [3, 4]:
        return cur_user
    raise ForbiddenException
