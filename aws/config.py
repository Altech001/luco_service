import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from datetime import datetime, timedelta
import io
import os
import logging
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


load_dotenv()


AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
REGION = os.getenv("REGION")

def validate_aws_config():
    missing_vars = []
    if not AWS_ACCESS_KEY:
        missing_vars.append("AWS_ACCESS_KEY")
    if not AWS_SECRET_KEY:
        missing_vars.append("AWS_SECRET_KEY")
    if not AWS_BUCKET_NAME:
        missing_vars.append("AWS_BUCKET_NAME")
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

try:
    validate_aws_config()
except ValueError as e:
    logger.error(f"Configuration error: {str(e)}")


def get_aws_session():
    return boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION
    )

def get_s3_client():
    session = get_aws_session()
    return session.client('s3')