import io
import gzip
from PIL import Image
from fastapi import UploadFile

async def process_file_for_upload(file: UploadFile):
    """
    Process a file for upload by compressing or optimizing it based on its content type.

    :param file: The file to process.
    :return: A tuple containing the processed content, the new content type, and content encoding (if any).
    """
    content = await file.read()
    content_type = file.content_type
    content_encoding = None

    # Optimize images
    if content_type in ["image/jpeg", "image/png"]:
        try:
            image = Image.open(io.BytesIO(content))
            # You can add resizing logic here if needed, e.g., image.thumbnail((1024, 1024))
            
            output = io.BytesIO()
            if content_type == "image/jpeg":
                image.save(output, format='JPEG', quality=85, optimize=True)
            else: # PNG
                image.save(output, format='PNG', optimize=True)
            
            content = output.getvalue()
            
        except Exception:
            # If optimization fails, use the original content
            pass

    # Compress text-based files
    elif content_type in ["text/plain", "text/html", "text/css", "application/javascript", "application/json", "text/csv"]:
        output = io.BytesIO()
        with gzip.GzipFile(fileobj=output, mode='wb') as f:
            f.write(content)
        content = output.getvalue()
        content_encoding = 'gzip'

    # Reset file pointer before returning
    await file.seek(0)
    
    return content, content_type, content_encoding
