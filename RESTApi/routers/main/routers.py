import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from fastapi import Depends, HTTPException, status

from RESTApi.models.post import (
    Comment,
    CommentIn,
    PostLike,
    PostLikeIn,
    UserPostWithComments,
)
from RESTApi.security import get_current_user

from ...db import comment_table, database, like_table, post_table
from ...models import User, UserPost, UserPostIn
from . import router

# these were pre database
# post_table: dict = {}
# comment_table: dict = {}


logger: logging.Logger = logging.getLogger(__name__)

select_post_and_likes = (
    sqlalchemy.select(post_table, sqlalchemy.func.count(like_table.c.id).label("likes"))
    .select_from(post_table.outerjoin(like_table))
    .group_by(post_table.c.id)
)


async def find_post(post_id: int):
    logger.info("Finding post with id:%s", post_id)
    query = post_table.select().where(post_table.c.id == post_id)
    logger.debug(query)
    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: UserPostIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Creating a post.")
    data = {**post.model_dump(), "user_id": current_user.id}

    query = post_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


class PostSorting(str, Enum):
    new: str = "new"
    old: str = "old"
    most_likes: str = "most_likes"


@router.get("/post", response_model=list[UserPost])
async def get_all_posts(sorting: PostSorting = PostSorting.new):
    logger.info("Getting all posts.")

    if sorting == PostSorting.new:
        query = select_post_and_likes.order_by(post_table.c.id.desc())
    elif sorting == PostSorting.old:
        query = select_post_and_likes.order_by(post_table.c.id.asc())
    elif sorting == PostSorting.most_likes:
        query = select_post_and_likes.order_by(
            sqlalchemy.desc(sqlalchemy.text("likes"))
        )

    logger.debug(query)
    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment: CommentIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Creating a comment")
    post = await find_post(comment.post_id)
    if not post:
        logging.error("Post with id %s not found", comment.post_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found."
        )
    data = {**comment.model_dump(), "user_id": current_user.id}
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
    query = select_post_and_likes.where(post_table.c.id == post_id)
    logger.debug(query)
    post = await database.fetch_one(query)
    if not post:
        logging.error("Post with post_id: %s, not found", post_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    return {"post": post, "comments": await get_comments_on_post(post_id)}


@router.post("/like", response_model=PostLike, status_code=status.HTTP_201_CREATED)
async def like_post(
    like: PostLikeIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Liking post")

    post: UserPost | None = await find_post(like.post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    data = {**like.model_dump(), "user_id": current_user.id}
    query = like_table.insert().values(data)

    logger.debug(query)

    last_record_id = await database.execute(query)

    return {**data, "id": last_record_id}
