import os
import boto3
from botocore.exceptions import NoCredentialsError
from datetime import datetime
from pathlib import Path


def get_env_variable(key, default=None):
    """
    Helper function to get an environment variable, or return a default value.
    """
    return os.getenv(key, default)


def download_s3_bucket(bucket_name, backup_dir, endpoint_url=None):
    """
    Download the contents of an S3-compatible bucket to a specified local directory.

    Args:
        bucket_name (str): The name of the S3-compatible bucket.
        backup_dir (str): The local directory to save bucket contents.
        endpoint_url (str): The URL for the S3-compatible service (default: None for AWS S3).
    """
    # Configure the S3 client with a custom endpoint if provided
    s3 = boto3.client("s3", endpoint_url=endpoint_url)

    today = datetime.today()
    date_path = today.strftime(f"%Y/%m/%d")

    # Prepare backup directory with dynamic subdirectories
    base_backup_dir = Path(backup_dir).joinpath(date_path)
    backup_dir = base_backup_dir / "01"
    counter = 1

    # Ensure uniqueness of backup directory
    while backup_dir.exists():
        counter += 1
        backup_dir = base_backup_dir / f"{counter:02}"

    backup_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading S3 bucket '{bucket_name}' to local directory: {backup_dir}")
    try:
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)

        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    file_path = Path(backup_dir) / obj['Key']
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    print(f"Downloading {obj['Key']} to {file_path}")
                    s3.download_file(Bucket=bucket_name, Key=obj['Key'], Filename=str(file_path))
        print("Download completed successfully.")
    except NoCredentialsError:
        print("S3 credentials not found. Please configure them.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    """
    Required Environment Variables:
    --------------------------------
    1. **BACKUP_DIR**:
       - Directory where the backups will be stored.
       - Default: './backup'
       - Example: '/var/backups'

    2. **S3_BUCKET_NAME**:
       - Name of the S3-compatible bucket to download.
       - Example: 'my-example-bucket'

    3. **S3_ACCESS_KEY_ID**:
       - Access Key for authenticating with the S3-compatible service.
       - Example: 'your-access-key-id'

    4. **S3_SECRET_ACCESS_KEY**:
       - Secret Key for authenticating with the S3-compatible service.
       - Example: 'your-secret-access-key'

    5. **S3_ENDPOINT_URL** (Optional):
       - Endpoint URL for the S3-compatible service (e.g., MinIO, DigitalOcean Spaces).
       - Default: None (uses AWS S3 endpoints).
       - Example: 'https://nyc3.digitaloceanspaces.com' or 'http://localhost:9000' for MinIO.
    """
    # Get environment variables with default values
    backup_directory = get_env_variable("BACKUP_DIR", "./backup")
    s3_bucket = get_env_variable("S3_BUCKET_NAME", "bucket")
    endpoint_url = get_env_variable("S3_ENDPOINT_URL", "https://objects.lpg.cloudscale.ch")

    # Configure access credentials for generic S3-compatible services
    os.environ.setdefault("AWS_ACCESS_KEY_ID", get_env_variable("S3_ACCESS_KEY_ID", ""))
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", get_env_variable("S3_SECRET_ACCESS_KEY", ""))

    # Call the backup function
    download_s3_bucket(s3_bucket, backup_directory, endpoint_url)