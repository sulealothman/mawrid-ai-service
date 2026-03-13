from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass

import boto3


from app.core.config import settings

@dataclass(frozen=True)
class S3Ref:
    bucket: str
    key: str


class S3Fetcher:
    def __init__(self, *, region_name: str | None = None):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.AWS_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION,
        )

    def download_to_tmp(self, ref: S3Ref) -> str:
        base = os.path.basename(ref.key) or "file"
        fd, path = tempfile.mkstemp(prefix="ingest_", suffix=f"_{base}")
        os.close(fd)

        self.s3.download_file(ref.bucket, ref.key, path)
        return path
