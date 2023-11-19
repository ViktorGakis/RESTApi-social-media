import logging
import tempfile
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status

from . import router

chunk_size = 1024 * 1024
UPLOAD_DIRECTORY = Path(__file__).resolve().parent.parent.parent / "static/uploads"

logger = logging.getLogger(__name__)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile):
    try:
        # Ensure the upload directory exists
        UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

        file_location = UPLOAD_DIRECTORY / file.filename

        logger.info(f"Saving uploaded file to {file_location}")
        async with aiofiles.open(file_location, "wb") as f:
            while chunk := await file.read(chunk_size):
                await f.write(chunk)

        file_url = f"/static/uploads/{file.filename}"

    except Exception as e:
        logger.error(f"Error while uploading file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error uploading the file",
        ) from e

    return {"detail": f"Successfully uploaded {file.filename}", "file_url": file_url}
