from fastapi import UploadFile, HTTPException
from botocore.exceptions import ClientError

from ..config import get_s3_client, AWS_BUCKET_NAME, logger
from ..compression import process_file_for_upload


async def upload_file_to_s3(file: UploadFile, folder: str = None, object_name: str = None):
    """
    Process and upload a file to an S3 bucket.

    :param file: File to upload
    :param folder: Optional folder path in S3
    :param object_name: S3 object name. If not specified, the original filename is used.
    :return: Dict with upload status and details.
    """
    if object_name is None:
        object_name = file.filename

    if folder:
        folder = folder.rstrip('/')
        object_name = f"{folder}/{object_name}"

    s3_client = get_s3_client()
    try:
        # Process the file for compression or optimization
        processed_content, content_type, content_encoding = await process_file_for_upload(file)

        # Prepare parameters for S3 put_object
        put_params = {
            'Bucket': AWS_BUCKET_NAME,
            'Key': object_name,
            'Body': processed_content,
            'ContentType': content_type
        }
        if content_encoding:
            put_params['ContentEncoding'] = content_encoding

        # Upload the processed file to S3
        response = s3_client.put_object(**put_params)

        # Generate a presigned URL for immediate access
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': AWS_BUCKET_NAME, 'Key': object_name},
            ExpiresIn=3600  # URL expires in 1 hour
        )

        return {
            "success": True,
            "key": object_name,
            "etag": response.get('ETag'),
            "presigned_url": presigned_url,
            "compressed": bool(content_encoding)
        }
    except ClientError as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"S3 upload error: {str(e)}")
    finally:
        await file.close()
        