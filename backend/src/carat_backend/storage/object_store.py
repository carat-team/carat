import io

from minio import Minio
from minio.error import S3Error

from carat_backend.settings import ObjectStorageCredentials, ObjectStorageSettings

# Another request created the bucket between our check and our create
_BUCKET_RACE_CODES = {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}


class PhotoObjectStore:
    """Photo bytes in an S3-compatible bucket (MinIO locally, any S3 service in production)."""

    def __init__(self, client: Minio, bucket: str) -> None:
        self._client = client
        self._bucket = bucket
        self._bucket_ready = False

    def put(self, key: str, content: bytes, content_type: str) -> None:
        self._ensure_bucket()
        self._client.put_object(
            bucket_name=self._bucket,
            object_name=key,
            data=io.BytesIO(content),
            length=len(content),
            content_type=content_type,
        )

    def get(self, key: str) -> bytes:
        response = self._client.get_object(bucket_name=self._bucket, object_name=key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, key: str) -> None:
        self._client.remove_object(bucket_name=self._bucket, object_name=key)

    def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return
        if not self._client.bucket_exists(bucket_name=self._bucket):
            try:
                self._client.make_bucket(bucket_name=self._bucket)
            except S3Error as error:
                if error.code not in _BUCKET_RACE_CODES:
                    raise
        self._bucket_ready = True


def create_photo_object_store(
    settings: ObjectStorageSettings, credentials: ObjectStorageCredentials
) -> PhotoObjectStore:
    client = Minio(
        endpoint=settings.endpoint,
        access_key=credentials.access_key,
        secret_key=credentials.secret_key,
        secure=settings.secure,
    )
    return PhotoObjectStore(client, settings.bucket)
