# Deployment Plan

## Goal

Deploy the barcode-order aggregation script as a reliable Python utility for production use.

## Runtime requirements

- Python 3.14+ installed
- CSV input files available in the expected format

## Installation

1. Clone the repository
2. Install dependencies with uv

```bash
uv sync --extra dev
```

## Execution

```bash
uv run python main.py --orders path/to/orders.csv --barcodes path/to/barcodes.csv --output path/to/output.csv
```

## Testing

```bash
uv run pytest
```

## Production considerations

- Wrap the script with a process manager if run on a schedule
- Validate input file freshness and file permissions before execution
- Store output in a reproducible target location
- Collect stderr logs during execution for validation failures
- Use a CI pipeline to run `pytest` on every change

## Docker deployment

1. Build the container image from the repository root:

```bash
docker build -t tiqets-aggregation:latest .
```

2. Run the container with mounted input and output volumes:

```bash
docker run --rm \
  -v "$PWD:/app" \
  tiqets-aggregation:latest \
  --orders data/orders.csv \
  --barcodes data/barcodes.csv \
  --output data/output.csv
```

3. Alternatively, run the packaged entrypoint directly with custom arguments:

```bash
docker run --rm -v "$PWD:/app" tiqets-aggregation:latest --help
```

### Docker notes

- The container image uses Python 3.14 slim and installs the package from source.
- Input files should be mounted into `/app` or copied into the image for batch jobs.
- Use CI to build and validate the image before deploying to production.

## Kubernetes deployment strategy

1. Build and push the Docker image to your container registry:

```bash
docker build -t my-registry/tiqets-aggregation:latest .
docker push my-registry/tiqets-aggregation:latest
```

2. Create a Kubernetes ConfigMap or Secret for runtime configuration if needed.

3. Define a `Job` or `CronJob` for data processing:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: tiqets-aggregation-job
spec:
  template:
    spec:
      containers:
      - name: tiqets-aggregation
        image: my-registry/tiqets-aggregation:latest
        command: ["python", "main.py"]
        args: ["--orders", "/data/orders.csv", "--barcodes", "/data/barcodes.csv", "--output", "/data/output.csv"]
        volumeMounts:
        - name: data-volume
          mountPath: /data
      restartPolicy: Never
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: tiqets-data-pvc
```

4. Use a `CronJob` if the aggregation should run on a schedule.

5. Store input and output data on a shared PersistentVolume or object storage bucket mounted via CSI drivers.

6. Monitor job execution and capture logs. Ensure failed runs are retried or alerted.

7. Use a CI/CD pipeline to deploy the Kubernetes manifest and validate the image before promotion.
