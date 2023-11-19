import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

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


def create_credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
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
    expire = datetime.now(UTC) + timedelta(minutes=confirm_token_expire_minutes())
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
        raise create_credentials_exception("Invalid email or password")
    if not verify_password(password, user.password):
        raise create_credentials_exception("Invalid email or password")
    if not user.confirmed:
        raise create_credentials_exception("User has not confirmed email")
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    email: str = get_subject_for_token_type(token, "access")
    user = await get_user(email=email)
    if user is None:
        raise create_credentials_exception("Could not find user for this token")
    return user


def get_subject_for_token_type(
    token: str, token_type: Literal["access", "confirmation"]
) -> str:
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=ALGORITHM)
    except ExpiredSignatureError as e:
        raise create_credentials_exception("Token has expired.") from e
    except JWTError as e:
        raise create_credentials_exception("Invalid token") from e

    email = payload.get("sub")
    if email is None:
        raise create_credentials_exception("Token is missing 'sub' field")

    token_typen: str = payload.get("type")
    if token_typen is None or token_typen != token_type:
        raise create_credentials_exception(
            f"Token has incorrect type, expected '{token_type}"
        )
    return email
