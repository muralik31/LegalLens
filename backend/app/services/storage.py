from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

from app.config import settings


class StorageProvider(ABC):
    """Abstract base class for file storage providers."""

    @abstractmethod
    async def upload_file(self, file_content: bytes, filename: str, content_type: str) -> str:
        """Upload file and return storage path."""
        pass

    @abstractmethod
    async def download_file(self, storage_path: str) -> bytes:
        """Download file from storage."""
        pass

    @abstractmethod
    async def delete_file(self, storage_path: str) -> None:
        """Delete file from storage."""
        pass

    @abstractmethod
    async def get_file_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Get a temporary signed URL for file access."""
        pass


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider."""

    def __init__(self, base_path: str = "./uploads") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(self, file_content: bytes, filename: str, content_type: str) -> str:
        """Upload file to local filesystem."""
        # Create unique filename
        file_id = str(uuid4())
        ext = Path(filename).suffix
        storage_filename = f"{file_id}{ext}"

        # Create date-based subdirectory
        date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        full_dir = self.base_path / date_path
        full_dir.mkdir(parents=True, exist_ok=True)

        # Write file
        file_path = full_dir / storage_filename
        file_path.write_bytes(file_content)

        # Return relative path
        return f"{date_path}/{storage_filename}"

    async def download_file(self, storage_path: str) -> bytes:
        """Download file from local filesystem."""
        file_path = self.base_path / storage_path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        return file_path.read_bytes()

    async def delete_file(self, storage_path: str) -> None:
        """Delete file from local filesystem."""
        file_path = self.base_path / storage_path
        if file_path.exists():
            file_path.unlink()

    async def get_file_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Get file path (local storage doesn't use URLs)."""
        return str(self.base_path / storage_path)


class S3StorageProvider(StorageProvider):
    """AWS S3 / Cloudflare R2 storage provider."""

    def __init__(
        self,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
    ) -> None:
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            endpoint_url=endpoint_url,
        )

    async def upload_file(self, file_content: bytes, filename: str, content_type: str) -> str:
        """Upload file to S3/R2."""
        # Create unique key
        file_id = str(uuid4())
        ext = Path(filename).suffix
        date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        object_key = f"documents/{date_path}/{file_id}{ext}"

        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_content,
                ContentType=content_type,
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to upload to S3: {e}") from e

        return object_key

    async def download_file(self, storage_path: str) -> bytes:
        """Download file from S3/R2."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=storage_path)
            return response["Body"].read()
        except ClientError as e:
            raise FileNotFoundError(f"File not found in S3: {storage_path}") from e

    async def delete_file(self, storage_path: str) -> None:
        """Delete file from S3/R2."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=storage_path)
        except ClientError as e:
            # Ignore errors if file doesn't exist
            pass

    async def get_file_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for S3/R2 file."""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": storage_path},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            raise RuntimeError(f"Failed to generate presigned URL: {e}") from e


def get_storage_provider() -> StorageProvider:
    """Factory function to get the configured storage provider."""
    if settings.STORAGE_PROVIDER == "local":
        return LocalStorageProvider(settings.STORAGE_LOCAL_PATH)
    elif settings.STORAGE_PROVIDER in ("s3", "r2"):
        return S3StorageProvider(
            bucket_name=settings.S3_BUCKET_NAME,
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            region=settings.AWS_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL if settings.STORAGE_PROVIDER == "r2" else None,
        )
    else:
        raise ValueError(f"Unknown storage provider: {settings.STORAGE_PROVIDER}")


# Global storage instance
storage = get_storage_provider()
