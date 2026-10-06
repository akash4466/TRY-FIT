import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import datetime
import uuid
import pymysql
import config
import db
import server

def run_tests():
    print("==================================================")
    print("TRY-FIT DATABASE TEST SUITE (MySQL 8.4.8 on Aiven)")
    print("==================================================")
    
    test_email = f"test_verify_{uuid.uuid4().hex[:8]}@tryfit.test"
    test_session_id = f"test_sess_{uuid.uuid4().hex}"
    created_user_id = None
    created_order_id = None
    created_trial_id = None
    
    # 1. Database connection
    print("\n[TEST 1] Database Connection...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() as v, DATABASE() as db, CURRENT_USER() as u")
            row = cursor.fetchone()
            print(f"  -> SUCCESS! Connected to MySQL {row['v']}, Database: {row['db']}, User: {row['u']}")
            assert "8.4" in row['v'], f"Expected MySQL 8.4, got {row['v']}"
            assert row['db'] == "defaultdb", f"Expected defaultdb, got {row['db']}"
    finally:
        conn.close()

    # 2. User registration
    print("\n[TEST 2] User Registration...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", ("Test Runner", test_email))
            created_user_id = cursor.lastrowid
            conn.commit()
            print(f"  -> SUCCESS! Registered user ID: {created_user_id}, Email: {test_email}")
            assert created_user_id > 0
    finally:
        conn.close()

    # 3. User lookup
    print("\n[TEST 3] User Lookup...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", (test_email,))
            u = cursor.fetchone()
            print(f"  -> SUCCESS! Found user: {u['name']} (ID: {u['id']}, Role: {u['role']})")
            assert u['id'] == created_user_id
    finally:
        conn.close()

    # 4. OTP record creation & verification
    print("\n[TEST 4] OTP Record Creation...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            exp = datetime.datetime.now() + datetime.timedelta(minutes=10)
            cursor.execute(
                "INSERT INTO otp_verifications (email, otp, purpose, expires_at) VALUES (%s, %s, %s, %s)",
                (test_email, "123456", "login", exp)
            )
            otp_id = cursor.lastrowid
            conn.commit()
            
            cursor.execute("SELECT * FROM otp_verifications WHERE id = %s", (otp_id,))
            otp_rec = cursor.fetchone()
            print(f"  -> SUCCESS! Created OTP verification ID {otp_id}, code {otp_rec['otp']}, purpose {otp_rec['purpose']}")
            assert otp_rec['otp'] == "123456"
    finally:
        conn.close()

    # 5. Session creation & lookup
    print("\n[TEST 5] Session Creation & Lookup...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO sessions (session_id, user_id) VALUES (%s, %s)", (test_session_id, created_user_id))
            conn.commit()
            
            cursor.execute("""
                SELECT s.session_id, u.id, u.name, u.email, u.role
                FROM sessions s JOIN users u ON s.user_id = u.id
                WHERE s.session_id = %s
            """, (test_session_id,))
            s_rec = cursor.fetchone()
            print(f"  -> SUCCESS! Validated session {s_rec['session_id'][:16]}... for user {s_rec['email']}")
            assert s_rec['id'] == created_user_id
    finally:
        conn.close()

    # 6. Clothes/catalog listing
    print("\n[TEST 6] Clothes/Catalog Listing...")
    sample_cloth_id = None
    sample_cloth_price = None
    sample_cloth_trial_price = None
    sample_category = None
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as cnt FROM clothes")
            total_clothes = cursor.fetchone()['cnt']
            cursor.execute("SELECT id, name, category, price, trial_price, stock, is_available FROM clothes LIMIT 5")
            sample_clothes = cursor.fetchall()
            sample_cloth_id = sample_clothes[0]['id']
            sample_cloth_price = sample_clothes[0]['price']
            sample_cloth_trial_price = sample_clothes[0]['trial_price']
            sample_category = sample_clothes[0]['category']
            print(f"  -> SUCCESS! Total catalog items: {total_clothes}. Sample item: '{sample_clothes[0]['name']}' (ID: {sample_cloth_id}, Price: Rs. {sample_cloth_price})")
            assert total_clothes >= 300
    finally:
        conn.close()

    # 7. Search
    print("\n[TEST 7] Search Engine Querying...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            sql, params = server.build_search_query("Suit", limit=5)
            cursor.execute(sql, params)
            search_res = cursor.fetchall()
            print(f"  -> SUCCESS! Search for 'Suit' returned {len(search_res)} items (e.g., '{search_res[0]['name']}')")
            assert len(search_res) > 0
    finally:
        conn.close()

    # 8. Category filtering
    print("\n[TEST 8] Category Filtering...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as c FROM clothes WHERE category = %s AND is_available = 1", (sample_category,))
            cat_count = cursor.fetchone()['c']
            print(f"  -> SUCCESS! Category '{sample_category}' contains {cat_count} items")
            assert cat_count > 0
    finally:
        conn.close()

    # 9. Product details
    print("\n[TEST 9] Product Details...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM clothes WHERE id = %s", (sample_cloth_id,))
            prod = cursor.fetchone()
            print(f"  -> SUCCESS! Fetched product '{prod['name']}', Brand: {prod['brand']}, Sizes: {prod['available_sizes']}, Colors: {prod['available_colors']}")
            assert prod['id'] == sample_cloth_id
    finally:
        conn.close()

    # 10. Wishlist
    print("\n[TEST 10] Wishlist Operations...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO wishlist (user_id, cloth_id) VALUES (%s, %s)", (created_user_id, sample_cloth_id))
            conn.commit()
            
            cursor.execute("SELECT cloth_id FROM wishlist WHERE user_id = %s", (created_user_id,))
            wl_items = cursor.fetchall()
            print(f"  -> SUCCESS! Wishlist has {len(wl_items)} items for user {created_user_id}")
            assert any(item['cloth_id'] == sample_cloth_id for item in wl_items)
    finally:
        conn.close()

    # 11. Cart
    print("\n[TEST 11] Cart Operations...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO cart (session_id, cloth_id, size, color, quantity) VALUES (%s, %s, %s, %s, %s)",
                (test_session_id, sample_cloth_id, "L", "Navy", 2)
            )
            cart_id = cursor.lastrowid
            conn.commit()
            
            cursor.execute("""
                SELECT c.id as cart_id, cl.name, cl.price, c.quantity, c.size, c.color
                FROM cart c JOIN clothes cl ON c.cloth_id = cl.id
                WHERE c.session_id = %s
            """, (test_session_id,))
            cart_items = cursor.fetchall()
            print(f"  -> SUCCESS! Cart has {len(cart_items)} item(s). Item: '{cart_items[0]['name']}', Qty: {cart_items[0]['quantity']}")
            assert len(cart_items) == 1
            assert cart_items[0]['quantity'] == 2
    finally:
        conn.close()

    # 12. Checkout/Order Creation
    print("\n[TEST 12] Checkout / Order Creation...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            total_amt = float(sample_cloth_price) * 2
            cursor.execute("""
                INSERT INTO orders (user_id, total_amount, final_total, delivery_address, payment_method, customer_name, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
            """, (created_user_id, total_amt, total_amt, "123 Test Street, Bangalore, Karnataka", "Cash on Delivery", "Test Runner"))
            created_order_id = cursor.lastrowid
            conn.commit()
            print(f"  -> SUCCESS! Created order ID: {created_order_id}, Total: Rs. {total_amt}")
            assert created_order_id > 0
    finally:
        conn.close()

    # 13. Order Items
    print("\n[TEST 13] Order Items Creation...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO order_items (order_id, cloth_id, quantity, price, size, color)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (created_order_id, sample_cloth_id, 2, sample_cloth_price, "L", "Navy"))
            oi_id = cursor.lastrowid
            conn.commit()
            print(f"  -> SUCCESS! Created order_item ID: {oi_id} attached to order {created_order_id}")
            assert oi_id > 0
    finally:
        conn.close()

    # 14. Trial Creation
    print("\n[TEST 14] Trial Creation...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            end_d = datetime.datetime.now() + datetime.timedelta(days=3)
            cursor.execute("""
                INSERT INTO trials (user_id, cloth_id, duration_days, trial_fee, status, start_date, end_date)
                VALUES (%s, %s, %s, %s, 'trying', CURRENT_TIMESTAMP, %s)
            """, (created_user_id, sample_cloth_id, 3, sample_cloth_trial_price, end_d))
            created_trial_id = cursor.lastrowid
            conn.commit()
            print(f"  -> SUCCESS! Created trial ID: {created_trial_id}, fee Rs. {sample_cloth_trial_price}")
            assert created_trial_id > 0
    finally:
        conn.close()

    # 15. Trial Lookup
    print("\n[TEST 15] Trial Lookup...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.id, t.status, t.trial_fee, c.name, c.image_url
                FROM trials t JOIN clothes c ON t.cloth_id = c.id
                WHERE t.user_id = %s
            """, (created_user_id,))
            trials = cursor.fetchall()
            print(f"  -> SUCCESS! Found {len(trials)} trial(s) for user {created_user_id}: '{trials[0]['name']}' (Status: {trials[0]['status']})")
            assert len(trials) == 1
    finally:
        conn.close()

    # 16. User / Order History
    print("\n[TEST 16] User / Order History...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC", (created_user_id,))
            user_orders = cursor.fetchall()
            cursor.execute("""
                SELECT oi.*, c.name, c.image_url
                FROM order_items oi JOIN clothes c ON oi.cloth_id = c.id
                WHERE oi.order_id = %s
            """, (user_orders[0]['id'],))
            order_items = cursor.fetchall()
            print(f"  -> SUCCESS! Fetched order history: {len(user_orders)} order(s), with {len(order_items)} item(s) ('{order_items[0]['name']}')")
            assert len(user_orders) == 1
            assert len(order_items) == 1
    finally:
        conn.close()

    # Safe Cleanup of Test Fixture Data
    print("\n[CLEANUP] Cleaning up safe test fixture data...")
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM otp_verifications WHERE email LIKE '%@tryfit.test'")
            cursor.execute("DELETE FROM cart WHERE session_id LIKE 'test_sess_%'")
            cursor.execute("DELETE FROM users WHERE email LIKE '%@tryfit.test'")
            conn.commit()
            print("  -> Cleaned up test user, test OTP, and associated test fixtures cleanly.")
    finally:
        conn.close()

    print("\n==================================================")
    print("ALL 16 DATABASE OPERATIONS PASSED WITH ZERO ERRORS!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
