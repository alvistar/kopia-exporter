import json
import subprocess
import logging
from typing import Dict, List

from prometheus_client import Gauge, start_http_server
from datetime import datetime
import time

# Configuring logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def to_struct_time(ts: str) -> datetime:
    return datetime.strptime(ts[:-4], "%Y-%m-%dT%H:%M:%S.%f")


def refresh_data() -> List[Dict[str, any]]:
    command = "kopia snapshot list -n 1 --json"

    logging.info(f"Running command: {command}")

    # Run the command and capture the output
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    logging.info("Finish refreshing data")

    # Decode the output from bytes to string
    output = result.stdout.decode("utf-8")
    error = result.stderr.decode("utf-8")

    # Load the string as a JSON object
    try:
        json_output = json.loads(output)
        return json_output
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON: {e}")
        logging.error(f"Output was: {error}")


# Define metrics
total_size_gauge = Gauge(
    "backup_total_size_bytes",
    "Total size of the backup in bytes",
    ["id", "host", "path", "user"],
)
file_count_gauge = Gauge(
    "backup_file_count",
    "Total number of files in the backup",
    ["id", "host", "path", "user"],
)
dir_count_gauge = Gauge(
    "backup_dir_count",
    "Total number of directories in the backup",
    ["id", "host", "path", "user"],
)
error_count_gauge = Gauge(
    "backup_error_count",
    "Total number of errors encountered during the backup",
    ["id", "host", "path", "user"],
)
backup_duration_gauge = Gauge(
    "backup_duration_seconds",
    "Duration of the backup in seconds",
    ["id", "host", "path", "user"],
)
backup_start_time_gauge = Gauge(
    "backup_start_time",
    "Backup start time as unix timestamp",
    ["id", "host", "path", "user"],
)
backup_end_time_gauge = Gauge(
    "backup_end_time",
    "Backup end time as unix timestamp",
    ["id", "host", "path", "user"],
)

# Example JSON data
# data = [
#     {
#         "id": "442e0838851792b7109075a92663191c",
#         "source": {
#             "host": "freenas",
#             "userName": "root",
#             "path": "/mnt/fsrevolution/k3vols/immich",
#         },
#         "description": "",
#         "startTime": "2024-08-19T05:17:21.202557011Z",
#         "endTime": "2024-08-19T05:17:58.528054855Z",
#         "stats": {
#             "totalSize": 429170451342,
#             "excludedTotalSize": 0,
#             "fileCount": 0,
#             "cachedFiles": 517743,
#             "nonCachedFiles": 0,
#             "dirCount": 108296,
#             "excludedFileCount": 0,
#             "excludedDirCount": 0,
#             "ignoredErrorCount": 0,
#             "errorCount": 0,
#         },
#     },
#     # Add other JSON objects here
# ]


def main():
    # Start the HTTP server to expose metrics
    start_http_server(8000)

    while True:
        data = refresh_data()
        for entry in data:
            # Extract data
            backup_id = entry["id"]
            host = entry["source"]["host"]
            path = entry["source"]["path"]
            user = entry["source"]["userName"]
            total_size = entry["stats"]["totalSize"]
            file_count = entry["stats"]["fileCount"]
            dir_count = entry["stats"]["dirCount"]
            error_count = entry["stats"]["errorCount"]

            # Calculate backup duration
            start_time = to_struct_time(entry["startTime"])
            end_time = to_struct_time(entry["endTime"])

            duration = (end_time - start_time).seconds

            # Update Prometheus metrics
            total_size_gauge.labels(id=backup_id, host=host, path=path, user=user).set(
                total_size
            )
            file_count_gauge.labels(id=backup_id, host=host, path=path, user=user).set(
                file_count
            )
            dir_count_gauge.labels(id=backup_id, host=host, path=path, user=user).set(
                dir_count
            )
            error_count_gauge.labels(id=backup_id, host=host, path=path, user=user).set(
                error_count
            )
            backup_duration_gauge.labels(
                id=backup_id, host=host, path=path, user=user
            ).set(duration)
            backup_start_time_gauge.labels(
                id=backup_id, host=host, path=path, user=user
            ).set(start_time.timestamp())
            backup_end_time_gauge.labels(
                id=backup_id, host=host, path=path, user=user
            ).set(end_time.timestamp())

        # Sleep for a bit before the next update (simulate periodic updates)
        time.sleep(600)
