import sqlite3
import hashlib
import base64
import os
from contextlib import contextmanager
from datetime import datetime, date

DB_PATH = None

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS auth_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME,
    is_superuser BOOL NOT NULL DEFAULT 0,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL DEFAULT '',
    is_staff BOOL NOT NULL DEFAULT 0,
    is_active BOOL NOT NULL DEFAULT 1,
    date_joined DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS store_customer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_by_id INTEGER NOT NULL REFERENCES auth_user(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    national_id VARCHAR(20) NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS store_producttype (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    created_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS store_product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_type_id BIGINT REFERENCES store_producttype(id),
    name VARCHAR(200) NOT NULL,
    unit VARCHAR(20) NOT NULL DEFAULT '',
    purchase_price DECIMAL NOT NULL DEFAULT 0,
    selling_price DECIMAL NOT NULL DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 0,
    description TEXT NOT NULL DEFAULT '',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS store_product_price (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id BIGINT NOT NULL REFERENCES store_product(id),
    price_label VARCHAR(100) NOT NULL,
    amount DECIMAL NOT NULL DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS store_supply_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    price_id BIGINT NOT NULL REFERENCES store_product_price(id),
    quantity INTEGER NOT NULL DEFAULT 0,
    buy_price DECIMAL NOT NULL DEFAULT 0,
    sale_price DECIMAL NOT NULL DEFAULT 0,
    supplied_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS store_sale (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id BIGINT NOT NULL REFERENCES store_customer(id),
    created_by_id INTEGER NOT NULL REFERENCES auth_user(id),
    sale_date DATETIME NOT NULL,
    total_amount DECIMAL NOT NULL,
    payment_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    payment_due_days INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    created_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS store_saleitem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id BIGINT NOT NULL REFERENCES store_sale(id),
    product_id BIGINT NOT NULL REFERENCES store_product(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL NOT NULL,
    subtotal DECIMAL NOT NULL
);
CREATE TABLE IF NOT EXISTS store_payment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id BIGINT NOT NULL REFERENCES store_sale(id),
    customer_id BIGINT NOT NULL REFERENCES store_customer(id),
    installment_id BIGINT REFERENCES store_installment(id),
    received_by_id INTEGER NOT NULL REFERENCES auth_user(id),
    amount DECIMAL NOT NULL,
    payment_date DATETIME NOT NULL,
    payment_type VARCHAR(20) NOT NULL DEFAULT 'cash',
    notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS store_installment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id BIGINT NOT NULL REFERENCES store_sale(id),
    customer_id BIGINT NOT NULL REFERENCES store_customer(id),
    total_count INTEGER NOT NULL,
    paid_count INTEGER NOT NULL DEFAULT 0,
    amount_per_term DECIMAL NOT NULL,
    amount_paid DECIMAL NOT NULL DEFAULT 0,
    due_day INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    start_date DATE NOT NULL
);
"""

def make_password(password):
    import hashlib, base64, secrets
    salt = secrets.token_hex(6)
    iterations = 720000
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
    encoded = base64.b64encode(key).decode()
    return f'pbkdf2_sha256${iterations}${salt}${encoded}'

def init(db_path):
    global DB_PATH
    DB_PATH = db_path
    _ensure_database()

def _ensure_database():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.executescript(SCHEMA_SQL)
        conn.commit()

        try:
            conn.execute("ALTER TABLE store_product ADD COLUMN unit VARCHAR(20) NOT NULL DEFAULT ''")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE store_sale ADD COLUMN payment_due_days INTEGER NOT NULL DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute("ALTER TABLE store_product_price ADD COLUMN stock INTEGER NOT NULL DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        cur = conn.execute("SELECT COUNT(*) as c FROM auth_user")
        count = cur.fetchone()[0]
        if count == 0:
            pw = make_password('admin123')
            conn.execute(
                "INSERT INTO auth_user (password, is_superuser, username, is_staff, is_active, date_joined) VALUES (?,1,'admin',1,1,datetime('now'))",
                [pw]
            )
            conn.commit()
    finally:
        conn.close()

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

@contextmanager
def transaction():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def fetchone(sql, params=None):
    conn = get_conn()
    try:
        cur = conn.execute(sql, params or [])
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def fetchall(sql, params=None):
    conn = get_conn()
    try:
        cur = conn.execute(sql, params or [])
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def execute(sql, params=None):
    conn = get_conn()
    try:
        cur = conn.execute(sql, params or [])
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def check_password(password, encoded):
    parts = encoded.split('$')
    if len(parts) != 4:
        return False
    algorithm, iterations, salt, hash_b64 = parts
    if algorithm not in ('pbkdf2_sha256',):
        return False
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), int(iterations))
    return base64.b64encode(key).decode() == hash_b64

def today_str():
    return date.today().isoformat()

def month_start():
    return date.today().replace(day=1).isoformat()

def week_ago():
    from datetime import timedelta
    return (date.today() - timedelta(days=7)).isoformat()

def auth_user(username, password):
    user = fetchone("SELECT * FROM auth_user WHERE username=? AND is_active=1", [username])
    if user and check_password(password, user['password']):
        return user
    return None

def get_user(uid):
    return fetchone("SELECT * FROM auth_user WHERE id=?", [uid])

def get_all_users():
    return fetchall("SELECT * FROM auth_user ORDER BY date_joined DESC")

def create_user(data):
    pw = make_password(data['password'])
    return execute(
        "INSERT INTO auth_user (password, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES (?,?,?,?,?,?,?,datetime('now'))",
        [pw, data['username'], data.get('first_name',''), data.get('last_name',''), data.get('email',''), 1 if data.get('is_staff') else 0, 1 if data.get('is_active') else 1]
    )

def update_user(uid, data):
    if data.get('password'):
        pw = make_password(data['password'])
        execute("UPDATE auth_user SET password=? WHERE id=?", [pw, uid])
    execute(
        "UPDATE auth_user SET username=?, first_name=?, last_name=?, email=?, is_staff=?, is_active=? WHERE id=?",
        [data['username'], data.get('first_name',''), data.get('last_name',''), data.get('email',''), 1 if data.get('is_staff') else 0, 1 if data.get('is_active') else 1, uid]
    )

def delete_user(uid):
    execute("DELETE FROM auth_user WHERE id=?", [uid])

def get_customer(cid):
    return fetchone("SELECT * FROM store_customer WHERE id=?", [cid])

def get_all_customers(search=None):
    if search:
        s = f'%{search}%'
        return fetchall("SELECT * FROM store_customer WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? ORDER BY created_at DESC", [s, s, s])
    return fetchall("SELECT * FROM store_customer ORDER BY created_at DESC")

def create_customer(data):
    return execute(
        "INSERT INTO store_customer (first_name, last_name, phone, national_id, address, created_by_id, created_at, updated_at) VALUES (?,?,?,?,?,1,datetime('now'),datetime('now'))",
        [data.get('first_name',''), data.get('last_name',''), data.get('phone',''), data.get('national_id',''), data.get('address','')]
    )

def update_customer(cid, data):
    execute(
        "UPDATE store_customer SET first_name=?, last_name=?, phone=?, national_id=?, address=?, updated_at=datetime('now') WHERE id=?",
        [data.get('first_name',''), data.get('last_name',''), data.get('phone',''), data.get('national_id',''), data.get('address',''), cid]
    )

def delete_customer(cid):
    execute("DELETE FROM store_customer WHERE id=?", [cid])

def customer_debt(cid):
    total = fetchone("SELECT COALESCE(SUM(total_amount),0) as s FROM store_sale WHERE customer_id=? AND status IN ('pending','partial')", [cid])
    paid = fetchone("SELECT COALESCE(SUM(amount),0) as s FROM store_payment WHERE customer_id=?", [cid])
    return max(0, (total['s'] or 0) - (paid['s'] or 0))

def get_product(tid):
    return fetchone("SELECT * FROM store_product WHERE id=?", [tid])

def get_all_products():
    return fetchall(
        "SELECT p.*, pt.name as product_type_name FROM store_product p LEFT JOIN store_producttype pt ON pt.id=p.product_type_id ORDER BY p.name"
    )

def create_product(data):
    return execute(
        "INSERT INTO store_product (name, product_type_id, unit, purchase_price, selling_price, stock, description, created_at, updated_at) VALUES (?,?,?,?,?,?,?,datetime('now'),datetime('now'))",
        [data['name'], data.get('product_type_id'), data.get('unit',''), int(data.get('purchase_price',0) or 0), int(data.get('selling_price',0) or 0), int(data.get('stock',0) or 0), data.get('description','')]
    )

def update_product(tid, data):
    execute(
        "UPDATE store_product SET name=?, product_type_id=?, unit=?, purchase_price=?, selling_price=?, stock=?, description=?, updated_at=datetime('now') WHERE id=?",
        [data['name'], data.get('product_type_id'), data.get('unit',''), int(data.get('purchase_price',0) or 0), int(data.get('selling_price',0) or 0), int(data.get('stock',0) or 0), data.get('description',''), tid]
    )

def delete_product(tid):
    execute("DELETE FROM store_product_price WHERE product_id=?", [tid])
    execute("DELETE FROM store_product WHERE id=?", [tid])

def get_product_prices(pid):
    return fetchall("SELECT * FROM store_product_price WHERE product_id=? ORDER BY id", [pid])

def create_product_price(pid, label, amount, stock=0):
    return execute(
        "INSERT INTO store_product_price (product_id, price_label, amount, stock) VALUES (?,?,?,?)",
        [pid, label, int(amount), int(stock)]
    )

def update_product_price(price_id, label, amount, stock=0):
    execute(
        "UPDATE store_product_price SET price_label=?, amount=?, stock=? WHERE id=?",
        [label, int(amount), int(stock), price_id]
    )

def delete_product_price(price_id):
    execute("DELETE FROM store_supply_log WHERE price_id=?", [price_id])
    execute("DELETE FROM store_product_price WHERE id=?", [price_id])

def create_supply_entry(price_id, quantity, buy_price, sale_price):
    return execute(
        "INSERT INTO store_supply_log (price_id, quantity, buy_price, sale_price, supplied_at) VALUES (?,?,?,?,datetime('now'))",
        [price_id, int(quantity), int(buy_price), int(sale_price)]
    )

def get_supply_log(price_id):
    return fetchall("SELECT * FROM store_supply_log WHERE price_id=? ORDER BY supplied_at DESC", [price_id])

def get_product_types():
    return fetchall("SELECT * FROM store_producttype ORDER BY name")

def get_product_type(tid):
    return fetchone("SELECT * FROM store_producttype WHERE id=?", [tid])

def create_product_type(data):
    return execute("INSERT INTO store_producttype (name, description, created_at) VALUES (?,?,datetime('now'))", [data['name'], data.get('description','')])

def update_product_type(tid, data):
    execute("UPDATE store_producttype SET name=?, description=? WHERE id=?", [data['name'], data.get('description',''), tid])

def delete_product_type(tid):
    execute("UPDATE store_product SET product_type_id=NULL WHERE product_type_id=?", [tid])
    execute("DELETE FROM store_producttype WHERE id=?", [tid])

def get_sale(sid):
    return fetchone("SELECT * FROM store_sale WHERE id=?", [sid])

def get_all_sales(status=None, payment_type=None):
    sql = "SELECT s.*, c.first_name as c_first, c.last_name as c_last FROM store_sale s JOIN store_customer c ON c.id=s.customer_id"
    params = []
    where = []
    if status:
        where.append("s.status=?")
        params.append(status)
    if payment_type:
        where.append("s.payment_type=?")
        params.append(payment_type)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY s.sale_date DESC"
    return fetchall(sql, params)

def get_customer_sales(cid):
    return fetchall("SELECT * FROM store_sale WHERE customer_id=? ORDER BY sale_date DESC", [cid])

def get_customer_payments(cid):
    return fetchall("SELECT * FROM store_payment WHERE customer_id=? ORDER BY payment_date DESC", [cid])

def get_sale_items(sid):
    return fetchall("SELECT si.*, p.name as product_name FROM store_saleitem si JOIN store_product p ON p.id=si.product_id WHERE si.sale_id=?", [sid])

def get_sale_payments(sid):
    return fetchall("SELECT * FROM store_payment WHERE sale_id=? ORDER BY payment_date DESC", [sid])

def get_all_payments(limit=100):
    return fetchall(
        "SELECT p.*, c.first_name, c.last_name FROM store_payment p "
        "JOIN store_customer c ON c.id=p.customer_id "
        "ORDER BY p.payment_date DESC LIMIT ?", [limit])

def sale_total_paid(sid):
    r = fetchone("SELECT COALESCE(SUM(amount),0) as s FROM store_payment WHERE sale_id=?", [sid])
    return r['s'] or 0

def sale_remaining(sid):
    sale = get_sale(sid)
    if not sale:
        return 0
    return (sale['total_amount'] or 0) - sale_total_paid(sid)

def create_sale(customer_id, total_amount, payment_type, status, notes, payment_due_days=0, created_by_id=1):
    return execute(
        "INSERT INTO store_sale (customer_id, created_by_id, total_amount, payment_type, status, payment_due_days, notes, sale_date, created_at) VALUES (?,?,?,?,?,?,?,datetime('now'),datetime('now'))",
        [customer_id, created_by_id, total_amount, payment_type, status, payment_due_days, notes]
    )

def get_overdue_sales():
    return fetchall(
        "SELECT s.*, c.first_name, c.last_name, c.phone "
        "FROM store_sale s JOIN store_customer c ON c.id=s.customer_id "
        "WHERE s.status IN ('pending','partial') AND s.payment_due_days > 0 "
        "AND date(s.sale_date, '+' || s.payment_due_days || ' days') < date('now') "
        "ORDER BY s.sale_date"
    )

def create_sale_item(sale_id, product_id, quantity, unit_price, subtotal, price_id=None):
    if price_id:
        execute(
            "UPDATE store_product_price SET stock=stock-? WHERE id=? AND stock>=?",
            [quantity, price_id, quantity]
        )
    else:
        execute(
            "UPDATE store_product SET stock=stock-? WHERE id=? AND stock>=?",
            [quantity, product_id, quantity]
        )
    return execute(
        "INSERT INTO store_saleitem (sale_id, product_id, quantity, unit_price, subtotal) VALUES (?,?,?,?,?)",
        [sale_id, product_id, quantity, unit_price, subtotal]
    )

def create_payment(sale_id, customer_id, amount, payment_type, notes, received_by_id=1):
    return execute(
        "INSERT INTO store_payment (sale_id, customer_id, received_by_id, amount, payment_type, notes, payment_date) VALUES (?,?,?,?,?,?,datetime('now'))",
        [sale_id, customer_id, received_by_id, amount, payment_type, notes]
    )

def get_installments(sale_id, customer_id):
    return fetchall("SELECT * FROM store_installment WHERE sale_id=? AND customer_id=? AND status='active'", [sale_id, customer_id])

def get_installment(iid):
    return fetchone("SELECT * FROM store_installment WHERE id=?", [iid])

def create_installment(sale_id, customer_id, total_amount, due_days=1):
    return execute(
        "INSERT INTO store_installment (sale_id, customer_id, total_count, paid_count, amount_per_term, due_day, status, start_date) VALUES (?,?,6,0,?,?,'active',date('now'))",
        [sale_id, customer_id, max(1, total_amount // 6), due_days]
    )

def update_installment(iid, paid_count, amount_paid):
    inst = get_installment(iid)
    if not inst:
        return
    new_paid = paid_count + 1
    new_status = 'paid' if new_paid >= inst['total_count'] else 'active'
    execute("UPDATE store_installment SET paid_count=?, amount_paid=?, status=? WHERE id=?", [new_paid, amount_paid, new_status, iid])

def update_sale_status(sid):
    sale = get_sale(sid)
    if not sale:
        return
    paid = sale_total_paid(sid)
    remaining = (sale['total_amount'] or 0) - paid
    if remaining <= 0:
        new_status = 'paid'
    elif paid > 0:
        new_status = 'partial'
    else:
        new_status = 'pending'
    execute("UPDATE store_sale SET status=? WHERE id=?", [new_status, sid])

def daily_sales(d):
    sql = "SELECT * FROM store_sale WHERE date(sale_date)=? AND status!='cancelled'"
    return fetchall(sql, [d])

def monthly_sales(month_start_date):
    sql = "SELECT * FROM store_sale WHERE date(sale_date)>=? AND status!='cancelled'"
    return fetchall(sql, [month_start_date])

def get_debtors():
    return fetchall("""
        SELECT c.id, c.first_name, c.last_name, c.phone,
               COALESCE(s.total,0) as total, COALESCE(p.paid,0) as paid
        FROM store_customer c
        LEFT JOIN (
            SELECT customer_id, SUM(total_amount) as total
            FROM store_sale WHERE status IN ('pending','partial')
            GROUP BY customer_id
        ) s ON s.customer_id=c.id
        LEFT JOIN (
            SELECT customer_id, SUM(amount) as paid
            FROM store_payment GROUP BY customer_id
        ) p ON p.customer_id=c.id
        WHERE COALESCE(s.total,0) > COALESCE(p.paid,0)
        ORDER BY (COALESCE(s.total,0)-COALESCE(p.paid,0)) DESC
    """)

def best_selling(limit=10):
    return fetchall(f"""
        SELECT si.product_id, p.name, SUM(si.quantity) as qty, SUM(si.subtotal) as rev
        FROM store_saleitem si
        JOIN store_product p ON p.id=si.product_id
        GROUP BY si.product_id
        ORDER BY qty DESC LIMIT {limit}
    """)

def yearly_sales(year):
    return fetchall("""
        SELECT strftime('%m', sale_date) as month,
               COUNT(*) as sale_count,
               SUM(total_amount) as total,
               SUM(CASE WHEN payment_type='cash' THEN total_amount ELSE 0 END) as cash_total,
               SUM(CASE WHEN payment_type='installment' THEN total_amount ELSE 0 END) as inst_total
        FROM store_sale
        WHERE strftime('%Y', sale_date)=? AND status!='cancelled'
        GROUP BY strftime('%m', sale_date)
        ORDER BY month
    """, [str(year)])

def yearly_cost(year):
    rows = fetchall("""
        SELECT si.quantity, p.purchase_price
        FROM store_saleitem si
        JOIN store_product p ON p.id=si.product_id
        JOIN store_sale s ON s.id=si.sale_id
        WHERE strftime('%Y', s.sale_date)=? AND s.status!='cancelled'
    """, [str(year)])
    total = 0
    for r in rows:
        total += r['quantity'] * (r['purchase_price'] or 0)
    return total

def sales_by_category():
    return fetchall("""
        SELECT COALESCE(pt.name, 'بدون دسته') as category,
               COUNT(DISTINCT s.id) as sale_count,
               SUM(si.quantity) as qty,
               SUM(si.subtotal) as revenue,
               SUM(si.quantity * COALESCE(p.purchase_price,0)) as cost
        FROM store_saleitem si
        JOIN store_sale s ON s.id=si.sale_id
        JOIN store_product p ON p.id=si.product_id
        LEFT JOIN store_producttype pt ON pt.id=p.product_type_id
        WHERE s.status!='cancelled'
        GROUP BY pt.id
        ORDER BY revenue DESC
    """)

def payment_method_summary():
    return fetchall("""
        SELECT payment_type,
               COUNT(*) as sale_count,
               SUM(total_amount) as total
        FROM store_sale
        WHERE status!='cancelled'
        GROUP BY payment_type
        ORDER BY total DESC
    """)

def installment_report():
    return fetchall("""
        SELECT i.*, c.first_name, c.last_name, c.phone,
               s.total_amount, s.sale_date,
               (SELECT MAX(payment_date) FROM store_payment WHERE installment_id=i.id) as last_payment_date
        FROM store_installment i
        JOIN store_customer c ON c.id=i.customer_id
        JOIN store_sale s ON s.id=i.sale_id
        ORDER BY i.status, i.start_date DESC
    """)

def low_stock_products(threshold=5):
    return fetchall("""
        SELECT p.*, COALESCE(pt.name,'') as product_type_name
        FROM store_product p
        LEFT JOIN store_producttype pt ON pt.id=p.product_type_id
        WHERE p.stock<=?
        ORDER BY p.stock ASC, p.name
    """, [threshold])
