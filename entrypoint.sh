#!/bin/sh
set -e

SCHEDULE="${BACKUP_SCHEDULE:-0 2 * * *}"

# Write all current env vars to a file cron can source, since cron runs with an empty environment
export -p > /etc/cron-env

# Write the crontab, redirecting output to PID 1's stdout/stderr so Docker captures it
echo "${SCHEDULE} . /etc/cron-env && cd /app && python backup-script.py >> /proc/1/fd/1 2>> /proc/1/fd/2" > /etc/cron.d/backup
chmod 0644 /etc/cron.d/backup
crontab /etc/cron.d/backup

echo "Backup scheduled with cron expression: ${SCHEDULE}"

exec cron -f
