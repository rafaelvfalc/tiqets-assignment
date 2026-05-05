# SQL Data Model

This section models how the data would be stored in a SQL database.

## Tables

- `customers`
  - `customer_id` (PK)

- `orders`
  - `order_id` (PK)
  - `customer_id` (FK -> customers.customer_id)

- `barcodes`
  - `barcode` (PK)
  - `order_id` (FK -> orders.order_id, nullable)

## Relationships

- One `customer` can have many `orders`
- One `order` can have many `barcodes`
- A barcode may be unused when `order_id` is NULL

## Example schema

```sql
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE barcodes (
    barcode TEXT PRIMARY KEY,
    order_id TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
```

## Index recommendations

- `INDEX idx_orders_customer_id ON orders(customer_id);`
- `INDEX idx_barcodes_order_id ON barcodes(order_id);`

## UML-style model

```text
customers
  1  <--- n
orders
  1  <--- n
barcodes
```

A barcode is either assigned to exactly one order or remains unused (`order_id IS NULL`).
