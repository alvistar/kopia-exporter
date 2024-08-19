import json
import click
import subprocess
import logging
from typing import Dict, List

from prometheus_client import Gauge, start_http_server
from datetime import datetime, timezone
import time

# Configuring logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def to_struct_time(ts: str) -> datetime:
    d = datetime.strptime(ts[:-4], "%Y-%m-%dT%H:%M:%S.%f")
    return d.replace(tzinfo=timezone.utc)


def refresh_data(config_file: str) -> List[Dict[str, any]]:
    command = "kopia snapshot list -n 1 --json"

    if config_file:
        command += f" --config-file {config_file}"

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
    ["host", "path", "user"],
)
file_count_gauge = Gauge(
    "backup_file_count",
    "Total number of files in the backup",
    ["host", "path", "user"],
)
dir_count_gauge = Gauge(
    "backup_dir_count",
    "Total number of directories in the backup",
    ["host", "path", "user"],
)
error_count_gauge = Gauge(
    "backup_error_count",
    "Total number of errors encountered during the backup",
    ["host", "path", "user"],
)
backup_duration_gauge = Gauge(
    "backup_duration_seconds",
    "Duration of the backup in seconds",
    ["host", "path", "user"],
)
backup_start_time_gauge = Gauge(
    "backup_start_time",
    "Backup start time as unix timestamp",
    ["host", "path", "user"],
)
backup_end_time_gauge = Gauge(
    "backup_end_time",
    "Backup end time as unix timestamp",
    ["host", "path", "user"],
)

# Example JSON data
# data = [
#     {
#         "id": "618f83d08a9938351e8d385a24aca252",
#         "source": {
#             "host": "freenas",
#             "userName": "root",
#             "path": "/mnt/fsrevolution/media/pictures",
#         },
#         "description": "",
#         "startTime": "2023-10-05T09:01:36.265095891Z",
#         "endTime": "2023-10-05T09:01:55.028680144Z",
#         "stats": {
#             "totalSize": 162291781350,
#             "excludedTotalSize": 0,
#             "fileCount": 8054,
#             "cachedFiles": 42506,
#             "nonCachedFiles": 8054,
#             "dirCount": 221,
#             "excludedFileCount": 0,
#             "excludedDirCount": 0,
#             "ignoredErrorCount": 0,
#             "errorCount": 0,
#         },
#         "rootEntry": {
#             "name": "pictures",
#             "type": "d",
#             "mode": "0775",
#             "mtime": "2023-10-05T07:01:44.583769857Z",
#             "obj": "kd4656c46f03377cbc01c2a7843f28b44",
#             "summ": {
#                 "size": 162291781350,
#                 "files": 50560,
#                 "symlinks": 0,
#                 "dirs": 221,
#                 "maxTime": "2023-10-05T07:01:18.627015144Z",
#                 "numFailed": 0,
#             },
#         },
#         "retentionReason": [
#             "latest-1",
#             "hourly-1",
#             "daily-1",
#             "weekly-1",
#             "monthly-1",
#             "annual-1",
#         ],
#     }
#     # Add other JSON objects here
# ]


@click.command()
@click.option("--port", default=8123, help="The port to listen on.")
@click.option(
    "--config-file", default="", help="The kopia config file to use.", type=click.Path()
)
def main(port, config_file):
    # Start the HTTP server to expose metrics
    logging.info(f"Listening on port {port}")
    start_http_server(port)

    while True:
        data = refresh_data(config_file)
        for entry in data:
            # Extract data
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
            total_size_gauge.labels(host=host, path=path, user=user).set(total_size)
            file_count_gauge.labels(host=host, path=path, user=user).set(file_count)
            dir_count_gauge.labels(host=host, path=path, user=user).set(dir_count)
            error_count_gauge.labels(host=host, path=path, user=user).set(error_count)
            backup_duration_gauge.labels(host=host, path=path, user=user).set(duration)
            backup_start_time_gauge.labels(host=host, path=path, user=user).set(
                start_time.timestamp()
            )
            backup_end_time_gauge.labels(host=host, path=path, user=user).set(
                end_time.timestamp()
            )

        # Sleep for a bit before the next update (simulate periodic updates)
        time.sleep(600)
