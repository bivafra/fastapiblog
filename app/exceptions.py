from fastapi import status, HTTPException

UserAlreadyExistsException = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="User already exists"
)

UserNotFoundException = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="User's not found"
)

ForbiddenException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="No permissions for query"
)

IncorrectLoginOrPasswordException = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Incorrect user login or password"
)

CookieNotFound = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid cookie"
)

PostAlreadyExists = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Post with the same title already exists"
)
