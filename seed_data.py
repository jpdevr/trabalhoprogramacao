import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "payment_system.db"


def utc_now():
    return datetime.now(timezone.utc)


CUSTOMERS = [
    {
        "legal_name": "Mercado Nova Era LTDA",
        "cnpj": "12.345.678/0001-90",
        "email": "compras@novaera.com.br",
        "is_active": 1,
    },
    {
        "legal_name": "Construtora Horizonte SA",
        "cnpj": "23.456.789/0001-01",
        "email": "suprimentos@horizonte.com.br",
        "is_active": 1,
    },
    {
        "legal_name": "Farmacia Central Popular LTDA",
        "cnpj": "34.567.890/0001-12",
        "email": "gestao@farmaciacentral.com.br",
        "is_active": 1,
    },
    {
        "legal_name": "Atacado Boa Compra LTDA",
        "cnpj": "45.678.901/0001-23",
        "email": "pedidos@boacompra.com.br",
        "is_active": 1,
    },
    {
        "legal_name": "Distribuidora Litoral Sul LTDA",
        "cnpj": "56.789.012/0001-34",
        "email": "contato@litoralsul.com.br",
        "is_active": 0,
    },
]

PRODUCTS = [
    {"sku": "ARZ-001", "name": "Arroz Tipo 1 5kg", "base_price": "32.90", "is_active": 1},
    {"sku": "FEJ-001", "name": "Feijao Carioca 1kg", "base_price": "8.40", "is_active": 1},
    {"sku": "CAF-500", "name": "Cafe Torrado 500g", "base_price": "15.90", "is_active": 1},
    {"sku": "OLE-900", "name": "Oleo de Soja 900ml", "base_price": "7.80", "is_active": 1},
    {"sku": "ACH-400", "name": "Achocolatado 400g", "base_price": "9.90", "is_active": 1},
    {"sku": "LMP-500", "name": "Limpador Multiuso 500ml", "base_price": "6.70", "is_active": 1},
]

PAYMENT_CONDITIONS = [
    {"name": "A vista", "installments": 1, "interest_rate": "0"},
    {"name": "30 dias", "installments": 1, "interest_rate": "0"},
    {"name": "2x sem juros", "installments": 2, "interest_rate": "0"},
    {"name": "3x com juros", "installments": 3, "interest_rate": "1.9900"},
]

CUSTOMER_PRICES = [
    ("12.345.678/0001-90", "ARZ-001", "35.50"),
    ("12.345.678/0001-90", "CAF-500", "17.20"),
    ("23.456.789/0001-01", "LMP-500", "7.10"),
    ("23.456.789/0001-01", "OLE-900", "8.45"),
    ("34.567.890/0001-12", "ACH-400", "10.40"),
    ("45.678.901/0001-23", "FEJ-001", "8.95"),
    ("45.678.901/0001-23", "CAF-500", "16.80"),
]

SALES = [
    {
        "customer_cnpj": "12.345.678/0001-90",
        "payment_name": "30 dias",
        "created_at": utc_now() - timedelta(days=40),
        "items": [
            {"sku": "ARZ-001", "quantity": 12},
            {"sku": "CAF-500", "quantity": 8},
            {"sku": "OLE-900", "quantity": 20},
        ],
    },
    {
        "customer_cnpj": "23.456.789/0001-01",
        "payment_name": "3x com juros",
        "created_at": utc_now() - timedelta(days=32),
        "items": [
            {"sku": "LMP-500", "quantity": 30},
            {"sku": "OLE-900", "quantity": 16},
        ],
    },
    {
        "customer_cnpj": "34.567.890/0001-12",
        "payment_name": "A vista",
        "created_at": utc_now() - timedelta(days=25),
        "items": [
            {"sku": "ACH-400", "quantity": 18},
            {"sku": "CAF-500", "quantity": 6},
        ],
    },
    {
        "customer_cnpj": "45.678.901/0001-23",
        "payment_name": "2x sem juros",
        "created_at": utc_now() - timedelta(days=15),
        "items": [
            {"sku": "FEJ-001", "quantity": 24},
            {"sku": "ARZ-001", "quantity": 10},
            {"sku": "CAF-500", "quantity": 14},
        ],
    },
    {
        "customer_cnpj": "56.789.012/0001-34",
        "payment_name": "A vista",
        "created_at": utc_now() - timedelta(days=7),
        "items": [
            {"sku": "FEJ-001", "quantity": 10},
            {"sku": "LMP-500", "quantity": 12},
        ],
    },
]


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def fetch_id(conn, table, field, value):
    row = conn.execute(f"SELECT id FROM {table} WHERE {field} = ?", (value,)).fetchone()
    return row["id"] if row else None


def ensure_customer(conn, payload):
    conn.execute(
        """
        INSERT INTO customers (legal_name, cnpj, email, is_active)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(cnpj) DO UPDATE SET
            legal_name = excluded.legal_name,
            email = excluded.email,
            is_active = excluded.is_active
        """,
        (payload["legal_name"], payload["cnpj"], payload["email"], payload["is_active"]),
    )


def ensure_product(conn, payload):
    conn.execute(
        """
        INSERT INTO products (sku, name, base_price, is_active)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(sku) DO UPDATE SET
            name = excluded.name,
            base_price = excluded.base_price,
            is_active = excluded.is_active
        """,
        (payload["sku"], payload["name"], payload["base_price"], payload["is_active"]),
    )


def ensure_payment_condition(conn, payload):
    conn.execute(
        """
        INSERT INTO payment_conditions (name, installments, interest_rate)
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            installments = excluded.installments,
            interest_rate = excluded.interest_rate
        """,
        (payload["name"], payload["installments"], payload["interest_rate"]),
    )


def ensure_customer_price(conn, customer_cnpj, product_sku, price):
    customer_id = fetch_id(conn, "customers", "cnpj", customer_cnpj)
    product_id = fetch_id(conn, "products", "sku", product_sku)
    conn.execute(
        """
        INSERT INTO customer_prices (customer_id, product_id, price, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(customer_id, product_id) DO UPDATE SET
            price = excluded.price,
            updated_at = excluded.updated_at
        """,
        (customer_id, product_id, price, utc_now().isoformat()),
    )


def customer_has_sales(conn, customer_id):
    row = conn.execute("SELECT 1 FROM sales WHERE customer_id = ? LIMIT 1", (customer_id,)).fetchone()
    return row is not None


def resolve_unit_price(conn, customer_id, product_id):
    custom_price = conn.execute(
        """
        SELECT price FROM customer_prices
        WHERE customer_id = ? AND product_id = ?
        """,
        (customer_id, product_id),
    ).fetchone()
    if custom_price:
        return custom_price["price"]
    row = conn.execute("SELECT base_price FROM products WHERE id = ?", (product_id,)).fetchone()
    return row["base_price"]


def ensure_sales(conn):
    for sale in SALES:
        customer_id = fetch_id(conn, "customers", "cnpj", sale["customer_cnpj"])
        payment_condition_id = fetch_id(conn, "payment_conditions", "name", sale["payment_name"])
        if customer_has_sales(conn, customer_id):
            continue

        cursor = conn.execute(
            """
            INSERT INTO sales (customer_id, payment_condition_id, created_at)
            VALUES (?, ?, ?)
            """,
            (customer_id, payment_condition_id, sale["created_at"].isoformat()),
        )
        sale_id = cursor.lastrowid

        for item in sale["items"]:
            product_id = fetch_id(conn, "products", "sku", item["sku"])
            unit_price = resolve_unit_price(conn, customer_id, product_id)
            conn.execute(
                """
                INSERT INTO sale_items (sale_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (sale_id, product_id, item["quantity"], unit_price),
            )


def main():
    with connect() as conn:
        for customer in CUSTOMERS:
            ensure_customer(conn, customer)

        for product in PRODUCTS:
            ensure_product(conn, product)

        for condition in PAYMENT_CONDITIONS:
            ensure_payment_condition(conn, condition)

        for customer_cnpj, product_sku, price in CUSTOMER_PRICES:
            ensure_customer_price(conn, customer_cnpj, product_sku, price)

        ensure_sales(conn)
        conn.commit()

        summary = {
            "customers": conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
            "products": conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "payment_conditions": conn.execute("SELECT COUNT(*) FROM payment_conditions").fetchone()[0],
            "customer_prices": conn.execute("SELECT COUNT(*) FROM customer_prices").fetchone()[0],
            "sales": conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0],
            "sale_items": conn.execute("SELECT COUNT(*) FROM sale_items").fetchone()[0],
            "notifications": conn.execute("SELECT COUNT(*) FROM price_drop_notifications").fetchone()[0],
        }

    print("Banco populado com sucesso.")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
