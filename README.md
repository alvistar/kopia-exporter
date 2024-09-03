# kopia-exporter

Kopia Exporter for Prometheus

## Description

kopia-exporter is a tool that exports metrics from Kopia backups to Prometheus. It can run in server mode to continuously update metrics or in snapshot mode to create backups and push metrics to a Prometheus Pushgateway.

## Installation

1. Ensure you have Python 3.7+ installed on your system.

2. Clone the repository:
   ```
   git clone https://github.com/yourusername/kopia-exporter.git
   cd kopia-exporter
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

kopia-exporter can be used in two modes: server mode and snapshot mode.

### Server Mode

In server mode, kopia-exporter continuously updates metrics and exposes them via an HTTP server.

```
python -m kopia_exporter server [OPTIONS]
```

Options:
- `--port INTEGER`: The port to listen on (default: 8123)
- `--config-file FILE`: The Kopia config file to use
- `--refresh-interval INTEGER`: Refresh interval in seconds (default: 600)

Example:
```
python -m kopia_exporter server --port 8080 --config-file /path/to/kopia.config --refresh-interval 300
```

### Snapshot Mode

In snapshot mode, kopia-exporter creates a Kopia snapshot and pushes metrics to a Prometheus Pushgateway.

```
python -m kopia_exporter snapshot [OPTIONS] PATH
```

Options:
- `--zfs, -z TEXT`: ZFS snapshot to create
- `--override-source, -o PATH`: Override source path
- `--job TEXT`: Job name for the Pushgateway
- `--pushgateway TEXT`: Pushgateway host URL
- `--conf FILE`: Path to the YAML configuration file

Example:
```
python -m kopia_exporter snapshot /path/to/backup --zfs tank/data@snapshot1 --job kopia-backup --pushgateway http://pushgateway:9091
```

## Configuration

You can use a YAML configuration file to set default values for the Pushgateway URL and job name. Create a file named `config.yaml` with the following content:

```yaml
pushgateway: "http://pushgateway:9091"
job: "kopia-backup"
```

Then use the `--conf` option to specify the configuration file:

```
python -m kopia_exporter --conf config.yaml snapshot /path/to/backup
```

## Metrics

kopia-exporter exports[metrics.py](src%2Fkopia_exporter%2Fmetrics.py) the following metrics:

- `total_size`: Total size of the backup
- `file_count`: Number of files in the backup
- `dir_count`: Number of directories in the backup
- `error_count`: Number of errors in the backup
- `backup_duration`: Duration of the backup in seconds
- `backup_start_time`: Start time of the backup (Unix timestamp)
- `backup_end_time`: End time of the backup (Unix timestamp)

These metrics are labeled with `host`, `path`, and `user` to identify the source of the backup.

## Requirements

- Python 3.7+
- Kopia backup tool installed and configured
- Prometheus server (for server mode)
- Prometheus Pushgateway (for snapshot mode)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
