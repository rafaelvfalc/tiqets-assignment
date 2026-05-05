# tiqets-assignment

This repository implements the Tiqets assignment for aggregating barcodes and orders into a voucher-ready export.

## What it does

- Reads `orders.csv` and `barcodes.csv`
- Validates input data
  - Duplicate barcodes are logged and ignored
  - Orders with no barcodes are logged and omitted from the output
- Produces an aggregated CSV containing `customer_id`, `order_id`, and a JSON list of barcodes
- Prints the top 5 customers by ticket count to stdout
- Prints the number of unused barcodes to stdout

## Usage

From the project root:

```bash
uv run python main.py --orders orders.csv --barcodes barcodes.csv --output output.csv
```

If the package is installed, you can also use the provided script entry points:

```bash
ti4-aggregate --orders orders.csv --barcodes barcodes.csv --output output.csv
```

If you omit arguments, the defaults are:

- `orders.csv`
- `barcodes.csv`
- `orders_with_barcodes.csv`

## Output format

The output CSV includes a header row:

```csv
customer_id,order_id,barcodes
c1,o1,["b1","b2"]
```

## Architecture

- `main.py` provides a CLI wrapper around the package
- `tiqets_assignment/processor.py` contains parsing, validation, aggregation, and output logic
- `tests/test_processor.py` contains unit tests for behavior; `tests/test_integration.py` covers end-to-end CLI execution
- Row parsing is implemented with a streaming CSV iterator so data is processed line by line

## Complexity

- **Time complexity**: O(N + M) where N is the number of orders and M is the number of barcodes (linear in input size)
- **Space complexity**: O(N + K) where N is the number of valid orders and K is the number of assigned barcodes stored for aggregation
- Designed to handle large files via streaming; memory usage scales with number of unique orders and assigned barcodes, not file size

## Validation rules

- Duplicate barcode values are ignored and reported on stderr
- Any order without assigned barcodes is ignored in the generated output and reported on stderr
- Barcodes without an order assignment are counted as unused
- Barcodes referencing unknown orders are ignored and logged

## Testing

Install development dependencies and run tests:

```bash
uv sync --extra dev
```

Run all tests with:

```bash
uv run pytest
```

Run only unit tests:

```bash
uv run pytest tests/unit
```

Run only integration tests:

```bash
uv run pytest tests/integration
```

## Data model

See `DATA_MODEL.md` for the SQL-ready schema and relationship design.

## Deployment plan

See `DEPLOYMENT.md` for a production-ready deployment checklist and recommended runtime setup.
