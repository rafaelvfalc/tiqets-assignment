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
