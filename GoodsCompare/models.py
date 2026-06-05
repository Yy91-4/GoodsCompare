import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'goodscompare.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            spec TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, spec)
        );
        CREATE TABLE IF NOT EXISTS price_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER REFERENCES products(id),
            platform TEXT NOT NULL,
            price REAL NOT NULL,
            shop TEXT DEFAULT '',
            url TEXT DEFAULT '',
            source TEXT NOT NULL CHECK(source IN ('auto', 'manual')),
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER REFERENCES products(id),
            platform TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(product_id, platform)
        );
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()


def add_product(name, spec=''):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO products (name, spec) VALUES (?, ?)",
            (name, spec)
        )
        conn.commit()
        if cur.lastrowid:
            return cur.lastrowid
        row = conn.execute(
            "SELECT id FROM products WHERE name=? AND spec=?",
            (name, spec)
        ).fetchone()
        return row['id']
    finally:
        conn.close()


def get_or_create_product(name, spec=''):
    product_id = add_product(name, spec)
    conn = get_db()
    try:
        return dict(conn.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ).fetchone())
    finally:
        conn.close()


def add_price_record(product_id, platform, price, shop='', url='', source='auto'):
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO price_records (product_id, platform, price, shop, url, source)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (product_id, platform, price, shop, url, source)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_price_trends(product_name):
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT pr.*, p.name, p.spec
               FROM price_records pr
               JOIN products p ON pr.product_id = p.id
               WHERE p.name = ?
               ORDER BY pr.recorded_at ASC""",
            (product_name,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_price_trends_grouped(product_name):
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT pr.platform, pr.price, DATE(pr.recorded_at) as date
               FROM price_records pr
               JOIN products p ON pr.product_id = p.id
               WHERE p.name = ?
               ORDER BY pr.recorded_at ASC""",
            (product_name,)
        ).fetchall()

        date_set = sorted(set(r['date'] for r in rows))
        datasets = {}
        for r in rows:
            if r['platform'] not in datasets:
                datasets[r['platform']] = {d: None for d in date_set}
            datasets[r['platform']][r['date']] = r['price']

        return {
            'product_name': product_name,
            'labels': date_set,
            'datasets': [
                {'platform': p, 'prices': [datasets[p].get(d) for d in date_set]}
                for p in datasets
            ]
        }
    finally:
        conn.close()


def add_favorite(product_id, platform):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO favorites (product_id, platform) VALUES (?, ?)",
            (product_id, platform)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_favorites():
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT f.id as fav_id, f.platform, p.name, p.spec,
                      (SELECT price FROM price_records
                       WHERE product_id = p.id AND platform = f.platform
                       ORDER BY recorded_at DESC LIMIT 1) as latest_price
               FROM favorites f
               JOIN products p ON f.product_id = p.id
               ORDER BY f.added_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def remove_favorite(fav_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM favorites WHERE id=?", (fav_id,))
        conn.commit()
    finally:
        conn.close()


def add_search_history(query):
    conn = get_db()
    try:
        conn.execute("INSERT INTO search_history (query) VALUES (?)", (query,))
        conn.commit()
    finally:
        conn.close()


def get_search_history(limit=20):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT query, MAX(searched_at) as searched_at FROM search_history GROUP BY query ORDER BY searched_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_product_names():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT name FROM products ORDER BY name"
        ).fetchall()
        return [r['name'] for r in rows]
    finally:
        conn.close()
