"""
S3-compatible bucket backup script.

Downloads the full contents of an S3-compatible bucket to a local directory,
organized by date (YYYY/MM/DD/NN).

Required environment variables:
  S3_BUCKET_NAME         Name of the bucket to download.
  S3_ACCESS_KEY_ID       Access key for authentication.
  S3_SECRET_ACCESS_KEY   Secret key for authentication.
  S3_ENDPOINT_URL        Endpoint URL for the S3-compatible service (e.g. MinIO, cloudscale).

Optional environment variables:
  BACKUP_DIR             Directory where backups are stored (default: ./backup).
  UPTIME_KUMA_PUSH_URL   Push URL for an Uptime Kuma push monitor. If set, a push is sent
                         on success (status=up, ping=elapsed ms) and on failure (status=down).
"""

import os
import sys
import time
import urllib.parse
import urllib.request
import boto3
from botocore.exceptions import NoCredentialsError
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path


def push_uptime_kuma(push_url, status, msg, ping):
    params = urllib.parse.urlencode({"status": status, "msg": msg, "ping": int(ping)})
    try:
        urllib.request.urlopen(f"{push_url}?{params}", timeout=10)
    except Exception as e:
        print(f"Uptime Kuma push failed: {e}")


def download_s3_bucket(bucket_name, backup_dir, access_key, secret_key, endpoint_url=None, push_url=None):
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    date_path = datetime.today().strftime("%Y/%m/%d")
    base_backup_dir = Path(backup_dir) / date_path
    backup_path = base_backup_dir / "01"
    counter = 1

    while backup_path.exists():
        counter += 1
        backup_path = base_backup_dir / f"{counter:02}"

    print(f"Downloading S3 bucket '{bucket_name}' to: {backup_path}")

    start = time.monotonic()
    try:
        paginator = s3.get_paginator("list_objects_v2")
        objects = [
            obj
            for page in paginator.paginate(Bucket=bucket_name)
            for obj in page.get("Contents", [])
        ]

        if not objects:
            print("Bucket is empty, nothing to download.")
            return

        backup_path.mkdir(parents=True, exist_ok=True)

        def download_one(obj):
            file_path = backup_path / obj["Key"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Downloading {obj['Key']}")
            s3.download_file(Bucket=bucket_name, Key=obj["Key"], Filename=str(file_path))

        with ThreadPoolExecutor() as executor:
            for future in as_completed(executor.submit(download_one, obj) for obj in objects):
                future.result()

        elapsed_ms = (time.monotonic() - start) * 1000
        print("Download completed successfully.")
        if push_url:
            push_uptime_kuma(push_url, "up", "OK", elapsed_ms)

    except NoCredentialsError as e:
        if push_url:
            push_uptime_kuma(push_url, "down", "S3 credentials not found or invalid.", 0)
        print("S3 credentials not found or invalid.")
        sys.exit(1)
    except Exception as e:
        if push_url:
            push_uptime_kuma(push_url, "down", str(e), 0)
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    backup_directory = os.getenv("BACKUP_DIR", "./backup")
    s3_bucket = os.getenv("S3_BUCKET_NAME")
    access_key = os.getenv("S3_ACCESS_KEY_ID")
    secret_key = os.getenv("S3_SECRET_ACCESS_KEY")
    endpoint_url = os.getenv("S3_ENDPOINT_URL")
    push_url = os.getenv("UPTIME_KUMA_PUSH_URL")

    missing = [name for name, val in [
        ("S3_BUCKET_NAME", s3_bucket),
        ("S3_ACCESS_KEY_ID", access_key),
        ("S3_SECRET_ACCESS_KEY", secret_key),
    ] if not val]

    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    download_s3_bucket(s3_bucket, backup_directory, access_key, secret_key, endpoint_url, push_url)
