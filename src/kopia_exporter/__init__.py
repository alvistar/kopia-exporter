import json
import click
import subprocess
import logging
from typing import Dict, List

import time

from kopia_exporter.metrics import Metrics

# Configuring logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


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


@click.group()
def main():
    pass


@main.command()
@click.option("--port", default=8123, help="The port to listen on.")
@click.option(
    "--config-file", default="", help="The kopia config file to use.", type=click.Path()
)
def server(port, config_file):
    """Run in server mode.

    This will run th exporter in server mode and will pull data from kopia repository
    """
    # Start the HTTP server to expose metrics
    logging.info(f"Listening on port {port}")

    metrics = Metrics()
    metrics.start_http_server(port)

    while True:
        data = refresh_data(config_file)
        for entry in data:
            metrics.update_metrics(entry)

        # Sleep for a bit before the next update (simulate periodic updates)
        time.sleep(600)


@main.command()
@click.argument("path", type=click.Path())
@click.option("--zfs", "-z", help="Zfs snapshot to create.")
@click.option("--override-source", "-o", help="Override source path", type=click.Path())
def snapshot(path: str, zfs: str, override_source: str):
    """Create a kopia snapshot.

    This will run kopia snapshot and send metrics to prometheus pushgateway
    :return:
    """

    if zfs:
        click.echo(f"Creating zfs snapshot {zfs}...")
        command = f"zfs snapshot {zfs}"
        result = subprocess.run(command, shell=True, capture_output=True)

        if result.returncode != 0:
            click.echo(
                f"Failed to create zfs snapshot: {result.stderr.decode('utf-8')}",
                err=True,
            )
            exit(1)

    click.echo("Creating kopia snapshot...")
    command = "kopia snapshot create --json"

    if override_source:
        command += f" --override-source {override_source}"

    command += f" {path}"

    result = subprocess.run(command, shell=True, capture_output=True)

    # Decode the output from bytes to string
    output = result.stdout.decode("utf-8")
    error = result.stderr.decode("utf-8")

    if result.returncode != 0:
        click.echo(f"Failed to create snapshot: {error}", err=True)
        exit(1)

    click.echo("Finished creating kopia snapshot")

    if zfs:
        click.echo(f"Destroying zfs snapshot {zfs}...")
        command = f"zfs destroy {zfs}"
        result = subprocess.run(command, shell=True, capture_output=True)

        if result.returncode != 0:
            click.echo(
                f"Failed to destroy zfs snapshot: {result.stderr.decode('utf-8')}",
                err=True,
            )

    # Load the string as a JSON object
    try:
        json_output = json.loads(output)
    except json.JSONDecodeError as e:
        click.echo(f"Failed to decode JSON: {e}", err=True)
        click.echo(f"Output was: {error}", err=True)
        exit(1)

    metrics = Metrics(default_registry=False)
    metrics.update_and_push(
        json_output, "pushgateway.cluster.thealvistar.com", "kopia-gw"
    )

    click.echo("Pushed metrics to pushgateway")
