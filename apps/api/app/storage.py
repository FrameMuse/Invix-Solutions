import asyncio

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import Settings

CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class Storage:
    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.s3_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        )

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
            return
        except ClientError:
            pass

        try:
            self._client.create_bucket(Bucket=self._bucket)
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")
            if code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                raise

    async def ensure_bucket(self) -> None:
        await asyncio.to_thread(self._ensure_bucket)

    def _put_object(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        await asyncio.to_thread(self._put_object, key, data, content_type)

    def _read(self, key: str) -> tuple[bytes, str] | None:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")
            if code in {"NoSuchKey", "404"}:
                return None
            raise

        data = response["Body"].read()
        content_type = response.get("ContentType") or "application/octet-stream"
        return data, content_type

    async def read(self, key: str) -> tuple[bytes, str] | None:
        return await asyncio.to_thread(self._read, key)
