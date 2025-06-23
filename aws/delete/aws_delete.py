from fastapi import HTTPException
from botocore.exceptions import ClientError

from ..config import get_s3_client, AWS_BUCKET_NAME, logger

def delete_file_from_s3(file_name: str):
    """
    Delete a file from an S3 bucket
    
    :param file_name: File to delete
    :return: Success status
    """
    s3_client = get_s3_client()
    try:
        s3_client.delete_object(Bucket=AWS_BUCKET_NAME, Key=file_name)
        return True
    except ClientError as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=f"S3 deletion error: {str(e)}")