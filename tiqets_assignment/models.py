from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class OrderRow:
    """Represents a validated order row from CSV."""
    order_id: str
    customer_id: str


@dataclass(frozen=True)
class BarcodeRow:
    """Represents a validated barcode row from CSV."""
    barcode: str
    order_id: Optional[str]


@dataclass(frozen=True)
class BarcodeAggregation:
    """Aggregated data for an order with its barcodes."""
    customer_id: str
    order_id: str
    barcodes: List[str]
