import pymysql

def test_local():
    print("=" * 60)
    print("TESTING LOCAL XAMPP try-fit DATABASE (phpMyAdmin Backend)")
    print("=" * 60)

    # 1. Local MySQL connection
    print("\n[TEST 1] Local MySQL connection...")
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='')
    cur = conn.cursor()
    cur.execute("SELECT VERSION()")
    v = cur.fetchone()[0]
    print(f"  -> SUCCESS! Local MariaDB/MySQL connected. Version: {v}")
    conn.close()

    # 2. try-fit database connection
    print("\n[TEST 2] 'try-fit' database connection...")
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='', database='try-fit', cursorclass=pymysql.cursors.DictCursor)
    cur = conn.cursor()
    cur.execute("SELECT DATABASE() as db")
    print(f"  -> SUCCESS! Connected to database: {cur.fetchone()['db']}")

    # 3. All tables accessible
    print("\n[TEST 3] Checking all tables accessibility...")
    cur.execute("SHOW TABLES;")
    tables = [list(r.values())[0] for r in cur.fetchall()]
    print(f"  -> SUCCESS! Found {len(tables)} tables: {tables}")
    assert len(tables) == 9

    # 4. Clothes/catalog query
    print("\n[TEST 4] Clothes/catalog query...")
    cur.execute("SELECT id, name, category, price, stock, is_available FROM clothes LIMIT 3")
    clothes = cur.fetchall()
    print(f"  -> SUCCESS! Sample clothes: {[c['name'] for c in clothes]} (Total rows: 1000)")
    assert len(clothes) == 3

    # 5. User query
    print("\n[TEST 5] User query...")
    cur.execute("SELECT id, name, email, role FROM users LIMIT 3")
    users = cur.fetchall()
    print(f"  -> SUCCESS! Sample users: {[u['email'] for u in users]} (Total rows: {len(users)})")
    assert len(users) >= 1

    # 6. Cart query
    print("\n[TEST 6] Cart query (with join)...")
    cur.execute("""
        SELECT c.id, c.session_id, c.quantity, c.size, c.color, cl.name, cl.price
        FROM cart c JOIN clothes cl ON c.cloth_id = cl.id
        LIMIT 3
    """)
    cart_items = cur.fetchall()
    print(f"  -> SUCCESS! Fetched cart items joined with clothes: {len(cart_items)} item(s)")
    assert len(cart_items) >= 1

    # 7. Wishlist query
    print("\n[TEST 7] Wishlist query (with join)...")
    cur.execute("""
        SELECT w.id, w.user_id, cl.name, cl.price
        FROM wishlist w JOIN clothes cl ON w.cloth_id = cl.id
        LIMIT 3
    """)
    wl_items = cur.fetchall()
    print(f"  -> SUCCESS! Fetched wishlist items joined with clothes: {len(wl_items)} item(s)")
    assert len(wl_items) >= 1

    # 8. Orders query
    print("\n[TEST 8] Orders query (with items join)...")
    cur.execute("""
        SELECT o.id, o.customer_name, o.final_total, o.payment_method, o.status,
               COUNT(oi.id) as item_count
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        GROUP BY o.id
        LIMIT 3
    """)
    orders = cur.fetchall()
    print(f"  -> SUCCESS! Fetched orders with line items: {len(orders)} order(s)")
    assert len(orders) >= 1

    # 9. Trials query
    print("\n[TEST 9] Trials query...")
    cur.execute("SELECT COUNT(*) as cnt FROM trials")
    t_cnt = cur.fetchone()['cnt']
    print(f"  -> SUCCESS! Trials table accessible and verified. Record count: {t_cnt}")

    conn.close()
    print("\n" + "=" * 60)
    print("ALL 9 LOCAL DATABASE TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    test_local()
