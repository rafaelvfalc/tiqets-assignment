import csv
import json
import subprocess
import sys
from pathlib import Path


def write_csv(path: Path, header, rows):
    """Write test CSV data to file."""
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def test_end_to_end_cli(tmp_path):
    """Test end-to-end CLI execution with sample data."""
    project_root = Path(__file__).resolve().parents[2]
    orders_csv = tmp_path / "orders.csv"
    barcodes_csv = tmp_path / "barcodes.csv"
    output_csv = tmp_path / "output.csv"

    write_csv(
        orders_csv,
        ["order_id", "customer_id"],
        [["o1", "c1"], ["o2", "c2"], ["o3", "c1"]],
    )
    write_csv(
        barcodes_csv,
        ["barcode", "order_id"],
        [["b1", "o1"], ["b2", "o1"], ["b3", "o2"], ["b4", ""], ["b5", "o3"]],
    )

    result = subprocess.run(
        [sys.executable, str(project_root / "main.py"),
         "--orders", str(orders_csv),
         "--barcodes", str(barcodes_csv),
         "--output", str(output_csv)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Top 5 customers" in result.stdout
    assert "Unused barcodes: 1" in result.stdout

    with output_csv.open("r", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)

    assert len(rows) == 3
    assert json.loads(rows[0]["barcodes"]) == ["b1", "b2"]
    assert json.loads(rows[1]["barcodes"]) == ["b3"]
    assert json.loads(rows[2]["barcodes"]) == ["b5"]


def test_cli_with_missing_orders_file(tmp_path):
    """Test CLI exits with error when orders file is missing."""
    project_root = Path(__file__).resolve().parents[2]
    barcodes_csv = tmp_path / "barcodes.csv"
    output_csv = tmp_path / "output.csv"

    write_csv(barcodes_csv, ["barcode", "order_id"], [["b1", "o1"]])

    result = subprocess.run(
        [sys.executable, str(project_root / "main.py"),
         "--orders", str(tmp_path / "missing.csv"),
         "--barcodes", str(barcodes_csv),
         "--output", str(output_csv)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Input file does not exist" in result.stderr


def test_cli_with_invalid_csv_header(tmp_path):
    """Test CLI exits with error on invalid CSV header."""
    project_root = Path(__file__).resolve().parents[2]
    orders_csv = tmp_path / "orders.csv"
    barcodes_csv = tmp_path / "barcodes.csv"
    output_csv = tmp_path / "output.csv"

    # Wrong header for orders
    write_csv(orders_csv, ["wrong", "header"], [["o1", "c1"]])
    write_csv(barcodes_csv, ["barcode", "order_id"], [["b1", "o1"]])

    result = subprocess.run(
        [sys.executable, str(project_root / "main.py"),
         "--orders", str(orders_csv),
         "--barcodes", str(barcodes_csv),
         "--output", str(output_csv)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 3  # ValidationError
    assert "Expected header" in result.stderr
