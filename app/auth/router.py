from fastapi import APIRouter, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import session

from app.auth.dao import UsersDAO
from app.auth.schemas import SUserAddDB, SUserAuth, SUserRegister, UserBase, SUserInfo
from app.auth.models import User
from app.dependencies.dao_dep import get_session_no_commit, get_session_with_commit
from app.exceptions import IncorrectLoginOrPasswordException, UserAlreadyExistsException
from app.auth.utils import authenticate_user, set_cookie
from app.dependencies.auth_dep import get_current_admin_user, get_current_user

router = APIRouter()


@router.post("/register")
async def register_user(user_data: SUserRegister,
                        session: AsyncSession = Depends(get_session_with_commit)) -> dict:
    # Check whether user already exists
    existing_user = await UsersDAO.find_one_or_none(
        session=session,
        filters=UserBase(name=user_data.name)
    )
    if existing_user:
        raise UserAlreadyExistsException

    # Add user to database
    user_data_dict = user_data.model_dump()
    user_data_dict.pop("confirm_passwrod", None)

    await UsersDAO.add(session=session, values=SUserAddDB(**user_data_dict))

    return {"message": "You were successfully registered"}


@router.post("/login")
async def auth_user(
        response: Response,
        user_data: SUserAuth,
        session: AsyncSession = Depends(get_session_no_commit)) -> dict:
    """
    Checks correctness of entered data and set cookie for authentication
    """
    user = await UsersDAO.find_one_or_none(
        session=session,
        filters=UserBase(name=user_data.name)
    )

    if not user and not await authenticate_user(user=user, password=user_data.password):
        raise IncorrectLoginOrPasswordException

    set_cookie(response, user.id)
    return {
        "ok": True,
        "message": "Successful authorization"
    }


@router.post("/logout")
async def logout(response: Response):
    """
    Removes cookie from response
    """
    response.delete_cookie("user_access_token")
    return {"message": "Successfully logout"}


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)) -> SUserInfo:
    return SUserInfo.model_validate(user_data)


@router.get("/all_users")
async def get_all_users(session: AsyncSession = Depends(get_session_no_commit),
                        user_data: User = Depends(get_current_admin_user)):
    return await UsersDAO.find_all(session=session)
