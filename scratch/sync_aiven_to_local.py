import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pymysql
import config

# Table creation order respecting foreign keys
TABLE_ORDER = [
    'users',
    'clothes',
    'otp_verifications',
    'sessions',
    'cart',
    'wishlist',
    'orders',
    'order_items',
    'trials'
]

# Accurate, MariaDB 10.4-compatible DDL for all 9 tables matching Aiven schema
DDL_STATEMENTS = {
    'users': """
        CREATE TABLE IF NOT EXISTS `users` (
          `id` INT NOT NULL AUTO_INCREMENT,
          `name` VARCHAR(100) NOT NULL,
          `email` VARCHAR(100) NOT NULL,
          `role` VARCHAR(20) DEFAULT 'user',
          `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          UNIQUE KEY `email` (`email`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    'clothes': """
        CREATE TABLE IF NOT EXISTS `clothes` (
          `id` INT NOT NULL AUTO_INCREMENT,
          `name` VARCHAR(100) NOT NULL,
          `category` VARCHAR(50) NOT NULL,
          `price` DECIMAL(10,2) NOT NULL,
          `trial_price` DECIMAL(10,2) NOT NULL,
          `image_url` VARCHAR(255) NOT NULL,
          `brand` VARCHAR(100) DEFAULT 'TRY-FIT',
          `description` TEXT,
          `rating` DECIMAL(3,1) DEFAULT 4.5,
          `discount_percent` INT DEFAULT 0,
          `available_sizes` VARCHAR(255) DEFAULT 'S,M,L,XL',
          `available_colors` VARCHAR(255) DEFAULT 'Black,White',
          `stock` INT DEFAULT 10,
          `is_available` TINYINT(1) DEFAULT 1,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    'otp_verifications': """
        CREATE TABLE IF NOT EXISTS `otp_verifications` (
          `id` INT NOT NULL AUTO_INCREMENT,
          `email` VARCHAR(100) NOT NULL,
          `otp` VARCHAR(6) NOT NULL,
          `purpose` VARCHAR(20) NOT NULL,
          `is_verified` TINYINT(1) DEFAULT 0,
          `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
          `expires_at` DATETIME NOT NULL,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    'sessions': """
        CREATE TABLE IF NOT EXISTS `sessions` (
          `session_id` VARCHAR(64) NOT NULL,
          `user_id` INT NOT NULL,
          `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (`session_id`),
          KEY `user_id` (`user_id`),
          CONSTRAINT `sessions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    'cart': """
        CREATE TABLE IF NOT EXISTS `cart` (
          `id` INT NOT NULL AUTO_INCREMENT,
          `session_id` VARCHAR(64) NOT NULL,
          `cloth_id` INT NOT NULL,
          `size` VARCHAR(20) NOT NULL,
          `color` VARCHAR(50) NOT NULL,
          `quantity` INT DEFAULT 1,
          `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          KEY `cloth_id` (`cloth_id`),
          CONSTRAINT `cart_ibfk_1` FOREIGN KEY (`cloth_id`) REFERENCES `clothes` (`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    'wishlist': """
        CREATE TABLE IF NOT EXISTS `wishlist` (
          `id` INT NOT NULL AUTO_INCREMENT,
          `user_id` INT DEFAULT NULL,
          `session_id` VARCHAR(64) DEFAULT NULL,
          `cloth_id` INT NOT NULL,
          `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          UNIQUE KEY `uq_wishlist_user_cloth` (`user_id`,`cloth_id`),
          KEY `cloth_id` (`cloth_id`),
          KEY `idx_wishlist_session` (`session_id`),
          KEY `idx_wishlist_user_cloth` (`user_id`,`cloth_id`),
          CONSTRAINT `wishlist_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
          CONSTRAINT `wishlist_ibfk_2` FOREIGN KEY (`cloth_id`) REFERENCES `clothes` (`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    'orders': """
        CREATE TABLE IF NOT EXISTS `orders` (
          `id` INT NOT NULL AUTO_INCREMENT,
          `user_id` INT NOT NULL,
          `total_amount` DECIMAL(10,2) NOT NULL,
          `discount_amount` DECIMAL(10,2) DEFAULT 0.00,
          `trial_charges` DECIMAL(10,2) DEFAULT 0.00,
          `delivery_charges` DECIMAL(10,2) DEFAULT 0.00,
          `final_total` DECIMAL(10,2) NOT NULL,
          `status` VARCHAR(50) DEFAULT 'Pending',
          `delivery_address` TEXT NOT NULL,
          `payment_method` VARCHAR(50) DEFAULT 'Cash on Delivery',
          `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
          `razorpay_order_id` VARCHAR(255) DEFAULT NULL,
          `razorpay_payment_id` VARCHAR(255) DEFAULT NULL,
          `razorpay_signature` VARCHAR(255) DEFAULT NULL,
          `payment_status` ENUM('created','pending','paid','failed','captured') DEFAULT 'created',
          `payment_verified_at` DATETIME DEFAULT NULL,
          `customer_name` VARCHAR(100) DEFAULT NULL,
          PRIMARY KEY (`id`),
          KEY `user_id` (`user_id`),
          CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    'order_items': """
        CREATE TABLE IF NOT EXISTS `order_items` (
          `id` INT NOT NULL AUTO_INCREMENT,
          `order_id` INT NOT NULL,
          `cloth_id` INT NOT NULL,
          `quantity` INT DEFAULT 1,
          `price` DECIMAL(10,2) NOT NULL,
          `size` VARCHAR(20) NOT NULL,
          `color` VARCHAR(50) NOT NULL,
          PRIMARY KEY (`id`),
          KEY `order_id` (`order_id`),
          KEY `cloth_id` (`cloth_id`),
          CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
          CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`cloth_id`) REFERENCES `clothes` (`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    'trials': """
        CREATE TABLE IF NOT EXISTS `trials` (
          `id` INT NOT NULL AUTO_INCREMENT,
          `user_id` INT NOT NULL,
          `cloth_id` INT NOT NULL,
          `duration_days` INT NOT NULL,
          `trial_fee` DECIMAL(10,2) NOT NULL,
          `status` VARCHAR(20) DEFAULT 'trying',
          `start_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
          `end_date` DATETIME NOT NULL,
          PRIMARY KEY (`id`),
          KEY `user_id` (`user_id`),
          KEY `cloth_id` (`cloth_id`),
          CONSTRAINT `trials_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
          CONSTRAINT `trials_ibfk_2` FOREIGN KEY (`cloth_id`) REFERENCES `clothes` (`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
}

def migrate():
    print("=" * 65)
    print("TRY-FIT DATABASE REPLICATION: AIVEN (SOURCE) -> LOCAL XAMPP (DEST)")
    print("=" * 65)

    # 1. Connect to Aiven (Strict READ-ONLY)
    print("\n[1/6] Connecting to Aiven MySQL 8.4.8 (SOURCE)...")
    aiven_conn = pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        ssl={'ssl': {}} if config.DB_SSL else None,
        cursorclass=pymysql.cursors.DictCursor
    )
    aiven_cur = aiven_conn.cursor()
    aiven_cur.execute("SELECT VERSION() as v, DATABASE() as d")
    src_info = aiven_cur.fetchone()
    print(f"  Connected to Source: {src_info['d']} on MySQL {src_info['v']}")

    # 2. Connect to Local XAMPP
    print("\n[2/6] Connecting to Local XAMPP MySQL/MariaDB (DESTINATION)...")
    local_conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='',
        database='try-fit',
        cursorclass=pymysql.cursors.DictCursor
    )
    local_cur = local_conn.cursor()
    local_cur.execute("SELECT VERSION() as v, DATABASE() as d")
    dest_info = local_cur.fetchone()
    print(f"  Connected to Destination: {dest_info['d']} on {dest_info['v']}")

    # 3. Verify destination is empty
    print("\n[3/6] Verifying Local Destination Database is Empty...")
    local_cur.execute("SHOW TABLES;")
    existing_tables = [list(r.values())[0] for r in local_cur.fetchall()]
    if existing_tables:
        print(f"  SAFETY STOP: Local database is NOT empty! Found tables: {existing_tables}")
        print("  Aborting replication to prevent accidental data loss.")
        aiven_conn.close()
        local_conn.close()
        return False
    print("  Local database is confirmed EMPTY (0 tables). Safe to proceed.")

    # 4. Create Tables in Local Database
    print("\n[4/6] Creating 9 Tables in Local Database...")
    for t in TABLE_ORDER:
        ddl = DDL_STATEMENTS[t]
        local_cur.execute(ddl)
        print(f"  Created table `{t}`")
    local_conn.commit()

    # 5. Extract Data from Aiven and Load into Local
    print("\n[5/6] Extracting Data from Aiven & Importing into Local...")
    local_cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
    
    total_records_copied = 0
    for t in TABLE_ORDER:
        # Read from Aiven
        aiven_cur.execute(f"SELECT * FROM `{t}`")
        rows = aiven_cur.fetchall()
        
        if rows:
            columns = list(rows[0].keys())
            cols_quoted = ", ".join(f"`{c}`" for c in columns)
            placeholders = ", ".join(["%s"] * len(columns))
            insert_sql = f"INSERT INTO `{t}` ({cols_quoted}) VALUES ({placeholders})"
            
            # Prepare row tuples
            row_data = [tuple(r[c] for c in columns) for r in rows]
            local_cur.executemany(insert_sql, row_data)
            local_conn.commit()
            print(f"  Imported `{t}`: {len(rows)} records copied")
            total_records_copied += len(rows)
        else:
            print(f"  Imported `{t}`: 0 records (empty table on source)")

    local_cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    local_conn.commit()
    print(f"  Total records copied: {total_records_copied}")

    # 6. Verification & Comparison
    print("\n[6/6] Verifying Table Row Counts...")
    print(f"{'Table Name':<20} | {'Aiven (Source)':<15} | {'Local XAMPP':<15} | {'Status'}")
    print("-" * 65)

    all_matched = True
    for t in TABLE_ORDER:
        aiven_cur.execute(f"SELECT COUNT(*) as cnt FROM `{t}`")
        a_cnt = aiven_cur.fetchone()['cnt']
        
        local_cur.execute(f"SELECT COUNT(*) as cnt FROM `{t}`")
        l_cnt = local_cur.fetchone()['cnt']
        
        status = "MATCH" if a_cnt == l_cnt else "MISMATCH"
        if a_cnt != l_cnt:
            all_matched = False
        print(f"{t:<20} | {a_cnt:<15} | {l_cnt:<15} | {status}")

    aiven_conn.close()
    local_conn.close()

    print("=" * 65)
    if all_matched:
        print("REPLICATION COMPLETED SUCCESSFULLY! ALL DATA MATCHES 100%.")
    else:
        print("REPLICATION COMPLETED WITH WARNINGS: Some counts did not match.")
    print("=" * 65)
    return all_matched

if __name__ == "__main__":
    migrate()
