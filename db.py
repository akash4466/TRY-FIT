import os
import random

import pymysql
import pymysql.cursors

import config


def get_connection():
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ssl": {}}
    )


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

        if "Jeans" in category:
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
            colors
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
            available_colors
        )
        VALUES
        (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                available_colors VARCHAR(255) DEFAULT 'Black,White'
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
                total_amount DECIMAL(10, 2) NOT NULL,
                discount_amount DECIMAL(10, 2) DEFAULT 0,
                trial_charges DECIMAL(10, 2) DEFAULT 0,
                delivery_charges DECIMAL(10, 2) DEFAULT 0,
                final_total DECIMAL(10, 2) NOT NULL,
                status VARCHAR(50) DEFAULT 'Pending',
                delivery_address TEXT NOT NULL,
                payment_method VARCHAR(50) DEFAULT 'Cash on Delivery',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

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
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

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

