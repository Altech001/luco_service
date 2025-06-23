from botocore.exceptions import ClientError

from ..config import get_s3_client, AWS_BUCKET_NAME, logger

def list_all_files_in_s3(prefix: str = None, max_items: int = 1000):
    
    s3_client = get_s3_client()
    try:
        params = {
            'Bucket': AWS_BUCKET_NAME,
            'MaxKeys': max_items
        }
        
        if prefix:
            params['Prefix'] = prefix
            
        response = s3_client.list_objects_v2(**params)
        
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"')
                })
        return files
    except ClientError as e:
        logger.error(f"Error listing files: {e}")
        return None