import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from .db import database, user_table

logger: logging.Logger = logging.getLogger(__name__)

# openssl rand -base64 55
SECRET_KEY = "lFCXytdXwZAtsyALaJG9R+DKZKM03HQgDThtguKrRWXBNpbgREp"
ALGORITHM = "HS256"

# tokenUrl specifies the endpoint in the API that will handle
# or relative URL to your API's token endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def confirm_token_expire_minutes():
    return 1440


def create_access_token(email: str):
    logger.debug("Creating confirmation token", extra={"email": email})
    expire: datetime = datetime.now(UTC) + timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data: dict = {"sub": email, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_confirmation_token(email: str):
    logger.debug("Creating confirmation token", extra={"email": email})
    expire = datetime.now(UTC) + timedelta(minutes=access_token_expire_minutes())
    jwt_data = {"sub": email, "exp": expire, "type": "confirmation"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def access_token_expire_minutes() -> int:
    return 30


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


async def get_user(email: str):
    logger.debug("Fetching user from the db", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    result = await database.fetch_one(query)
    if result:
        return result


async def authenticate_user(email: str, password: str):
    logger.debug("Authenticating user...", extra={"email", email})
    user = await get_user(email)
    if not user:
        raise credentials_exception
    if not verify_password(password, user.password):
        raise credentials_exception
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = await verify_token(token)
    if user is None:
        raise credentials_exception
    return user


async def verify_token(token: str):
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=ALGORITHM)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        email = payload.get("sub")
        if email is None:
            return None
        token_type = payload.get("type")
        if token_type is None or token_type != "access":
            raise credentials_exception
        return await get_user(email=email)
