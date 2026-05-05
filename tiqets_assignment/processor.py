import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .io import configure_logger, iter_csv_rows
from .models import BarcodeAggregation, BarcodeRow, OrderRow


class OrderProcessor:
    """Handles processing of orders and barcodes for aggregation."""

    def __init__(self, logger=None):
        """Initialize the processor with an optional logger."""
        self.logger = logger or configure_logger()

    def validate_order_row(self, row: Dict[str, str], row_index: int) -> Optional[OrderRow]:
        """Validate a single order row from CSV.

        Args:
            row: Dictionary of column values from the CSV row.
            row_index: 1-based index of the row for error reporting.

        Returns:
            OrderRow if valid, None otherwise.
        """
        order_id = row.get("order_id", "")
        customer_id = row.get("customer_id", "")
        if not order_id or not customer_id:
            self.logger.error(
                "Invalid order row %s: missing order_id or customer_id",
                row_index,
            )
            return None
        return OrderRow(order_id=order_id, customer_id=customer_id)

    def validate_barcode_row(self, row: Dict[str, str], row_index: int) -> Optional[BarcodeRow]:
        """Validate a single barcode row from CSV.

        Args:
            row: Dictionary of column values from the CSV row.
            row_index: 1-based index of the row for error reporting.

        Returns:
            BarcodeRow if valid, None otherwise.
        """
        barcode = row.get("barcode", "")
        order_id = row.get("order_id", "")
        if not barcode:
            self.logger.error("Invalid barcode row %s: missing barcode", row_index)
            return None
        return BarcodeRow(barcode=barcode, order_id=order_id or None)

    def read_orders(self, path: Path) -> Dict[str, str]:
        """Read and validate orders from CSV file.

        Args:
            path: Path to the orders CSV file.

        Returns:
            Dictionary mapping order_id to customer_id for valid orders.
        """
        orders: Dict[str, str] = {}
        for row_index, row in iter_csv_rows(path, ["order_id", "customer_id"]):
            validated = self.validate_order_row(row, row_index)
            if validated is None:
                continue
            if validated.order_id in orders:
                self.logger.error(
                    "Duplicate order_id %r on row %s, ignoring duplicate",
                    validated.order_id,
                    row_index,
                )
                continue
            orders[validated.order_id] = validated.customer_id
        return orders

    def read_barcodes(self, path: Path, orders: Dict[str, str]) -> Tuple[Dict[str, List[str]], int]:
        """
        Read and validate barcodes from CSV, filtering invalid ones during ingestion.

        Streams the barcodes file row-by-row for memory efficiency with large files.
        Validates each barcode against the in-memory orders dict (O(1) lookup).
        Only stores valid barcodes in the map, avoiding unnecessary memory usage.
        """
        barcode_map: Dict[str, List[str]] = defaultdict(list)
        seen_barcodes: Dict[str, int] = {}
        unused_count = 0
        for row_index, row in iter_csv_rows(path, ["barcode", "order_id"]):
            validated = self.validate_barcode_row(row, row_index)
            if validated is None:
                continue
            if validated.barcode in seen_barcodes:
                first_seen = seen_barcodes[validated.barcode]
                self.logger.error(
                    "Duplicate barcode %r on row %s (first seen on row %s), ignoring duplicate",
                    validated.barcode,
                    row_index,
                    first_seen,
                )
                continue
            seen_barcodes[validated.barcode] = row_index
            if validated.order_id is None:
                unused_count += 1
                continue
            if validated.order_id not in orders:
                self.logger.error(
                    "Barcode references unknown order_id %r on row %s, ignoring",
                    validated.order_id,
                    row_index,
                )
                continue
            barcode_map[validated.order_id].append(validated.barcode)
        return barcode_map, unused_count

    def aggregate(self, orders: Dict[str, str], barcode_map: Dict[str, List[str]]) -> List[BarcodeAggregation]:
        """Aggregate orders with their barcodes into BarcodeAggregation objects.

        Args:
            orders: Dictionary of order_id to customer_id.
            barcode_map: Dictionary of order_id to list of barcodes.

        Returns:
            List of BarcodeAggregation sorted by order_id.
        """
        result: List[BarcodeAggregation] = []
        for order_id, customer_id in sorted(orders.items(), key=lambda item: item[0]):
            barcodes = sorted(barcode_map.get(order_id, []))
            if not barcodes:
                self.logger.error("Order %r has no barcodes and will be ignored", order_id)
                continue
            result.append(BarcodeAggregation(customer_id=customer_id, order_id=order_id, barcodes=barcodes))
        return result

    def write_output(self, path: Path, aggregated: Iterable[BarcodeAggregation]) -> None:
        """Write aggregated data to CSV file.

        Args:
            path: Output file path.
            aggregated: Iterable of BarcodeAggregation to write.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["customer_id", "order_id", "barcodes"])
            for entry in aggregated:
                writer.writerow([entry.customer_id, entry.order_id, json.dumps(entry.barcodes)])

    def top_customers(self, aggregated: Iterable[BarcodeAggregation], top_n: int = 5) -> List[Tuple[str, int]]:
        """Get top customers by total ticket count.

        Args:
            aggregated: Iterable of BarcodeAggregation.
            top_n: Number of top customers to return.

        Returns:
            List of (customer_id, ticket_count) tuples, sorted by count descending.
        """
        counter = Counter()
        for entry in aggregated:
            counter[entry.customer_id] += len(entry.barcodes)
        return counter.most_common(top_n)
