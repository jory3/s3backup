   ![Build Status](https://github.com/jory3/s3backup/actions/workflows/build.yml/badge.svg)

# S3 Backup Script

## Purpose

This script is designed to download the contents of an S3-compatible bucket (including AWS S3, MinIO, DigitalOcean Spaces, Wasabi, or others) and store them in a local directory. It supports both AWS S3 and generic S3-compatible services with custom endpoint URLs, making it a flexible solution for backing up your cloud storage.

The script ensures backups are organized by date and uses a unique subdirectory for each run (e.g., `2023/11/01/01`). It is packaged within a Docker image for easy portability and execution.

---

## Features

- Compatible with **AWS S3** and **S3-compatible services** like:
    - [MinIO](https://min.io)
    - [DigitalOcean Spaces](https://www.digitalocean.com/products/spaces)
    - [Wasabi](https://wasabi.com)
    - Other S3-compatible storage providers
- Environmental variables allow easy configuration of:
    - Bucket name
    - Access credentials (Access Key & Secret Key)
    - Endpoint URL for S3-compatible providers
    - Backup directory
- Dockerized for consistent runtime and easy deployment.

---

## Environment Variables

The script is configured using environment variables. Here's what you need to set:

| Variable Name          | Description                                                                 | Required | Example Values                               |
|------------------------|-----------------------------------------------------------------------------|----------|---------------------------------------------|
| `BACKUP_DIR`            | The directory inside the container where backups will be stored. Defaults to `/backups`. | No       | `/backups`                                  |
| `S3_BUCKET_NAME`        | The name of the S3-compatible bucket to download.                          | Yes      | `my-example-bucket`                         |
| `S3_ACCESS_KEY_ID`      | The Access Key for authenticating with the S3-compatible service.          | Yes      | `your-access-key-id`                        |
| `S3_SECRET_ACCESS_KEY`  | The Secret Key for authenticating with the S3-compatible service.          | Yes      | `your-secret-access-key`                    |
| `S3_ENDPOINT_URL`       | The custom endpoint URL for the S3-compatible service. Use AWS-compatible defaults if absent. | No       | `https://nyc3.digitaloceanspaces.com` (for DigitalOcean Spaces) |

---

## Running the Docker Image

To run the Docker container, you need to pass the required environment variables and specify a volume to store the backup files.

### Step-by-Step Instructions

1. **Build the Docker Image**:
   If you haven't already built the image, you can build it using:
   ```bash
   docker build -t s3-backup-app .
   ```

2. **Run the Docker Container**:
   To run the container, use the following command:

   ```bash
   docker run --rm \
     -e BACKUP_DIR=/backups \
     -e S3_BUCKET_NAME=my-bucket \
     -e S3_ACCESS_KEY_ID=your-access-key-id \
     -e S3_SECRET_ACCESS_KEY=your-secret-access-key \
     -e S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com \
     -v /path/to/your/local/backup:/backups \
     s3-backup-app
   ```

#### Breakdown of the Command:
- `--rm`: Automatically removes the container after it stops.
- `-e BACKUP_DIR=/backups`: Specifies the backup directory inside the container.
- `-e S3_BUCKET_NAME=my-bucket`: Sets the name of the bucket to back up.
- `-e S3_ACCESS_KEY_ID` & `-e S3_SECRET_ACCESS_KEY`: Provide your S3-compatible access credentials.
- `-e S3_ENDPOINT_URL`: (Optional) Endpoint URL for non-AWS S3 services (e.g., MinIO, DigitalOcean Spaces). Leave this empty for AWS S3.
- `-v /path/to/your/local/backup:/backups`: Maps the container's backup directory `/backups` to a local directory on your system (`/path/to/your/local/backup` allows you to see your backups after the container stops).
- `s3-backup-app`: Name of the Docker image to run.

3. **Post-execution**:
   After the script runs, the backup files will be saved in the local directory you specified, for example, `/path/to/your/local/backup`.

---

## Using a `.env` File

Instead of passing environment variables directly in the `docker run` command, you can use a `.env` file to simplify the configuration process. Here's how you can do it:

### Step-by-Step Instructions

1. **Create a `.env` File**:
    - Save the following template as a file named `.env` in the same directory where you will run the Docker container:
      ```env
      BACKUP_DIR=/backups
      S3_BUCKET_NAME=my-example-bucket
      S3_ACCESS_KEY_ID=your-access-key-id
      S3_SECRET_ACCESS_KEY=your-secret-access-key
      S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
      ```

2. **Modify the Values**:
    - Replace the placeholders (`your-access-key-id`, `your-secret-access-key`, etc.) with your actual credentials and settings.

3. **Run the Docker Container with the `.env` File**:
    - You can pass the `.env` file to the container using the `--env-file` option:
      ```bash
      docker run --rm \
        --env-file .env \
        -v /path/to/your/local/backup:/backups \
        s3-backup-app
      ```

### Benefits of Using `.env`:
- **Secure**: Prevents sensitive credentials (like keys) from appearing in logs or command history.
- **Reusable**: Makes it easy to update and reuse the configuration without modifying your `docker run` command every time.
- **Organized**: Keeps your configuration neat and easy to manage.

---

## Examples

### Run with AWS S3:
```bash
docker run --rm \
  -e BACKUP_DIR=/backups \
  -e S3_BUCKET_NAME=my-aws-bucket \
  -e S3_ACCESS_KEY_ID=AWS_ACCESS_KEY_HERE \
  -e S3_SECRET_ACCESS_KEY=AWS_SECRET_KEY_HERE \
  -v /local/backup:/backups \
  s3-backup-app
```

### Run with DigitalOcean Spaces:
```bash
docker run --rm \
  -e BACKUP_DIR=/backups \
  -e S3_BUCKET_NAME=my-digitalocean-space \
  -e S3_ACCESS_KEY_ID=DO_ACCESS_KEY_HERE \
  -e S3_SECRET_ACCESS_KEY=DO_SECRET_KEY_HERE \
  -e S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com \
  -v /local/backup:/backups \
  s3-backup-app
```

### Run with MinIO (Local Storage):
```bash
docker run --rm \
  -e BACKUP_DIR=/backups \
  -e S3_BUCKET_NAME=minio-bucket \
  -e S3_ACCESS_KEY_ID=minio-access-key \
  -e S3_SECRET_ACCESS_KEY=minio-secret-key \
  -e S3_ENDPOINT_URL=http://localhost:9000 \
  -v /local/backup:/backups \
  s3-backup-app
```

---

## Development Setup

If you'd like to run the script locally without Docker, you can do so by following these steps:

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Script**:
   ```bash
   export BACKUP_DIR=./backup
   export S3_BUCKET_NAME=my-example-bucket
   export S3_ACCESS_KEY_ID=your-access-key-id
   export S3_SECRET_ACCESS_KEY=your-secret-access-key
   export S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com  # Optional
   python backup_script.py
   ```

---

## Folder Structure of Backups

When the backup runs successfully, the files will be downloaded into the specified `BACKUP_DIR`, organized with the following structure:

## License

This project is licensed under the [MIT License](LICENSE). Please refer to the LICENSE file for more details.