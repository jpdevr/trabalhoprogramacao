import queue
import sqlite3
import threading
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from flask import Flask, jsonify, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "payment_system.db"

app = Flask(__name__)

price_events: "queue.Queue[dict]" = queue.Queue()
stop_event = threading.Event()


def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def now_iso():
    return datetime.utcnow().isoformat()


def init_db():
    with db_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                legal_name TEXT NOT NULL,
                cnpj TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                base_price NUMERIC NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS payment_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                installments INTEGER NOT NULL,
                interest_rate NUMERIC NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS customer_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                price NUMERIC NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(customer_id, product_id),
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                payment_condition_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                FOREIGN KEY(payment_condition_id) REFERENCES payment_conditions(id)
            );

            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price NUMERIC NOT NULL,
                FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS price_drop_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                old_price_paid NUMERIC NOT NULL,
                new_price NUMERIC NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id)
            );
            """
        )


def fetch_one_or_404(conn, table, obj_id):
    row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (obj_id,)).fetchone()
    if not row:
        return None, (jsonify({"error": f"{table} id={obj_id} nao encontrado"}), 404)
    return row, None


def row_to_dict(row):
    return dict(row) if row else None


def start_price_worker():
    def _run():
        while not stop_event.is_set():
            try:
                event = price_events.get(timeout=0.3)
            except queue.Empty:
                continue

            with db_conn() as conn:
                items = conn.execute(
                    """
                    SELECT s.customer_id, si.product_id, si.unit_price, si.sale_id
                    FROM sale_items si
                    JOIN sales s ON s.id = si.sale_id
                    WHERE si.product_id = ? AND CAST(si.unit_price AS REAL) > CAST(? AS REAL)
                    """,
                    (event["product_id"], str(event["new_price"])),
                ).fetchall()

                for item in items:
                    msg = (
                        f"Produto {item['product_id']} ficou mais barato ({event['new_price']}) do que o "
                        f"preco pago ({item['unit_price']}) na venda {item['sale_id']}."
                    )
                    conn.execute(
                        """
                        INSERT INTO price_drop_notifications
                        (customer_id, product_id, old_price_paid, new_price, message, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item["customer_id"],
                            item["product_id"],
                            item["unit_price"],
                            str(event["new_price"]),
                            msg,
                            now_iso(),
                        ),
                    )
                conn.commit()
            price_events.task_done()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


@app.get("/")
def health():
    return {"status": "ok", "service": "payment-system-api"}


@app.post("/api/customers")
def create_customer():
    data = request.get_json(force=True)
    with db_conn() as conn:
        cur = conn.execute(
            "INSERT INTO customers (legal_name, cnpj, email, is_active) VALUES (?, ?, ?, ?)",
            (data["legal_name"], data["cnpj"], data["email"], int(data.get("is_active", True))),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM customers WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row), 201


@app.get("/api/customers")
def list_customers():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM customers ORDER BY id").fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.put("/api/customers/<int:customer_id>")
def update_customer(customer_id):
    data = request.get_json(force=True)
    with db_conn() as conn:
        row, err = fetch_one_or_404(conn, "customers", customer_id)
        if err:
            return err
        conn.execute(
            """
            UPDATE customers SET legal_name = ?, cnpj = ?, email = ?, is_active = ? WHERE id = ?
            """,
            (
                data.get("legal_name", row["legal_name"]),
                data.get("cnpj", row["cnpj"]),
                data.get("email", row["email"]),
                int(data.get("is_active", row["is_active"])),
                customer_id,
            ),
        )
        conn.commit()
        upd = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    return row_to_dict(upd)


@app.delete("/api/customers/<int:customer_id>")
def delete_customer(customer_id):
    with db_conn() as conn:
        row, err = fetch_one_or_404(conn, "customers", customer_id)
        if err:
            return err
        conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()
    return "", 204


@app.post("/api/products")
def create_product():
    data = request.get_json(force=True)
    with db_conn() as conn:
        cur = conn.execute(
            "INSERT INTO products (sku, name, base_price, is_active) VALUES (?, ?, ?, ?)",
            (data["sku"], data["name"], str(data["base_price"]), int(data.get("is_active", True))),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM products WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row), 201


@app.get("/api/products")
def list_products():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.put("/api/products/<int:product_id>")
def update_product(product_id):
    data = request.get_json(force=True)
    with db_conn() as conn:
        row, err = fetch_one_or_404(conn, "products", product_id)
        if err:
            return err

        old_price = Decimal(str(row["base_price"]))
        new_price = Decimal(str(data.get("base_price", row["base_price"])))

        conn.execute(
            """
            UPDATE products SET sku = ?, name = ?, base_price = ?, is_active = ? WHERE id = ?
            """,
            (
                data.get("sku", row["sku"]),
                data.get("name", row["name"]),
                str(new_price),
                int(data.get("is_active", row["is_active"])),
                product_id,
            ),
        )
        conn.commit()
        upd = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    if new_price < old_price:
        price_events.put({"product_id": product_id, "new_price": new_price})

    return row_to_dict(upd)


@app.delete("/api/products/<int:product_id>")
def delete_product(product_id):
    with db_conn() as conn:
        row, err = fetch_one_or_404(conn, "products", product_id)
        if err:
            return err
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
    return "", 204


@app.post("/api/payment-conditions")
def create_payment_condition():
    data = request.get_json(force=True)
    with db_conn() as conn:
        cur = conn.execute(
            "INSERT INTO payment_conditions (name, installments, interest_rate) VALUES (?, ?, ?)",
            (data["name"], data["installments"], str(data.get("interest_rate", 0))),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM payment_conditions WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row), 201


@app.get("/api/payment-conditions")
def list_payment_conditions():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM payment_conditions ORDER BY id").fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.put("/api/payment-conditions/<int:condition_id>")
def update_payment_condition(condition_id):
    data = request.get_json(force=True)
    with db_conn() as conn:
        row, err = fetch_one_or_404(conn, "payment_conditions", condition_id)
        if err:
            return err
        conn.execute(
            """
            UPDATE payment_conditions SET name = ?, installments = ?, interest_rate = ? WHERE id = ?
            """,
            (
                data.get("name", row["name"]),
                data.get("installments", row["installments"]),
                str(data.get("interest_rate", row["interest_rate"])),
                condition_id,
            ),
        )
        conn.commit()
        upd = conn.execute("SELECT * FROM payment_conditions WHERE id = ?", (condition_id,)).fetchone()
    return row_to_dict(upd)


@app.delete("/api/payment-conditions/<int:condition_id>")
def delete_payment_condition(condition_id):
    with db_conn() as conn:
        row, err = fetch_one_or_404(conn, "payment_conditions", condition_id)
        if err:
            return err
        conn.execute("DELETE FROM payment_conditions WHERE id = ?", (condition_id,))
        conn.commit()
    return "", 204


@app.post("/api/customer-prices")
def create_customer_price():
    data = request.get_json(force=True)
    with db_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO customer_prices (customer_id, product_id, price, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (data["customer_id"], data["product_id"], str(data["price"]), now_iso()),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM customer_prices WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row), 201


@app.get("/api/customer-prices")
def list_customer_prices():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM customer_prices ORDER BY id").fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.put("/api/customer-prices/<int:price_id>")
def update_customer_price(price_id):
    data = request.get_json(force=True)
    with db_conn() as conn:
        row, err = fetch_one_or_404(conn, "customer_prices", price_id)
        if err:
            return err
        conn.execute(
            "UPDATE customer_prices SET price = ?, updated_at = ? WHERE id = ?",
            (str(data["price"]), now_iso(), price_id),
        )
        conn.commit()
        upd = conn.execute("SELECT * FROM customer_prices WHERE id = ?", (price_id,)).fetchone()
    return row_to_dict(upd)


@app.delete("/api/customer-prices/<int:price_id>")
def delete_customer_price(price_id):
    with db_conn() as conn:
        row, err = fetch_one_or_404(conn, "customer_prices", price_id)
        if err:
            return err
        conn.execute("DELETE FROM customer_prices WHERE id = ?", (price_id,))
        conn.commit()
    return "", 204


@app.post("/api/sales")
def create_sale():
    data = request.get_json(force=True)
    items = data.get("items", [])
    if not items:
        return jsonify({"error": "Venda precisa de pelo menos 1 item"}), 400

    with db_conn() as conn:
        cur = conn.execute(
            "INSERT INTO sales (customer_id, payment_condition_id, created_at) VALUES (?, ?, ?)",
            (data["customer_id"], data["payment_condition_id"], now_iso()),
        )
        sale_id = cur.lastrowid

        for item in items:
            custom_price = conn.execute(
                """
                SELECT price FROM customer_prices
                WHERE customer_id = ? AND product_id = ?
                """,
                (data["customer_id"], item["product_id"]),
            ).fetchone()
            if custom_price:
                unit_price = custom_price["price"]
            else:
                p = conn.execute("SELECT base_price FROM products WHERE id = ?", (item["product_id"],)).fetchone()
                if not p:
                    return jsonify({"error": f"Produto {item['product_id']} nao encontrado"}), 404
                unit_price = p["base_price"]

            conn.execute(
                "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (sale_id, item["product_id"], item["quantity"], unit_price),
            )

        conn.commit()

        sale = conn.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()
        sale_items = conn.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()

    out = row_to_dict(sale)
    out["items"] = [row_to_dict(i) for i in sale_items]
    return out, 201


@app.get("/api/sales")
def list_sales():
    with db_conn() as conn:
        sales = conn.execute("SELECT * FROM sales ORDER BY id").fetchall()
        result = []
        for s in sales:
            items = conn.execute("SELECT * FROM sale_items WHERE sale_id = ?", (s["id"],)).fetchall()
            obj = row_to_dict(s)
            obj["items"] = [row_to_dict(i) for i in items]
            result.append(obj)
    return jsonify(result)


@app.get("/api/notifications")
def list_notifications():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM price_drop_notifications ORDER BY id DESC").fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.get("/api/reports/customer-sales")
def customer_sales_report():
    cnpj = request.args.get("cnpj")
    legal_name = request.args.get("legal_name")

    if not cnpj and not legal_name:
        return jsonify({"error": "Informe cnpj ou legal_name"}), 400

    with db_conn() as conn:
        if cnpj:
            customer = conn.execute("SELECT * FROM customers WHERE cnpj = ?", (cnpj,)).fetchone()
        else:
            customer = conn.execute(
                "SELECT * FROM customers WHERE lower(legal_name) LIKE lower(?) LIMIT 1",
                (f"%{legal_name}%",),
            ).fetchone()

        if not customer:
            return jsonify({"error": "Cliente nao encontrado"}), 404

        sales = conn.execute("SELECT * FROM sales WHERE customer_id = ?", (customer["id"],)).fetchall()

        total = Decimal("0")
        products = {}

        for s in sales:
            items = conn.execute("SELECT * FROM sale_items WHERE sale_id = ?", (s["id"],)).fetchall()
            for item in items:
                prod = conn.execute("SELECT name FROM products WHERE id = ?", (item["product_id"],)).fetchone()
                subtotal = Decimal(str(item["unit_price"])) * int(item["quantity"])
                total += subtotal
                pid = item["product_id"]
                if pid not in products:
                    products[pid] = {
                        "product_id": pid,
                        "product_name": prod["name"] if prod else "N/A",
                        "quantity": 0,
                        "total": Decimal("0"),
                    }
                products[pid]["quantity"] += int(item["quantity"])
                products[pid]["total"] += subtotal

    return {
        "customer_id": customer["id"],
        "legal_name": customer["legal_name"],
        "cnpj": customer["cnpj"],
        "sales_count": len(sales),
        "total_amount": str(total),
        "products": [
            {
                **v,
                "total": str(v["total"]),
            }
            for v in products.values()
        ],
    }


init_db()
start_price_worker()


if __name__ == "__main__":
    app.run(debug=True)
