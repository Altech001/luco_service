from fastapi import HTTPException
from botocore.exceptions import ClientError
import logging

from ..config import get_s3_client, AWS_BUCKET_NAME, logger


async def download_file_from_s3(file_name: str):
    """
    Download a file from an S3 bucket

    :param file_name: File to download
    :return: File contents if successful
    """
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(Bucket=AWS_BUCKET_NAME, Key=file_name)
        content_type = response.get('ContentType', 'application/octet-stream')
        return response['Body'].read(), content_type
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise HTTPException(status_code=404, detail=f"File {file_name} not found")
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=f"S3 download error: {str(e)}")


def generate_presigned_url(file_name: str, expiration: int = 3600):
    """
    Generate a presigned URL for an S3 object

    :param file_name: File for which to generate URL
    :param expiration: Time in seconds until URL expires
    :return: Presigned URL
    """
    s3_client = get_s3_client()
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': AWS_BUCKET_NAME, 'Key': file_name},
            ExpiresIn=expiration
        )
        return response
    except ClientError as e:
        logger.error(f"Error generating presigned URL: {e}")
        raise HTTPException(status_code=500, detail=f"S3 URL generation error: {str(e)}")
