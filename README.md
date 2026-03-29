![Build Status](https://github.com/jory3/s3backup/actions/workflows/build.yml/badge.svg)

# S3 Backup Script

## Purpose

This script backs up the contents of an S3-compatible bucket to a local directory. It maintains a local mirror and creates dated snapshots using hardlinks, so only changed files are downloaded on each run.

It is packaged as a Docker image for easy deployment.

---

## Features

- Works with any S3-compatible storage provider (DigitalOcean Spaces, Wasabi, cloudscale, Infomaniak, and others)
- Incremental sync — only changed files are downloaded, reducing egress costs
- Hardlink-based snapshots — unchanged files take no additional disk space
- Concurrent downloads for faster backups
- Configurable via environment variables
- Optional [Uptime Kuma](https://uptime.kuma.pet) push monitor integration

---

## Environment Variables

| Variable                | Description                                                              | Required | Example                                  |
|-------------------------|--------------------------------------------------------------------------|----------|------------------------------------------|
| `S3_BUCKET_NAME`        | Name of the bucket to back up.                                           | Yes      | `my-example-bucket`                      |
| `S3_ACCESS_KEY_ID`      | Access key for authentication.                                           | Yes      | `your-access-key-id`                     |
| `S3_SECRET_ACCESS_KEY`  | Secret key for authentication.                                           | Yes      | `your-secret-access-key`                 |
| `S3_ENDPOINT_URL`       | Endpoint URL of the S3-compatible service.                               | Yes      | `https://nyc3.digitaloceanspaces.com`    |
| `BACKUP_DIR`            | Directory inside the container where backups are stored. Default: `/backups`. | No  | `/backups`                               |
| `UPTIME_KUMA_PUSH_URL`  | Push URL of an Uptime Kuma push monitor. If set, a push is sent on success and on failure. | No | `https://your-kuma/api/push/xxxxxxxxxx` |
| `BACKUP_SCHEDULE`       | Cron expression controlling how often the backup runs. Default: `0 2 * * *` (daily at 02:00). | No | `0 2 * * *` |

---

## Running the Docker Image

### Using the pre-built image

```bash
docker run --rm \
  -e S3_BUCKET_NAME=my-bucket \
  -e S3_ACCESS_KEY_ID=your-access-key-id \
  -e S3_SECRET_ACCESS_KEY=your-secret-access-key \
  -e S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com \
  -v /path/to/local/backup:/backups \
  ghcr.io/jory3/s3backup
```

### Building the image yourself

```bash
docker build -t s3-backup-app .
```

```bash
docker run --rm \
  -e S3_BUCKET_NAME=my-bucket \
  -e S3_ACCESS_KEY_ID=your-access-key-id \
  -e S3_SECRET_ACCESS_KEY=your-secret-access-key \
  -e S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com \
  -v /path/to/local/backup:/backups \
  s3-backup-app
```

---

## Docker Compose

A `docker-compose.yml` is included. Adjust the values and run:

```bash
docker compose up -d
```

The container will start and run the backup on the configured schedule. Logs are available via `docker compose logs -f`.

---

## Using a `.env` File

Instead of passing variables inline, you can use a `.env` file:

```env
S3_BUCKET_NAME=my-example-bucket
S3_ACCESS_KEY_ID=your-access-key-id
S3_SECRET_ACCESS_KEY=your-secret-access-key
S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
BACKUP_DIR=/backups
# UPTIME_KUMA_PUSH_URL=https://your-kuma/api/push/xxxxxxxxxx
```

```bash
docker run --rm \
  --env-file .env \
  -v /path/to/local/backup:/backups \
  ghcr.io/jory3/s3backup
```

Using a `.env` file keeps credentials out of your shell history and makes configuration reusable.

---

## Development Setup

```bash
pip install -r requirements.txt

export S3_BUCKET_NAME=my-example-bucket
export S3_ACCESS_KEY_ID=your-access-key-id
export S3_SECRET_ACCESS_KEY=your-secret-access-key
export S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
export BACKUP_DIR=./backup  # optional

python backup-script.py
```

---

## Backup Structure

```
BACKUP_DIR/
  main/               # local mirror of the S3 bucket (always up to date)
  2026/03/29/01/      # snapshot — hardlinks to main/ for unchanged files
  2026/03/30/01/      # next day's snapshot
```

`main/` is synced with S3 on each run (only new/changed files downloaded, deleted files removed). A dated snapshot is then created using hardlinks. If `main/` is deleted, existing snapshots remain intact — hardlinks are independent references to the same data.

Snapshots are organized as `BACKUP_DIR/YYYY/MM/DD/NN/`, where `NN` increments if multiple runs happen on the same day.

---

## License

This project is licensed under the [MIT License](LICENSE).
