"""JWT bearer authentication."""
import os

import jwt
from fastapi import Header, HTTPException


def current_user(authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")
    try:
        return jwt.decode(token, os.environ["JWT_SIGNING_KEY"], algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401) from exc
