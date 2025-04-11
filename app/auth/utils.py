from fastapi import Response


def set_cookie(response: Response, user_id: int) -> None:
    # TODO: use JTW
    response.set_cookie(
        key="user_access_token",
        value=str(user_id),
        httponly=True
    )


async def authenticate_user(user, password):
    """
    Tries to authenticate given user's database obj and
    entered password.

    Args:
        user : Real database user object
        password : entered password

    Returns:
        Given user if password is correct.
        Otherwise None
    """
    if not user or user.password != password:
        return None
    return user
