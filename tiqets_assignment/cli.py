import argparse
from pathlib import Path
from typing import List, Optional

from .io import configure_logger, ValidationError
from .processor import OrderProcessor


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional list of arguments to parse.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Aggregate Tiqets barcodes and orders into customer-level voucher CSV output."
    )
    parser.add_argument(
        "--orders",
        default="orders.csv",
        help="Path to orders CSV file (default: orders.csv)",
    )
    parser.add_argument(
        "--barcodes",
        default="barcodes.csv",
        help="Path to barcodes CSV file (default: barcodes.csv)",
    )
    parser.add_argument(
        "--output",
        default="orders_with_barcodes.csv",
        help="Output path for aggregated CSV (default: orders_with_barcodes.csv)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI application.

    Args:
        argv: Optional list of command-line arguments.

    Returns:
        Exit code: 0 for success, non-zero for errors.
    """
    args = parse_args(argv)
    logger = configure_logger()

    # Validate input files exist and are files
    for file_path in [args.orders, args.barcodes]:
        path = Path(file_path)
        if not path.exists():
            logger.error("Input file does not exist: %s", file_path)
            return 2
        if not path.is_file():
            logger.error("Input path is not a file: %s", file_path)
            return 2

    processor = OrderProcessor(logger=logger)

    try:
        orders = processor.read_orders(Path(args.orders))
        barcode_map, unused_count = processor.read_barcodes(Path(args.barcodes), orders)
        aggregated = processor.aggregate(orders, barcode_map)

        processor.write_output(Path(args.output), aggregated)

        print("Top 5 customers")
        for customer_id, ticket_count in processor.top_customers(aggregated):
            print(f"{customer_id}, {ticket_count}")
        print(f"Unused barcodes: {unused_count}")
        return 0
    except FileNotFoundError as exc:
        logger.error("File not found: %s", exc)
        return 2
    except ValidationError as exc:
        logger.error("Validation error: %s", exc)
        return 3
    except Exception:
        logger.exception("Unexpected failure while processing data")
        return 1
