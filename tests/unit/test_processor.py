import csv
import json
import sys
from pathlib import Path

import pytest

from tiqets_assignment.processor import OrderProcessor, BarcodeAggregation


def write_csv(path: Path, header, rows):
    """Write test CSV data to file."""
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def test_aggregation_with_valid_data(tmp_path):
    """Test aggregation with valid orders and barcodes."""
    orders_csv = tmp_path / "orders.csv"
    barcodes_csv = tmp_path / "barcodes.csv"
    write_csv(orders_csv, ["order_id", "customer_id"], [["o1", "c1"], ["o2", "c2"]])
    write_csv(barcodes_csv, ["barcode", "order_id"], [["b1", "o1"], ["b2", "o1"], ["b3", "o2"], ["unused", ""]])

    processor = OrderProcessor()
    orders = processor.read_orders(orders_csv)
    barcode_map, unused_count = processor.read_barcodes(barcodes_csv, orders)
    aggregated = processor.aggregate(orders, barcode_map)

    assert unused_count == 1
    assert aggregated == [
        BarcodeAggregation(customer_id="c1", order_id="o1", barcodes=["b1", "b2"]),
        BarcodeAggregation(customer_id="c2", order_id="o2", barcodes=["b3"]),
    ]
    assert processor.top_customers(aggregated) == [("c1", 2), ("c2", 1)]


def test_duplicate_barcodes_are_ignored(tmp_path, caplog):
    """Test that duplicate barcodes are ignored."""
    orders_csv = tmp_path / "orders.csv"
    barcodes_csv = tmp_path / "barcodes.csv"
    write_csv(orders_csv, ["order_id", "customer_id"], [["o1", "c1"]])
    write_csv(barcodes_csv, ["barcode", "order_id"], [["b1", "o1"], ["b1", "o1"]])

    processor = OrderProcessor()
    caplog.set_level("ERROR")
    orders = processor.read_orders(orders_csv)
    barcode_map, unused_count = processor.read_barcodes(barcodes_csv, orders)

    assert unused_count == 0
    assert barcode_map == {"o1": ["b1"]}
    assert any("Duplicate barcode" in record.message for record in caplog.records)


def test_orders_without_barcodes_are_logged_and_ignored(tmp_path, caplog):
    """Test that orders without barcodes are logged and ignored."""
    orders_csv = tmp_path / "orders.csv"
    barcodes_csv = tmp_path / "barcodes.csv"
    write_csv(orders_csv, ["order_id", "customer_id"], [["o1", "c1"], ["o2", "c2"]])
    write_csv(barcodes_csv, ["barcode", "order_id"], [["b1", "o1"]])

    processor = OrderProcessor()
    caplog.set_level("ERROR")
    orders = processor.read_orders(orders_csv)
    barcode_map, unused_count = processor.read_barcodes(barcodes_csv, orders)
    aggregated = processor.aggregate(orders, barcode_map)

    assert len(aggregated) == 1
    assert aggregated[0].order_id == "o1"
    assert any("has no barcodes" in record.message for record in caplog.records)


def test_write_output_creates_csv(tmp_path):
    """Test writing aggregated output to CSV."""
    order_file = tmp_path / "out.csv"
    aggregated = [BarcodeAggregation(customer_id="c1", order_id="o1", barcodes=["b1", "b2"])]
    processor = OrderProcessor()
    processor.write_output(order_file, aggregated)

    with order_file.open("r", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)

    assert rows[0]["customer_id"] == "c1"
    assert rows[0]["order_id"] == "o1"
    assert json.loads(rows[0]["barcodes"]) == ["b1", "b2"]


def test_duplicate_orders_are_ignored(tmp_path, caplog):
    """Test that duplicate order_ids are ignored."""
    orders_csv = tmp_path / "orders.csv"
    write_csv(orders_csv, ["order_id", "customer_id"], [["o1", "c1"], ["o1", "c2"]])

    processor = OrderProcessor()
    caplog.set_level("ERROR")
    orders = processor.read_orders(orders_csv)

    assert len(orders) == 1
    assert orders["o1"] == "c1"  # First one wins
    assert any("Duplicate order_id" in record.message for record in caplog.records)


def test_barcodes_with_unknown_orders_are_ignored(tmp_path, caplog):
    """Test that barcodes referencing unknown orders are ignored."""
    orders_csv = tmp_path / "orders.csv"
    barcodes_csv = tmp_path / "barcodes.csv"
    write_csv(orders_csv, ["order_id", "customer_id"], [["o1", "c1"]])
    write_csv(barcodes_csv, ["barcode", "order_id"], [["b1", "o1"], ["b2", "o2"]])  # o2 unknown

    processor = OrderProcessor()
    caplog.set_level("ERROR")
    orders = processor.read_orders(orders_csv)
    barcode_map, unused_count = processor.read_barcodes(barcodes_csv, orders)

    assert unused_count == 0
    assert barcode_map == {"o1": ["b1"]}
    assert any("unknown order_id" in record.message for record in caplog.records)


def test_top_customers_with_ties(tmp_path):
    """Test top customers when there are ties in ticket counts."""
    aggregated = [
        BarcodeAggregation(customer_id="c1", order_id="o1", barcodes=["b1", "b2"]),
        BarcodeAggregation(customer_id="c2", order_id="o2", barcodes=["b3", "b4"]),
        BarcodeAggregation(customer_id="c3", order_id="o3", barcodes=["b5"]),
    ]
    processor = OrderProcessor()
    top = processor.top_customers(aggregated, top_n=2)

    assert top == [("c1", 2), ("c2", 2)]  # c1 and c2 tie, c3 has 1


def test_aggregate_sorts_by_order_id(tmp_path):
    """Test that aggregate sorts results by order_id."""
    orders_csv = tmp_path / "orders.csv"
    barcodes_csv = tmp_path / "barcodes.csv"
    write_csv(orders_csv, ["order_id", "customer_id"], [["o3", "c1"], ["o1", "c2"]])
    write_csv(barcodes_csv, ["barcode", "order_id"], [["b1", "o3"], ["b2", "o1"]])

    processor = OrderProcessor()
    orders = processor.read_orders(orders_csv)
    barcode_map, unused_count = processor.read_barcodes(barcodes_csv, orders)
    aggregated = processor.aggregate(orders, barcode_map)

    assert len(aggregated) == 2
    assert aggregated[0].order_id == "o1"
    assert aggregated[1].order_id == "o3"


def test_write_output_creates_parent_dirs(tmp_path):
    """Test that write_output creates parent directories if needed."""
    output_dir = tmp_path / "subdir"
    order_file = output_dir / "out.csv"
    aggregated = [BarcodeAggregation(customer_id="c1", order_id="o1", barcodes=["b1"])]
    processor = OrderProcessor()
    processor.write_output(order_file, aggregated)

    assert order_file.exists()
    with order_file.open("r", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    assert len(rows) == 1
