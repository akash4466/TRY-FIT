"""
Safe, idempotent catalog expansion script for TRY-FIT.
Expands the clothing catalog to exactly 1,000 realistic and varied products.
Preserves all existing products and tables.
"""

import os
import random
import pymysql
import db


# -----------------------------------------------------------------------------
# CATEGORY DEFINITIONS & EXISTING IMAGE POOLS
# -----------------------------------------------------------------------------

CATEGORIES = [
    "Men – Shirts & Suits",
    "Men – Jackets & Hoodies",
    "Men – Jeans & Trousers",
    "Men – Shoes & Footwear",
    "Women – Dresses & Western",
    "Women – Footwear & Handbags"
]

STYLES = [
    "Casual", "Smart Casual", "Formal", "Business", "Streetwear",
    "Minimal", "Luxury", "Classic", "Contemporary", "Athletic",
    "Resort", "Party", "Festive", "Vintage", "Oversized",
    "Slim Fit", "Relaxed Fit"
]

BRANDS = [
    "Urban Thread", "Northline", "Atelier Nine", "ModeCraft",
    "Vanta Studio", "Heritage Lane", "Elevé", "Metro Form",
    "Aura Studio", "Loom & Haven", "Komorebi Studio", "Stitch & Stone"
]

COLOR_PALETTES = {
    "Men – Shirts & Suits": [
        "White,Sky Blue,Navy", "Navy,Charcoal,White", "Powder Blue,White,Grey",
        "Charcoal,Black,White", "Beige,Olive,Cream", "Pastel Pink,White,Navy",
        "Ivory,Black,Burgundy", "French Blue,White,Slate"
    ],
    "Men – Jackets & Hoodies": [
        "Black,Charcoal,Grey", "Olive Green,Tan,Black", "Navy,Grey,White",
        "Camel,Brown,Beige", "Burgundy,Charcoal,Black", "Khaki,Olive,Cream",
        "Rust,Mustard,Charcoal", "Monochrome Black,Charcoal"
    ],
    "Men – Jeans & Trousers": [
        "Indigo Blue,Washed Blue,Raw Dark", "Jet Black,Charcoal,Grey",
        "Stone Wash Blue,Light Blue", "Khaki,Beige,Olive", "Navy,Grey,Charcoal",
        "Vintage Blue,Distressed Wash", "Off-White,Cream,Beige"
    ],
    "Men – Shoes & Footwear": [
        "Black,Charcoal", "Rich Tan,Cognac,Brown", "Dark Brown,Espresso",
        "Pure White,Grey Accents", "Olive,Khaki,Black", "Navy,White,Tan"
    ],
    "Women – Dresses & Western": [
        "Emerald Green,Sage,Teal", "Blush Pink,Rose,Ivory", "Crimson Red,Burgundy,Maroon",
        "Midnight Navy,Royal Blue", "Mustard Yellow,Ochre,Gold", "Lavender,Lilac,White",
        "Classic Black,Charcoal", "Floral Multi,Pastel Beige"
    ],
    "Women – Footwear & Handbags": [
        "Nude,Tan,Camel", "Jet Black,Gold Accents", "Crimson,Burgundy,Wine",
        "Metallic Silver,Pewter", "Warm Beige,Cream,Taupe", "Rose Gold,Blush,Nude"
    ]
}

SIZE_OPTIONS = {
    "Men – Shirts & Suits": "S,M,L,XL,XXL",
    "Men – Jackets & Hoodies": "S,M,L,XL,XXL",
    "Men – Jeans & Trousers": "30,32,34,36,38",
    "Men – Shoes & Footwear": "7,8,9,10,11",
    "Women – Dresses & Western": "XS,S,M,L,XL",
    "Women – Footwear & Handbags": "One Size"
}

# -----------------------------------------------------------------------------
# NAME GENERATION COMPONENTS (Guaranteed unique and natural fashion names)
# -----------------------------------------------------------------------------

NAME_TEMPLATES = {
    "Men – Shirts & Suits": {
        "adjectives": [
            "Classic", "Urban", "Essential", "Minimalist", "Refined", "Italian", "Heritage",
            "Executive", "Sleek", "Tailored", "Signature", "Royal", "Bespoke", "Modern",
            "Textured", "Brushed", "Chambray", "Monochrome", "Luxe", "Contemporary",
            "Pinstripe", "Crisp", "Structured", "Artisanal", "Savile", "Mercerized"
        ],
        "materials": [
            "Oxford Cotton", "Pure Linen", "Silk Blend", "Egyptian Cotton", "Poplin",
            "Herringbone Wool", "Fine Twill", "Sateen", "Supima Cotton", "Seersucker",
            "Merino Wool", "Velvet", "Cashmere Blend", "Tweed", "Flannel"
        ],
        "garments": [
            "Slim Shirt", "Dress Shirt", "Mandarin Collar Shirt", "Button-Down Shirt",
            "Resort Camp Shirt", "Double-Breasted Blazer", "Two-Piece Suit", "Tuxedo Blazer",
            "Overshirt Jacket", "Tailored Blazer", "Spread Collar Shirt", "Evening Dinner Jacket",
            "Cuban Collar Shirt", "Executive Blazer", "Textured Polo", "Formal Tunic Shirt"
        ]
    },
    "Men – Jackets & Hoodies": {
        "adjectives": [
            "Thermal", "Heavyweight", "Oversized", "Waterproof", "Insulated", "Rugged",
            "Urban", "Minimal", "Techwear", "Vintage", "Quilted", "Distressed", "Tailored",
            "All-Weather", "Polar", "Windproof", "Heritage", "Sleek", "Utility", "Tactical",
            "Sherpa-Lined", "Fleece-Backed", "Field", "Alpine", "Storm", "Aviator"
        ],
        "materials": [
            "Denim", "Fleece", "Goose Down", "Lambskin Leather", "Corduroy", "Nylon Ripstop",
            "Brushed Cotton", "Softshell", "Canvas", "Waxed Cotton", "Shearling", "Suede"
        ],
        "garments": [
            "Puffer Jacket", "Pullover Hoodie", "Zip-Up Hoodie", "Biker Jacket", "Bomber Jacket",
            "Utility Parka", "Track Jacket", "Trucker Jacket", "Overcoat", "Anorak Windbreaker",
            "Shacket Outerwear", "Field Jacket", "Harrington Jacket", "Fleece Sweatshirt"
        ]
    },
    "Men – Jeans & Trousers": {
        "adjectives": [
            "Raw Selvedge", "Vintage Wash", "Tapered", "High-Rise", "Pleated", "Relaxed",
            "Stretch", "Slim Fit", "Classic", "Distressed", "Tailored", "Cropped", "Carpenter",
            "Heavyweight", "Easy-Care", "Utility", "Contemporary", "Straight Leg", "Wide Leg",
            "Clean Cut", "Fade Resistant", "Washed Charcoal", "Everyday"
        ],
        "materials": [
            "Denim", "Cotton Chino", "Corduroy", "Linen-Cotton", "Twill", "Wool Flannel",
            "Stretch Drill", "Canvas", "Gabardine", "French Terry"
        ],
        "garments": [
            "Jeans", "Chino Trousers", "Cargo Pants", "Dress Trousers", "Relaxed Slacks",
            "Workwear Dungarees", "Jogger Pants", "Pleated Pants", "Bootcut Jeans",
            "Utility Denim", "Cropped Chinos", "Drawstring Trousers"
        ]
    },
    "Men – Shoes & Footwear": {
        "adjectives": [
            "Handcrafted", "Minimalist", "High-Top", "Italian", "Classic", "Rugged", "Sleek",
            "Water-Resistant", "Air-Cushioned", "Low-Profile", "Heritage", "Perforated",
            "Burnished", "Chunky", "Contemporary", "Tailored", "Artisan", "Urban"
        ],
        "materials": [
            "Full-Grain Leather", "Suede", "Canvas", "Nubuck Leather", "Calfskin",
            "Knit Mesh", "Vachetta Leather", "Patent Leather", "Tumbled Leather"
        ],
        "garments": [
            "Oxford Shoes", "Chelsea Boots", "Court Sneakers", "Penny Loafers", "Derby Shoes",
            "Monk Strap Shoes", "Hiking Boots", "Brogue Shoes", "Chukka Boots", "Athletic Runners",
            "Slip-On Mules", "Driving Shoes", "Combat Boots", "Boat Shoes"
        ]
    },
    "Women – Dresses & Western": {
        "adjectives": [
            "Floral", "Chic", "Satin", "Pleated", "Tiered", "Bohemian", "Embroidered",
            "Off-Shoulder", "Asymmetric", "Vintage", "A-Line", "Wrap", "Couture", "Corset",
            "Minimalist", "Flared", "High-Slit", "Ruched", "Ruffled", "Draped", "Statement",
            "Sculpted", "Botanical", "Ribbed", "Ethereal", "Romantic"
        ],
        "materials": [
            "Pure Silk", "Linen", "Chiffon", "Georgette", "Velvet", "Organza", "Cotton Voile",
            "Modal Satin", "Jacquard", "Crepe", "Lace", "Tencel", "Brocade"
        ],
        "garments": [
            "Summer Midi Dress", "Evening Maxi Gown", "Cocktail Slip Dress", "Shirt Dress",
            "Wrap Blouse", "Palazzo Jumpsuit", "Peasant Top", "Flared Maxi Skirt",
            "Sundress", "Kaftan Dress", "Bodycon Mini Dress", "Tiered Ruffle Dress",
            "Blazer Dress", "Anarkali Silhouette Dress", "Kimono Wrap Top"
        ]
    },
    "Women – Footwear & Handbags": {
        "adjectives": [
            "Quilted", "Structured", "Embellished", "Minimalist", "Strappy", "Block Heel",
            "Handwoven", "Metallic", "Pointed-Toe", "Convertible", "Slouchy", "Croc-Embossed",
            "Braided", "Sleek", "Polished", "Geometric", "Vintage", "Statement", "Everyday"
        ],
        "materials": [
            "Genuine Leather", "Suede", "Straw Raffia", "Velvet", "Satin", "Vegan Leather",
            "Patent Leather", "Tweed", "Canvas", "Microfiber"
        ],
        "garments": [
            "Crossbody Bag", "Tote Bag", "Stiletto Evening Sandals", "Pointed Pumps",
            "Ankle Boots", "Clutch Evening Purse", "Shoulder Hobo Bag", "Slip-On Mules",
            "Bucket Handbag", "Espadrille Wedges", "Satchel Bag", "Platform Sandals",
            "Baguette Bag", "Chain Strap Handbag"
        ]
    }
}

# -----------------------------------------------------------------------------
# DETAILED FASHION DESCRIPTION GENERATOR
# -----------------------------------------------------------------------------

FABRICS = [
    "breathable 100% organic cotton", "luxurious pure mulberry silk", "fine Belgian linen",
    "premium combed Supima cotton", "heavyweight Japanese selvedge denim", "durable Italian full-grain leather",
    "soft brushed microfleece", "refined merino wool blend", "stretch cotton-twill",
    "rich velvet with subtle luster", "crisp Egyptian poplin", "weather-resistant ripstop canvas"
]

FITS = [
    "tailored slim fit that contours seamlessly", "relaxed silhouette providing effortless movement",
    "modern regular fit ideal for daily wear", "structured cut engineered with clean architectural lines",
    "classic straight silhouette offering timeless appeal", "oversized modern drape with drop shoulders",
    "ergonomic athletic profile built for flexible comfort"
]

OCCASIONS = [
    "boardroom presentations, formal galas, and upscale business affairs",
    "weekend brunches, gallery openings, and casual city exploration",
    "evening cocktail celebrations and refined dinner dates",
    "trans-seasonal travel, airport styling, and resort getaways",
    "smart-casual office workdays that transition smoothly into evening social gatherings",
    "outdoor adventures, road trips, and relaxed urban living",
    "festive gatherings, wedding celebrations, and milestone occasions"
]

DESIGN_DETAILS = [
    "finished with reinforced French seams, mother-of-pearl buttons, and a crisp point collar",
    "featuring a tailored interior lining, functional welt pockets, and sleek metal hardware",
    "crafted with hand-finished topstitching, flexible stretch panels, and a clean minimalist hem",
    "accentuated by subtle tonal embroidery, custom-engraved buttons, and ribbed cuffs",
    "engineered with durable concealed closures, double-needle stitching, and a contoured neckline",
    "highlighted with elegant pleating, a concealed side zip, and fluid movement through the body"
]


def generate_unique_name(category, style, existing_names, attempt=0):
    cfg = NAME_TEMPLATES[category]
    adj = random.choice(cfg["adjectives"])
    mat = random.choice(cfg["materials"])
    gmt = random.choice(cfg["garments"])

    # Generate natural combinations
    formats = [
        f"{adj} {mat} {gmt}",
        f"{style} {mat} {gmt}",
        f"{adj} {gmt}",
        f"{style} {adj} {gmt}",
        f"{adj} {gmt} in {mat}"
    ]
    candidate = random.choice(formats).strip()

    if candidate not in existing_names:
        return candidate

    # Fallback to distinct qualifiers if collided
    descriptors = ["Signature", "Edition", "Heritage", "Atelier", "Prime", "Studio", "Series", "Form", "Concept"]
    for desc in descriptors:
        variant = f"{desc} {candidate}"
        if variant not in existing_names:
            return variant
        variant2 = f"{candidate} {desc} {random.randint(10, 99)}"
        if variant2 not in existing_names:
            return variant2

    # Extra fallback with unique counter
    counter = 1
    while f"{candidate} Vol. {counter}" in existing_names:
        counter += 1
    return f"{candidate} Vol. {counter}"


def generate_description(name, category, style, brand):
    fabric = random.choice(FABRICS)
    fit = random.choice(FITS)
    details = random.choice(DESIGN_DETAILS)
    occasion = random.choice(OCCASIONS)

    return (
        f"Designed exclusively by {brand}, the {name} embodies refined {style.lower()} styling. "
        f"Crafted from {fabric}, it showcases a {fit}. The piece is {details}, "
        f"making it an indispensable addition perfectly suited for {occasion}."
    )


def get_price_and_trial(category):
    if "Shirts & Suits" in category:
        price = random.choice([
            round(random.uniform(799, 2999), 2),
            round(random.uniform(2999, 7999), 2),
            round(random.uniform(7999, 12999), 2)
        ])
    elif "Jackets & Hoodies" in category:
        price = round(random.uniform(1499, 8999), 2)
    elif "Jeans & Trousers" in category:
        price = round(random.uniform(999, 5999), 2)
    elif "Shoes & Footwear" in category:
        price = round(random.uniform(1299, 9999), 2)
    elif "Dresses & Western" in category:
        price = round(random.uniform(999, 7999), 2)
    elif "Footwear & Handbags" in category:
        price = round(random.uniform(999, 8999), 2)
    else:
        price = round(random.uniform(999, 4999), 2)

    # Trial price is typically 2% to 4% of retail, rounded sensibly between ₹79 and ₹199
    trial_raw = max(79.0, min(199.0, round(price * 0.025, 0)))
    return round(price, 2), round(trial_raw, 2)


def get_local_images(category):
    """
    Returns valid image paths for the category strictly from existing files on disk.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(base_dir, "static", "images")

    mapping = {
        "Men – Shirts & Suits": ["men"],
        "Men – Jackets & Hoodies": ["jacket-hoddies"],
        "Men – Jeans & Trousers": ["jeans"],
        "Men – Shoes & Footwear": ["shoes"],
        "Women – Dresses & Western": ["women", "kurti", "saree"],
        "Women – Footwear & Handbags": ["footwarehandbage"]
    }

    folders = mapping.get(category, ["men"])
    collected = []

    for folder in folders:
        folder_path = os.path.join(img_dir, folder)
        if os.path.exists(folder_path):
            for fname in os.listdir(folder_path):
                if fname.lower().endswith((".jpg", ".png", ".jpeg", ".webp", ".avif")):
                    rel_url = f"/static/images/{folder}/{fname}"
                    collected.append(rel_url)

    if not collected:
        collected = ["/static/images/placeholder.svg"]

    return collected


# -----------------------------------------------------------------------------
# MAIN GENERATOR FUNCTION
# -----------------------------------------------------------------------------

def expand_catalog(target_count=1000):
    print("=" * 70)
    print("TRY-FIT CATALOG EXPANSION ENGINE")
    print("=" * 70)

    conn = db.get_connection()
    cursor = conn.cursor()

    try:
        # 1. Check existing count and names
        cursor.execute("SELECT COUNT(*) AS total FROM clothes")
        initial_count = cursor.fetchone()["total"]
        print(f"[*] Current products in database: {initial_count}")

        if initial_count >= target_count:
            print(f"[+] Database already has {initial_count} products (target: {target_count}).")
            print("[+] No additional products needed. Existing records preserved.")
            return {"previous": initial_count, "added": 0, "final": initial_count}

        needed = target_count - initial_count
        print(f"[*] Products to generate & insert: {needed}")

        # Fetch existing product names into memory to prevent duplicates
        cursor.execute("SELECT id, name, category FROM clothes")
        existing_rows = cursor.fetchall()
        existing_names = {r["name"].strip() for r in existing_rows}
        existing_ids = {r["id"] for r in existing_rows}
        print(f"[*] Loaded {len(existing_names)} existing unique product names.")

        # Check existing category distribution to balance
        cursor.execute("SELECT category, COUNT(*) as cnt FROM clothes GROUP BY category")
        cat_counts = {r["category"]: r["cnt"] for r in cursor.fetchall()}
        print("[*] Current Category Distribution:")
        for cat in CATEGORIES:
            print(f"    - {cat}: {cat_counts.get(cat, 0)}")

        # Distribute the 'needed' products evenly across all categories
        target_per_cat = target_count // len(CATEGORIES)
        remainder = target_count % len(CATEGORIES)

        cat_quotas = {}
        for idx, cat in enumerate(CATEGORIES):
            curr = cat_counts.get(cat, 0)
            target_for_this = target_per_cat + (1 if idx < remainder else 0)
            cat_quotas[cat] = max(0, target_for_this - curr)

        # If any roundoff discrepancy, adjust
        total_quota = sum(cat_quotas.values())
        if total_quota < needed:
            diff = needed - total_quota
            for i in range(diff):
                cat_quotas[CATEGORIES[i % len(CATEGORIES)]] += 1
        elif total_quota > needed:
            diff = total_quota - needed
            for i in range(diff):
                cat_quotas[CATEGORIES[i % len(CATEGORIES)]] -= 1

        print("\n[*] Planned insertions per category:")
        for cat, q in cat_quotas.items():
            print(f"    - {cat}: +{q} (new total: {cat_counts.get(cat, 0) + q})")

        # Load local images per category
        cat_images = {cat: get_local_images(cat) for cat in CATEGORIES}

        # Generate products
        new_records = []
        for cat, quota in cat_quotas.items():
            imgs = cat_images[cat]
            for i in range(quota):
                style = random.choice(STYLES)
                brand = random.choice(BRANDS)
                name = generate_unique_name(cat, style, existing_names)
                existing_names.add(name)

                price, trial_price = get_price_and_trial(cat)
                img = imgs[i % len(imgs)]
                desc = generate_description(name, cat, style, brand)
                rating = round(random.uniform(3.6, 4.9), 1)
                discount = random.choice([0, 5, 10, 15, 20, 25, 30, 40])
                sizes = SIZE_OPTIONS.get(cat, "S,M,L,XL")
                colors = random.choice(COLOR_PALETTES.get(cat, ["Black,White"]))
                stock = random.randint(8, 25)
                is_available = True

                new_records.append((
                    name,
                    cat,
                    price,
                    trial_price,
                    img,
                    brand,
                    desc,
                    rating,
                    discount,
                    sizes,
                    colors,
                    stock,
                    is_available
                ))

        print(f"\n[*] Generated {len(new_records)} unique fashion product records.")
        print("[*] Inserting into database safely using parameterized SQL...")

        insert_sql = """
        INSERT INTO clothes (
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
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        cursor.executemany(insert_sql, new_records)
        conn.commit()
        print(f"[+] Successfully committed {len(new_records)} new products to the database!")

        # ---------------------------------------------------------------------
        # POST-GENERATION VALIDATION SUITE
        # ---------------------------------------------------------------------
        print("\n" + "=" * 70)
        print("RUNNING POST-GENERATION VALIDATION SUITE")
        print("=" * 70)

        # 1. Total products = exactly 1,000
        cursor.execute("SELECT COUNT(*) AS total FROM clothes")
        final_total = cursor.fetchone()["total"]
        assert final_total == target_count, f"Validation Failed: Expected {target_count}, got {final_total}"
        print(f"[PASS] 1. Total products count: {final_total} == {target_count}")

        # 2. No duplicate names
        cursor.execute("SELECT COUNT(DISTINCT name) as unique_names, COUNT(*) as total FROM clothes")
        dup_check = cursor.fetchone()
        assert dup_check["unique_names"] == dup_check["total"] == target_count, "Validation Failed: Duplicate names found!"
        print(f"[PASS] 2. Zero duplicate names (all {final_total} product names are unique)")

        # 3. Every product has a valid name and price
        cursor.execute("SELECT COUNT(*) as invalid FROM clothes WHERE name IS NULL OR TRIM(name) = '' OR price <= 0")
        assert cursor.fetchone()["invalid"] == 0, "Validation Failed: Invalid name or price detected!"
        print("[PASS] 3. Every product has a non-empty name and valid positive price")

        # 4. Every product has a category
        cursor.execute("SELECT COUNT(*) as invalid FROM clothes WHERE category IS NULL OR TRIM(category) = ''")
        assert cursor.fetchone()["invalid"] == 0, "Validation Failed: Missing category detected!"
        print("[PASS] 4. Every product has a valid category")

        # 5. Every product has a description
        cursor.execute("SELECT COUNT(*) as invalid FROM clothes WHERE description IS NULL OR TRIM(description) = ''")
        assert cursor.fetchone()["invalid"] == 0, "Validation Failed: Missing description detected!"
        print("[PASS] 5. Every product has a detailed fashion description/prompt")

        # 6. Every product has a valid image path that exists on disk
        cursor.execute("SELECT DISTINCT image_url FROM clothes")
        image_urls = [r["image_url"] for r in cursor.fetchall()]
        base_dir = os.path.dirname(os.path.abspath(__file__))
        missing_images = []
        for url in image_urls:
            # url is e.g. /static/images/men/xyz.jpg
            rel_path = url.lstrip("/").replace("/", os.sep)
            full_path = os.path.join(base_dir, rel_path)
            if not os.path.exists(full_path):
                missing_images.append(url)

        assert len(missing_images) == 0, f"Validation Failed: Found missing images on disk: {missing_images[:5]}"
        print(f"[PASS] 6. Every image URL ({len(image_urls)} distinct images) physically exists on disk")

        # 7. Existing products were preserved
        cursor.execute("SELECT COUNT(*) as preserved FROM clothes WHERE id IN (%s)" % ",".join(map(str, existing_ids)))
        preserved_cnt = cursor.fetchone()["preserved"]
        assert preserved_cnt == initial_count, "Validation Failed: Some original products were modified or deleted!"
        print(f"[PASS] 7. All {preserved_cnt} original products were 100% preserved with original IDs")

        # 8. Category Distribution
        cursor.execute("SELECT category, COUNT(*) as cnt FROM clothes GROUP BY category ORDER BY cnt DESC")
        final_cat_dist = {r["category"]: r["cnt"] for r in cursor.fetchall()}
        print("\n[*] Final Category Distribution:")
        for cat, cnt in final_cat_dist.items():
            print(f"    - {cat}: {cnt} items")

        return {
            "previous": initial_count,
            "added": len(new_records),
            "final": final_total,
            "preserved": preserved_cnt,
            "distribution": final_cat_dist
        }

    except Exception as e:
        conn.rollback()
        print(f"[!] ERROR during catalog expansion: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    expand_catalog(1000)
