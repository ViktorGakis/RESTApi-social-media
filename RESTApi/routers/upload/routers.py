import logging
import tempfile
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status

from . import router

chunk_size = 1024 * 1024
UPLOAD_DIRECTORY = Path(".../static/assets/")

logger = logging.getLogger(__name__)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile):
    try:
        with tempfile.namedtemporaryfile() as temp_file:
            filename = temp_file.name
            logger.info(f"saving uploaded file temporarily to {filename}")
            file_location = f"{UPLOAD_DIRECTORY}/{file.filename}"
            async with aiofiles.open(file_location, "wb") as f:
                while chunk := await file.read(chunk_size):
                    await f.write(chunk)

            file_url = f"/static/{file.filename}"

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="there was an error uploading the file",
        )

    return {"detail": f"successfully uploaded {file.filename}", "file_url": file_url}
