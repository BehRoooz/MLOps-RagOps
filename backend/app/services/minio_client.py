"""
This module is used to interact with the Minio server.

It uses the Minio client to upload files to the Minio server.
"""

from minio import Minio
from io import BytesIO
from app.core.config import settings

# Remove https:// or http:// from the endpoint
_endpoint = settings.MINIO_ENDPOINT.replace("https://", "").replace("http://", "")

# Initialize the Minio client
minio_client = Minio(
    _endpoint,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)

# Ensure the bucket exists
def ensure_bucket():
    if not minio_client.bucket_exists(settings.MINIO_BUCKET):
        minio_client.make_bucket(settings.MINIO_BUCKET)

# Upload a file to the bucket
def upload_file(filename: str, content: bytes) -> str:
    ensure_bucket()
    minio_client.put_object(
        settings.MINIO_BUCKET, filename, BytesIO(content), length=len(content),
    )
    return f"s3://{settings.MINIO_BUCKET}/{filename}"