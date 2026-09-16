import os
import random

import pymysql
import pymysql.cursors

import config


def get_connection():
    conn_params = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
        "database": config.DB_NAME,
        "cursorclass": pymysql.cursors.DictCursor,
    }
    if getattr(config, 'DB_SSL', False):
        conn_params["ssl"] = {"ssl": {}}

    return pymysql.connect(**conn_params)


def seed_clothes(cursor):
    """
    Seed the catalog only when the clothes table is empty.
    Existing products are never deleted on restart/deployment.
    """

    cursor.execute("SELECT COUNT(*) AS count FROM clothes")
    result = cursor.fetchone()

    if result["count"] > 0:
        print(f"Clothes table already contains {result['count']} items. Skipping seed.")
        return

    def get_images(folder):
        path = os.path.join("static", "images", folder)

        if os.path.exists(path):
            files = [
                f for f in os.listdir(path)
                if f.lower().endswith(
                    (".jpg", ".png", ".jpeg", ".webp", ".avif")
                )
            ]

            if files:
                return [
                    f"/static/images/{folder}/{f}"
                    for f in files
                ]

        return ["/static/images/placeholder.svg"]

    men_imgs = get_images("men")
    women_imgs = get_images("women")
    jackets_imgs = get_images("jacket-hoddies")
    jeans_imgs = get_images("jeans")
    shoes_imgs = get_images("shoes")
    handbags_imgs = get_images("footwarehandbage")

    items = []

    # ---------------------------------------------------------
    # 1. MEN - SHIRTS & SUITS
    # ---------------------------------------------------------

    shirt_titles = [
        "Slim Fit Tuxedo Set",
        "Minimalist Summer Linen Outfit",
        "Smart Casual Chino Ensemble",
        "Velvet Evening Suit",
        "Classic Wool Blazer",
        "Casual Linen Shirt",
        "Relaxed Summer Breeze Set",
        "Pure Silk Formal Dress Shirt",
        "Heritage Italian Tailored Suit",
        "Egyptian Cotton Oxford Shirt",
        "Royal Navy Double-Breasted Suit",
        "Custom Tailored Tweed Jacket",
        "Satin Collar Dinner Jacket",
        "Lightweight Chambray Shirt",
        "Striped French Cuff Dress Shirt",
        "Cashmere Blend Formal Blazer",
        "Spread Collar Business Shirt",
        "Modern Fit Charcoal Suit",
        "Textured Weave Summer Blazer",
        "Pinstripe Executive Suit",
        "Casual Poplin Button-Down",
        "Linen-Silk Blend Summer Shirt",
        "Peak Lapel Evening Tuxedo",
        "Modern Minimalist Trench Blazer",
        "Brushed Cotton Casual Shirt"
    ]

    for i in range(50):
        name = (
            f"{shirt_titles[i % len(shirt_titles)]}"
            f"{'' if i < len(shirt_titles) else ' Edition ' + str(i // len(shirt_titles) + 1)}"
        )

        img = men_imgs[i % len(men_imgs)]
        price = 3500.00 + (i * 350.00) % 15000.00
        trial = 100.00 + (i * 10.00) % 150.00

        items.append((
            name,
            "Men – Shirts & Suits",
            round(price, 2),
            round(trial, 2),
            img
        ))

    # ---------------------------------------------------------
    # 2. MEN - JACKETS & HOODIES
    # ---------------------------------------------------------

    jacket_titles = [
        "Streetwear Denim Hoodie Jacket",
        "Thermal Insulated Puffer Jacket",
        "Classic Black Biker Leather Jacket",
        "Oversized Fleece Pullover Hoodie",
        "Sporty Windbreaker Track Jacket",
        "Tailored Corduroy Shacket",
        "Heavyweight Cotton Zip-Up Hoodie",
        "Quilted Bomber Outerwear Jacket",
        "Premium Shearling Aviator Jacket",
        "Minimalist Rainproof Parka",
        "Fleece-Lined Utility Jacket",
        "Suede Trucker Outerwear Jacket",
        "Monochrome Techwear Hoodie",
        "Heritage Wool Overcoat",
        "Down-Filled Winter Anorak",
        "Distressed Wash Denim Jacket",
        "Performance Thermal Zip Hoodie",
        "Water-Resistant Field Jacket"
    ]

    for i in range(50):
        name = (
            f"{jacket_titles[i % len(jacket_titles)]}"
            f"{'' if i < len(jacket_titles) else ' Series ' + str(i // len(jacket_titles) + 1)}"
        )

        img = jackets_imgs[i % len(jackets_imgs)]
        price = 4200.00 + (i * 280.00) % 12000.00
        trial = 110.00 + (i * 12.00) % 140.00

        items.append((
            name,
            "Men – Jackets & Hoodies",
            round(price, 2),
            round(trial, 2),
            img
        ))

    # ---------------------------------------------------------
    # 3. MEN - JEANS & TROUSERS
    # ---------------------------------------------------------

    jeans_titles = [
        "Classic Slim Fit Blue Denim",
        "Distressed Streetwear Jeans",
        "High-Rise Wide Leg Denim Trousers",
        "Raw Indigo Selvedge Jeans",
        "Relaxed Fit Cargo Denim",
        "Tapered Fit Black Wash Jeans",
        "Vintage Light Blue Straight Jeans",
        "Stretch Denim Bootcut Trousers",
        "Designer Patchwork Denim Jeans",
        "Tailored Pleated Chino Trousers",
        "Straight Leg Raw Denim",
        "Minimalist Cotton Cargo Pants",
        "Washed Black Slim Jeans",
        "Classic Corduroy Trousers",
        "Modern Cropped Denim Pants"
    ]

    for i in range(50):
        name = (
            f"{jeans_titles[i % len(jeans_titles)]}"
            f"{'' if i < len(jeans_titles) else ' Fit ' + str(i // len(jeans_titles) + 1)}"
        )

        img = jeans_imgs[i % len(jeans_imgs)]
        price = 3200.00 + (i * 220.00) % 8000.00
        trial = 90.00 + (i * 8.00) % 110.00

        items.append((
            name,
            "Men – Jeans & Trousers",
            round(price, 2),
            round(trial, 2),
            img
        ))

    # ---------------------------------------------------------
    # 4. MEN - SHOES & FOOTWEAR
    # ---------------------------------------------------------

    shoes_titles = [
        "Handcrafted Leather Oxford Shoes",
        "Premium Suede Chelsea Boots",
        "Minimalist White Leather Sneakers",
        "High-Top Urban Streetwear Sneakers",
        "Classic Brown Leather Brogues",
        "Lightweight Running Athletic Shoes",
        "Italian Leather Penny Loafers",
        "Rugged All-Terrain Hiking Boots",
        "Monk Strap Dress Shoes",
        "Handmade Suede Derby Shoes",
        "Sleek Black Leather Loafers",
        "Vintage Court Leather Sneakers"
    ]

    for i in range(50):
        name = (
            f"{shoes_titles[i % len(shoes_titles)]}"
            f"{'' if i < len(shoes_titles) else ' Edition ' + str(i // len(shoes_titles) + 1)}"
        )

        img = shoes_imgs[i % len(shoes_imgs)]
        price = 4800.00 + (i * 310.00) % 11000.00
        trial = 120.00 + (i * 10.00) % 130.00

        items.append((
            name,
            "Men – Shoes & Footwear",
            round(price, 2),
            round(trial, 2),
            img
        ))

    # ---------------------------------------------------------
    # 5. WOMEN - DRESSES & WESTERN
    # ---------------------------------------------------------

    women_titles = [
        "Chic Floral Summer Dress",
        "Designer Party Wear Gown",
        "Satin Blouse Top",
        "Royal Silk Zari Saree",
        "Embroidered Anarkali Kurti",
        "Premium Cotton Palazzo Set",
        "Elegant Pleated Maxi Skirt",
        "Silk Evening Wrap Gown",
        "Minimalist Linen Sundress",
        "Tiered Ruffle Cocktail Dress",
        "Velvet Off-Shoulder Gown",
        "Contemporary High-Slit Dress",
        "Embellished Flare Western Top"
    ]

    for i in range(50):
        name = (
            f"{women_titles[i % len(women_titles)]}"
            f"{'' if i < len(women_titles) else ' Couture ' + str(i // len(women_titles) + 1)}"
        )

        img = women_imgs[i % len(women_imgs)]
        price = 4500.00 + (i * 380.00) % 16000.00
        trial = 110.00 + (i * 15.00) % 160.00

        items.append((
            name,
            "Women – Dresses & Western",
            round(price, 2),
            round(trial, 2),
            img
        ))

    # ---------------------------------------------------------
    # 6. WOMEN - FOOTWEAR & HANDBAGS
    # ---------------------------------------------------------

    handbag_titles = [
        "Quilted Leather Crossbody Handbag",
        "Designer Embellished Party Heels",
        "Structured Tote Handbag with Charm",
        "Strappy Stiletto Evening Sandals",
        "Handwoven Straw Summer Beach Bag",
        "Block Heel Leather Ankle Boots",
        "Metallic Clutch Evening Handbag",
        "Comfortable Slip-On Leather Mules",
        "Handcrafted Leather Tote Bag",
        "Suede Pointed-Toe Pumps",
        "Luxury Monogram Shoulder Bag",
        "Minimalist Bucket Handbag"
    ]

    for i in range(50):
        name = (
            f"{handbag_titles[i % len(handbag_titles)]}"
            f"{'' if i < len(handbag_titles) else ' Model ' + str(i // len(handbag_titles) + 1)}"
        )

        img = handbags_imgs[i % len(handbags_imgs)]
        price = 3800.00 + (i * 290.00) % 12000.00
        trial = 100.00 + (i * 10.00) % 120.00

        items.append((
            name,
            "Women – Footwear & Handbags",
            round(price, 2),
            round(trial, 2),
            img
        ))

    # ---------------------------------------------------------
    # ADD BRAND / DESCRIPTION / RATING / DISCOUNT / SIZES / COLORS
    # ---------------------------------------------------------

    brands = [
        "TRY-FIT Originals",
        "Armani Exchange",
        "Polo Ralph Lauren",
        "Tommy Hilfiger",
        "Calvin Klein",
        "Hugo Boss"
    ]

    new_items = []

    for item in items:
        name, category, price, trial, img = item

        brand = random.choice(brands)

        desc = (
            f"Experience premium comfort and luxury with this elegant "
            f"{name.lower()}. A signature piece for your collection."
        )

        rating = round(random.uniform(4.0, 5.0), 1)
        discount = random.choice([0, 0, 10, 15, 20, 25])

        sizes = "S,M,L,XL"

        if "Shoes" in category:
            sizes = "7,8,9,10,11"
        elif "Handbags" in category:
            sizes = "One Size"

        colors = "Black,White,Navy,Grey,Beige"

        if "Shirt" in category:
            colors = "Blue,Navy,White,Black,Grey"
        elif "Jeans" in category:
            colors = "Blue,Black,Grey"

        new_items.append((
            name,
            category,
            price,
            trial,
            img,
            brand,
            desc,
            rating,
            discount,
            sizes,
            colors,
            10,
            True
        ))

    cursor.executemany(
        """
        INSERT INTO clothes
        (
            name,
            category,
            price,
            trial_price,
            image_url,
            brand,
            description,
            rating,
            discount_percent,
            available_sizes,
            available_colors,
            stock,
            is_available
        )
        VALUES
        (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """,
        new_items
    )

    print("Seeded database with 300 catalog items across all categories.")


def init_db():
    """
    Create tables if they don't already exist.

    IMPORTANT:
    This function NEVER drops existing tables.
    Existing users, orders, carts, wishlists and products are preserved.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # -----------------------------------------------------
        # USERS
        # -----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                role VARCHAR(20) DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        cursor.execute(
            """
            INSERT IGNORE INTO users (name, email, role)
            VALUES ('Admin', 'admin@tryfit.com', 'admin')
            """
        )

        # -----------------------------------------------------
        # OTP VERIFICATIONS
        # -----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS otp_verifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(100) NOT NULL,
                otp VARCHAR(6) NOT NULL,
                purpose VARCHAR(20) NOT NULL,
                is_verified BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        # -----------------------------------------------------
        # SESSIONS
        # -----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR(64) PRIMARY KEY,
                user_id INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        # -----------------------------------------------------
        # CLOTHES
        # -----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clothes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(100) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                trial_price DECIMAL(10, 2) NOT NULL,
                image_url VARCHAR(255) NOT NULL,
                brand VARCHAR(100) DEFAULT 'TRY-FIT',
                description TEXT,
                rating DECIMAL(3, 1) DEFAULT 4.5,
                discount_percent INT DEFAULT 0,
                available_sizes VARCHAR(255) DEFAULT 'S,M,L,XL',
                available_colors VARCHAR(255) DEFAULT 'Black,White',
                stock INT DEFAULT 10,
                is_available BOOLEAN DEFAULT TRUE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        # -----------------------------------------------------
        # TRIALS
        # -----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trials (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                cloth_id INT NOT NULL,
                duration_days INT NOT NULL,
                trial_fee DECIMAL(10, 2) NOT NULL,
                status VARCHAR(20) DEFAULT 'trying',
                start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_date DATETIME NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (cloth_id)
                    REFERENCES clothes(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        # -----------------------------------------------------
        # CART
        # -----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cart (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(64) NOT NULL,
                cloth_id INT NOT NULL,
                size VARCHAR(20) NOT NULL,
                color VARCHAR(50) NOT NULL,
                quantity INT DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cloth_id)
                    REFERENCES clothes(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        # -----------------------------------------------------
        # WISHLIST
        # -----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS wishlist (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                cloth_id INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (cloth_id)
                    REFERENCES clothes(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        # -----------------------------------------------------
        # ORDERS
        # -----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                customer_name VARCHAR(100) NULL,
                total_amount DECIMAL(10, 2) NOT NULL,
                discount_amount DECIMAL(10, 2) DEFAULT 0,
                trial_charges DECIMAL(10, 2) DEFAULT 0,
                delivery_charges DECIMAL(10, 2) DEFAULT 0,
                final_total DECIMAL(10, 2) NOT NULL,
                status VARCHAR(50) DEFAULT 'Pending',
                delivery_address TEXT NOT NULL,
                payment_method VARCHAR(50) DEFAULT 'Cash on Delivery',
                razorpay_order_id VARCHAR(255) NULL,
                razorpay_payment_id VARCHAR(255) NULL,
                razorpay_signature VARCHAR(255) NULL,
                payment_status ENUM('created', 'pending', 'paid', 'failed', 'captured') DEFAULT 'created',
                payment_verified_at DATETIME NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_orders_user_id (user_id),
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        # Migration: Ensure Razorpay and customer columns exist on existing orders table
        migration_columns = [
            ("customer_name", "VARCHAR(100) NULL"),
            ("razorpay_order_id", "VARCHAR(255) NULL"),
            ("razorpay_payment_id", "VARCHAR(255) NULL"),
            ("razorpay_signature", "VARCHAR(255) NULL"),
            ("payment_status", "ENUM('created', 'pending', 'paid', 'failed', 'captured') DEFAULT 'created'"),
            ("payment_verified_at", "DATETIME NULL")
        ]
        for col_name, col_type in migration_columns:
            cursor.execute(f"SHOW COLUMNS FROM orders LIKE '{col_name}'")
            col_info = cursor.fetchone()
            if not col_info:
                cursor.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}")
            elif col_name == "payment_status":
                col_type_str = str(col_info.get("Type", "")).lower()
                if "pending" not in col_type_str or "captured" not in col_type_str:
                    cursor.execute(f"ALTER TABLE orders MODIFY COLUMN {col_name} {col_type}")

        # Migration: Ensure stock and is_available columns exist on clothes table
        clothes_migrations = [
            ("stock", "INT DEFAULT 10"),
            ("is_available", "BOOLEAN DEFAULT TRUE")
        ]
        for col_name, col_type in clothes_migrations:
            cursor.execute(f"SHOW COLUMNS FROM clothes LIKE '{col_name}'")
            col_info = cursor.fetchone()
            if not col_info:
                cursor.execute(f"ALTER TABLE clothes ADD COLUMN {col_name} {col_type}")

        # Ensure default stock and is_available values are populated
        cursor.execute("UPDATE clothes SET stock = 10 WHERE stock IS NULL")
        cursor.execute("UPDATE clothes SET is_available = TRUE WHERE is_available IS NULL")

        # Color enrichment for accurate attribute searching:
        # Men's Shirts & Suits: Add Blue to available colors if not present
        cursor.execute("""
            UPDATE clothes 
            SET available_colors = 'Blue,Navy,White,Black,Grey' 
            WHERE (category LIKE '%Shirt%' OR name LIKE '%Shirt%') 
              AND available_colors NOT LIKE '%Blue%'
        """)

        # User-provided shoes collection
        featured_shoes = [
            ("Field Care Men Boots With PU Upper", "Men – Shoes & Footwear", 1560.00, 99.00, "/static/images/shoes/field_care_pu_boots.png", "Field Care", "Field Care Men Boots With PU Upper offering rugged durability, shock absorption, and casual streetwear styling.", 4.2, 61, "7,8,9,10,11", "Grey,Black,Red", 15, True),
            ("Woodland Men High-Top Ankle-Length Boots", "Men – Shoes & Footwear", 3117.00, 120.00, "/static/images/shoes/woodland_hightop_boots.png", "Woodland", "Authentic Woodland High-Top Ankle-Length Boots made for all-terrain adventure, hiking, and premium outdoor luxury.", 4.6, 40, "7,8,9,10,11", "Tan,Camel,Brown", 12, True),
            ("Mochi Men Round-Toe Lace-Up Boots", "Men – Shoes & Footwear", 2713.00, 110.00, "/static/images/shoes/mochi_laceup_boots.png", "Mochi", "Contemporary Mochi Round-Toe Lace-Up Boots in olive suede finish for sophisticated urban style and everyday comfort.", 4.4, 32, "7,8,9,10,11", "Olive,Green,Khaki", 10, True),
            ("Liberty Boots With Genuine Leather Upper", "Men – Shoes & Footwear", 2131.00, 105.00, "/static/images/shoes/liberty_leather_boots.png", "Liberty", "Durable Liberty Boots With Genuine Leather Upper engineered for heavy-duty performance, grip, and all-weather resilience.", 3.6, 18, "7,8,9,10,11", "Black", 14, True),
            ("Red Chief Men High-Top Boots with Lace Fastening", "Men – Shoes & Footwear", 2505.00, 115.00, "/static/images/shoes/red_chief_hightop_boots.png", "Red Chief", "Signature Red Chief Men High-Top Boots with Lace Fastening crafted in rich dark brown leather with reinforced cushioning.", 3.5, 70, "7,8,9,10,11", "Brown,Dark Brown,Chocolate", 18, True)
        ]
        for shoe in featured_shoes:
            cursor.execute("SELECT id FROM clothes WHERE name = %s", (shoe[0],))
            ex = cursor.fetchone()
            if not ex:
                cursor.execute("""
                    INSERT INTO clothes 
                    (name, category, price, trial_price, image_url, brand, description, rating, discount_percent, available_sizes, available_colors, stock, is_available)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, shoe)

        # Migration: Ensure index on orders(user_id) exists
        cursor.execute("SHOW INDEX FROM orders WHERE Column_name = 'user_id'")
        if not cursor.fetchone():
            cursor.execute("CREATE INDEX idx_orders_user_id ON orders (user_id)")

        # -----------------------------------------------------
        # ORDER ITEMS
        # -----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                cloth_id INT NOT NULL,
                quantity INT DEFAULT 1,
                price DECIMAL(10, 2) NOT NULL,
                size VARCHAR(20) NOT NULL,
                color VARCHAR(50) NOT NULL,
                FOREIGN KEY (order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (cloth_id)
                    REFERENCES clothes(id)
                    ON DELETE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        # Migration: Ensure foreign key on order_items(cloth_id) exists safely
        try:
            cursor.execute("""
                SELECT CONSTRAINT_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'order_items' AND COLUMN_NAME = 'cloth_id'
                  AND REFERENCED_TABLE_NAME = 'clothes'
            """, (config.DB_NAME,))
            if not cursor.fetchone():
                # Inspect for orphaned records without deleting any data
                cursor.execute("""
                    SELECT COUNT(*) as orphans
                    FROM order_items oi
                    LEFT JOIN clothes c ON oi.cloth_id = c.id
                    WHERE c.id IS NULL
                """)
                res = cursor.fetchone()
                if res and res.get('orphans', 0) == 0:
                    cursor.execute("""
                        ALTER TABLE order_items
                        ADD CONSTRAINT fk_order_items_cloth
                        FOREIGN KEY (cloth_id) REFERENCES clothes(id)
                        ON DELETE RESTRICT
                    """)
        except Exception as fk_err:
            print(f"Notice during foreign key verification: {fk_err}")

        conn.commit()

        # -----------------------------------------------------
        # SEED CATALOG ONLY IF EMPTY
        # -----------------------------------------------------

        seed_clothes(cursor)

        conn.commit()

        print("Database structures initialized and updated successfully.")

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    init_db()

