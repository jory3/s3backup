"""
S3-compatible bucket backup script.

Maintains a local mirror of the S3 bucket ("main") and creates dated snapshots
using hardlinks, so only changed files are downloaded on each run.

Snapshot layout: <BACKUP_DIR>/<YYYY>/<MM>/<DD>/<NN>/
Mirror layout:   <BACKUP_DIR>/main/

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

import json
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

ETAGS_FILE = ".s3_etags.json"


def push_uptime_kuma(push_url, status, msg, ping):
    base_url = push_url.split("?")[0]
    params = urllib.parse.urlencode({"status": status, "msg": msg, "ping": int(ping)})
    url = f"{base_url}?{params}"
    try:
        urllib.request.urlopen(url, timeout=10)
        print(f"Uptime Kuma push succeeded: {url}")
    except Exception as e:
        print(f"Uptime Kuma push failed: {e}")


def sync_main(s3, bucket_name, main_dir, objects):
    """Sync S3 objects to main_dir, downloading only new/changed files."""
    main_dir.mkdir(parents=True, exist_ok=True)

    etags_path = main_dir / ETAGS_FILE
    local_etags = json.loads(etags_path.read_text()) if etags_path.exists() else {}
    s3_keys = {obj["Key"] for obj in objects}
    s3_etags = {obj["Key"]: obj["ETag"].strip('"') for obj in objects}

    # Remove local files that were deleted from S3
    for file_path in main_dir.rglob("*"):
        if file_path.is_file() and file_path.name != ETAGS_FILE:
            key = str(file_path.relative_to(main_dir))
            if key not in s3_keys:
                print(f"Removing deleted: {key}")
                file_path.unlink()

    # Download new/changed files
    def sync_one(obj):
        key = obj["Key"]
        etag = s3_etags[key]
        file_path = main_dir / key
        if file_path.exists() and local_etags.get(key) == etag:
            return key, etag  # unchanged, skip
        file_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {key}")
        s3.download_file(Bucket=bucket_name, Key=key, Filename=str(file_path))
        return key, etag

    new_etags = {}
    with ThreadPoolExecutor() as executor:
        for future in as_completed(executor.submit(sync_one, obj) for obj in objects):
            key, etag = future.result()
            new_etags[key] = etag

    etags_path.write_text(json.dumps(new_etags, indent=2))


def create_snapshot(main_dir, snapshot_dir):
    """Create a snapshot of main_dir in snapshot_dir using hardlinks."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for src in main_dir.rglob("*"):
        if src.is_file() and src.name != ETAGS_FILE:
            rel = src.relative_to(main_dir)
            dst = snapshot_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.link(src, dst)


def run_backup(bucket_name, backup_dir, access_key, secret_key, endpoint_url=None, push_url=None):
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    backup_dir = Path(backup_dir)
    main_dir = backup_dir / "main"

    date_path = datetime.today().strftime("%Y/%m/%d")
    base_snapshot_dir = backup_dir / date_path
    snapshot_path = base_snapshot_dir / "01"
    counter = 1
    while snapshot_path.exists():
        counter += 1
        snapshot_path = base_snapshot_dir / f"{counter:02}"

    print(f"Syncing S3 bucket '{bucket_name}' to mirror: {main_dir}")

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

        sync_main(s3, bucket_name, main_dir, objects)

        print(f"Creating snapshot: {snapshot_path}")
        create_snapshot(main_dir, snapshot_path)

        elapsed_ms = (time.monotonic() - start) * 1000
        print("Backup completed successfully.")
        if push_url:
            push_uptime_kuma(push_url, "up", "OK", elapsed_ms)

    except NoCredentialsError:
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

    run_backup(s3_bucket, backup_directory, access_key, secret_key, endpoint_url, push_url)
