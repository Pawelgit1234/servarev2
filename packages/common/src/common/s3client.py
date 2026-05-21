import asyncio
import hashlib
import json
from contextlib import asynccontextmanager

from aiobotocore.session import get_session
from botocore.exceptions import ClientError

from common.settings import (
    S3_BUCKET,
    S3_ENDPOINT,
    S3_PUBLIC_READ_POLICY,
    S3_ROOT_PASSWORD,
    S3_ROOT_USER,
)


class S3Client:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        bucket_name: str,
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
            "region_name": "us-east-1",
        }

        self.bucket_name = bucket_name
        self.session = get_session()

        self._bucket_ready = False
        self._bucket_lock = asyncio.Lock()

    @asynccontextmanager
    async def get_client(self):  # type: ignore
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def ensure_bucket_exists(self) -> None:
        if self._bucket_ready:
            return

        async with self._bucket_lock:
            async with self.get_client() as client:
                try:
                    await client.head_bucket(Bucket=self.bucket_name)
                except ClientError:
                    await client.create_bucket(Bucket=self.bucket_name)

                    await client.put_bucket_policy(
                        Bucket=self.bucket_name,
                        Policy=json.dumps(S3_PUBLIC_READ_POLICY),
                    )

            self._bucket_ready = True

    async def file_exists(self, key: str) -> bool:
        async with self.get_client() as client:
            try:
                await client.head_object(Bucket=self.bucket_name, Key=key)
                return True
            except ClientError:
                return False

    async def upload_bytes(
        self,
        data: bytes,
        object_name: str | None,
        prefix: str,
        content_type: str | None = None,
        deduplicate: bool = False,
    ) -> str:
        await self.ensure_bucket_exists()

        if object_name is None:
            object_name = hashlib.md5(data).hexdigest()

        key = f"{prefix}/{object_name}"

        if deduplicate:  # noqa: SIM102
            if await self.file_exists(key):
                return object_name

        async with self.get_client() as client:
            await client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

        return object_name


s3 = S3Client(
    access_key=S3_ROOT_USER,  # type: ignore
    secret_key=S3_ROOT_PASSWORD,  # type: ignore
    endpoint_url=S3_ENDPOINT,
    bucket_name=S3_BUCKET,
)
