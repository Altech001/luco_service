from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional
import logging

from .config import get_s3_client
from .upload.aws_upload import upload_file_to_s3
from .download.aws_download import download_file_from_s3, generate_presigned_url
from .delete.aws_delete import delete_file_from_s3
from .list_file.aws_list import list_all_files_in_s3



aws_router = APIRouter(
    prefix="/aws",
    tags=["aws"],
)

logger = logging.getLogger(__name__)

@aws_router.post("/upload")
async def upload_file(file: UploadFile = File(...), folder: Optional[str] = None):
    try:
        result = await upload_file_to_s3(file, folder)
        return JSONResponse(status_code=201, content=result)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        logger.error(f"Unhandled error during upload: {e}")
        return JSONResponse(status_code=500, content={"detail": "An internal error occurred."})

@aws_router.get("/download/{file_name:path}")
async def download_file(file_name: str):
    try:
        file_content, content_type = await download_file_from_s3(file_name)
        return StreamingResponse(iter([file_content]), media_type=content_type)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

@aws_router.get("/presigned-url/{file_name:path}")
def get_presigned_url(file_name: str, expiration: int = 3600):
    try:
        url = generate_presigned_url(file_name, expiration)
        return {"url": url}
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})


@aws_router.get("/files")
def list_files(prefix: Optional[str] = None, max_items: int = 100):
    try:
        files = list_all_files_in_s3(prefix=prefix, max_items=max_items)
        if files is None:
            raise HTTPException(status_code=500, detail="Error listing files from S3")
        return files
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})


@aws_router.delete("/delete/{file_name:path}")
def delete_file(file_name: str):
    try:
        success = delete_file_from_s3(file_name)
        if not success:
            raise HTTPException(status_code=500, detail="Error deleting file from S3")
        return {"message": f"File {file_name} deleted successfully"}
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})


@aws_router.put("/update/{file_name:path}")
async def update_file(file_name: str, file: UploadFile = File(...)):
    """
    Update an existing file in S3 by overwriting it with a new file.
    """
    try:
        # The upload function handles overwriting, so we can reuse it.
        # We pass the file_name from the path as the object_name.
        result = await upload_file_to_s3(file, object_name=file_name)
        return JSONResponse(status_code=200, content=result)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        logger.error(f"Unhandled error during file update: {e}")
        return JSONResponse(status_code=500, content={"detail": "An internal error occurred."})


