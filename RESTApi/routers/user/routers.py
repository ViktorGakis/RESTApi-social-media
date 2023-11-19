import logging

from fastapi import HTTPException, Request, status

from ...db import comment_table, database, post_table, user_table
from ...models import (
    Comment,
    CommentIn,
    UserIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)
from ...security import (
    authenticate_user,
    create_access_token,
    create_confirmation_token,
    get_password_hash,
    get_subject_for_token_type,
    get_user,
)
from . import router

logger: logging.Logger = logging.getLogger(__name__)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserIn, request: Request):
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A user with that email already exists .",
        )

    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(email=user.email, password=hashed_password)

    logger.debug(query)

    await database.execute(query)

    return {
        "detail": "User created",
        "confirmation_url": request.url_for(
            "confirm_email", token=create_confirmation_token(user.email)
        ),
    }


@router.post("/token", status_code=status.HTTP_201_CREATED)
async def login(user: UserIn):
    user = await authenticate_user(user.email, user.password)
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}


async def find_post(post_id: int):
    logger.info("Finding post with id:%s", post_id)
    query = post_table.select().where(post_table.c.id == post_id)
    logger.debug(query)
    return await database.fetch_one(query)


@router.get("/", status_code=status.HTTP_200_OK)
async def root(request: Request):
    return {"data": "banana", "ip": request.client.host}


@router.post("/post", response_model=UserPost, status_code=status.HTTP_201_CREATED)
async def create_post(post: UserPostIn):
    logger.info("Creating a post.")
    data = post.model_dump()

    query = post_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post", response_model=list[UserPost])
async def get_all_posts():
    logger.info("Getting all posts.")
    query = post_table.select()

    logger.debug(query)
    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(comment: CommentIn):
    logger.info("Creating a comment")
    post = await find_post(comment.post_id)
    if not post:
        logging.error("Post with id %s not found", comment.post_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found."
        )

    data = comment.model_dump()
    query = comment_table.insert().values(data)
    logger.debug(query)

    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get(
    "/post/{post_id}/comment",
    response_model=list[Comment],
    status_code=status.HTTP_200_OK,
)
async def get_comments_on_post(post_id: int):
    logger.info("Getting comments on post")
    # return [
    #     comment for comment in comment_table.values() if comment["post_id"] == post_id
    # ]
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    logger.debug(query)
    return await database.fetch_all(query)


@router.get(
    "/post/{post_id}",
    response_model=UserPostWithComments,
    status_code=status.HTTP_200_OK,
)
async def get_post_with_comments(post_id: int):
    logger.info("Getting post and its comments")
    post = await find_post(post_id)
    if not post:
        logging.error("Post with post_id: %s, not found", post_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    return {"post": post, "comments": await get_comments_on_post(post_id)}


@router.get("/confirm/{token}")
async def confirm_email(token: str):
    email: str = get_subject_for_token_type(token, "confirmation")
    query = (
        user_table.update().where(user_table.c.email == email).values(confirmed=True)
    )
    logger.debug(query)

    await database.execute(query)
    return {"detail": "User confirmed"}
