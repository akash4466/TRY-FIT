import razorpay
import config
import http.server
import socketserver
import urllib.parse
import json
import os
import random
import datetime
import uuid
import http.cookies
import re
import html
import gzip
import time
import threading

import db
import sms
import config

# High-Performance In-Memory Caches
_STATIC_CACHE = {}            # filepath -> bytes
_GZIP_CACHE = {}              # filepath -> bytes
_SESSION_CACHE = {}           # session_id -> (user_dict, expire_time)
_CART_COUNT_CACHE = {}        # session_id -> (count_int, expire_time)
_WISHLIST_COUNT_CACHE = {}    # user_id -> (count_int, expire_time)
_CATALOG_CACHE = {}           # cache_key -> (catalog_html, expire_time)
_CACHE_LOCK = threading.Lock()

razorpay_client = razorpay.Client(
    auth=(config.RAZORPAY_KEY_ID, 
    config.RAZORPAY_KEY_SECRET)
)

# -------------------------------------------------------------
# ATTRIBUTE-AWARE SEARCH ENGINE
# -------------------------------------------------------------
SEARCH_COLORS = {
    'blue': ['Blue', 'Navy'],
    'navy': ['Navy', 'Blue'],
    'black': ['Black'],
    'white': ['White'],
    'grey': ['Grey', 'Gray'],
    'gray': ['Grey', 'Gray'],
    'beige': ['Beige'],
    'brown': ['Brown', 'Tan', 'Chocolate'],
    'tan': ['Tan', 'Brown', 'Camel'],
    'camel': ['Tan', 'Camel', 'Brown'],
    'chocolate': ['Chocolate', 'Brown'],
    'red': ['Red', 'Maroon'],
    'maroon': ['Maroon', 'Red'],
    'green': ['Green', 'Olive', 'Emerald'],
    'olive': ['Olive', 'Green'],
    'emerald': ['Emerald', 'Green'],
    'yellow': ['Yellow', 'Gold'],
    'pink': ['Pink'],
    'gold': ['Gold'],
    'silver': ['Silver'],
    'indigo': ['Indigo', 'Blue'],
    'khaki': ['Khaki', 'Olive', 'Beige'],
}

SEARCH_CATEGORIES = {
    'shirt': ['Shirts', 'Shirt'],
    'shirts': ['Shirts', 'Shirt'],
    'suit': ['Suits', 'Suit', 'Tuxedo', 'Blazer'],
    'suits': ['Suits', 'Suit', 'Tuxedo', 'Blazer'],
    'tuxedo': ['Tuxedo'],
    'tuxedos': ['Tuxedo'],
    'blazer': ['Blazer'],
    'blazers': ['Blazer'],
    'jacket': ['Jackets', 'Jacket'],
    'jackets': ['Jackets', 'Jacket'],
    'hoodie': ['Hoodies', 'Hoodie'],
    'hoodies': ['Hoodies', 'Hoodie'],
    'jean': ['Jeans', 'Jean', 'Denim'],
    'jeans': ['Jeans', 'Jean', 'Denim'],
    'denim': ['Denim', 'Jeans'],
    'trouser': ['Trousers', 'Trouser'],
    'trousers': ['Trousers', 'Trouser'],
    'chino': ['Chino', 'Trousers'],
    'chinos': ['Chino', 'Trousers'],
    'shoe': ['Shoes', 'Shoe', 'Footwear', 'Sneakers', 'Loafers', 'Boots'],
    'shoes': ['Shoes', 'Shoe', 'Footwear', 'Sneakers', 'Loafers', 'Boots'],
    'footwear': ['Footwear', 'Shoes', 'Boots'],
    'boot': ['Boots', 'Boot'],
    'boots': ['Boots', 'Boot'],
    'sneaker': ['Sneakers', 'Sneaker'],
    'sneakers': ['Sneakers', 'Sneaker'],
    'loafer': ['Loafers', 'Loafer'],
    'loafers': ['Loafers', 'Loafer'],
    'brogue': ['Brogues', 'Brogue'],
    'brogues': ['Brogues', 'Brogue'],
    'dress': ['Dresses', 'Dress'],
    'dresses': ['Dresses', 'Dress'],
    'saree': ['Saree', 'Sari'],
    'sarees': ['Saree', 'Sari'],
    'sari': ['Saree', 'Sari'],
    'gown': ['Gown', 'Gowns'],
    'gowns': ['Gown', 'Gowns'],
    'kurti': ['Kurti', 'Kurtis'],
    'kurtis': ['Kurti', 'Kurtis'],
    'top': ['Top', 'Tops'],
    'tops': ['Top', 'Tops'],
    'blouse': ['Blouse', 'Top'],
    'palazzo': ['Palazzo'],
    'palazzos': ['Palazzo'],
    'skirt': ['Skirt', 'Skirts'],
    'skirts': ['Skirt', 'Skirts'],
    'handbag': ['Handbags', 'Handbag'],
    'handbags': ['Handbags', 'Handbag'],
    'bag': ['Handbags', 'Bag'],
    'bags': ['Handbags', 'Bags'],
}

SEARCH_GENDERS = {
    'men': 'Men',
    'mens': "Men",
    "men's": 'Men',
    'man': 'Men',
    'male': 'Men',
    'women': 'Women',
    'womens': "Women",
    "women's": 'Women',
    'woman': 'Women',
    'female': 'Women',
    'ladies': 'Women',
    'lady': 'Women',
}

SEARCH_BRANDS = {
    'armani': 'Armani Exchange',
    'calvin': 'Calvin Klein',
    'klein': 'Calvin Klein',
    'tommy': 'Tommy Hilfiger',
    'hilfiger': 'Tommy Hilfiger',
    'polo': 'Polo Ralph Lauren',
    'ralph': 'Polo Ralph Lauren',
    'lauren': 'Polo Ralph Lauren',
    'boss': 'Hugo Boss',
    'hugo': 'Hugo Boss',
    'woodland': 'Woodland',
    'mochi': 'Mochi',
    'liberty': 'Liberty',
    'red chief': 'Red Chief',
    'redchief': 'Red Chief',
    'field care': 'Field Care',
    'fieldcare': 'Field Care',
    'tryfit': 'TRY-FIT',
    'try-fit': 'TRY-FIT',
}

SEARCH_STOPWORDS = {'a', 'an', 'the', 'in', 'on', 'for', 'of', 'with', 'and', 'or', 'cloth', 'clothes', 'piece', 'pieces', 'wear', 'item', 'items'}

def build_search_query(q, limit=None):
    q_clean = re.sub(r'[^\w\s]', ' ', q.strip().lower()) if q else ''
    tokens = [t for t in q_clean.split() if t and t not in SEARCH_STOPWORDS]

    where_clauses = ["is_available = 1 AND stock > 0"]
    params = []

    if not tokens:
        sql = "SELECT * FROM clothes WHERE is_available = 1 AND stock > 0 ORDER BY id ASC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        return sql, ()

    matched_colors = set()
    matched_categories = set()
    matched_gender = None
    matched_brands = set()

    # Multi-word brand checks
    full_str = " ".join(tokens)
    for multi_b in ['red chief', 'field care', 'calvin klein', 'tommy hilfiger', 'polo ralph', 'hugo boss', 'armani exchange']:
        if multi_b in full_str:
            target_b = SEARCH_BRANDS.get(multi_b, multi_b.title())
            matched_brands.add(target_b)
            for w in multi_b.split():
                if w in tokens:
                    tokens.remove(w)

    remaining_tokens = []
    for token in tokens:
        if token in SEARCH_COLORS:
            for c in SEARCH_COLORS[token]:
                matched_colors.add(c)
        elif token in SEARCH_CATEGORIES:
            for cat in SEARCH_CATEGORIES[token]:
                matched_categories.add(cat)
        elif token in SEARCH_GENDERS:
            matched_gender = SEARCH_GENDERS[token]
        elif token in SEARCH_BRANDS:
            matched_brands.add(SEARCH_BRANDS[token])
        else:
            remaining_tokens.append(token)

    # 1. Color filter: Strict attribute matching
    if matched_colors:
        color_subclauses = []
        for c in matched_colors:
            color_subclauses.append("(available_colors LIKE %s OR name LIKE %s)")
            params.extend([f"%{c}%", f"%{c}%"])
        where_clauses.append(f"({' OR '.join(color_subclauses)})")

    # 2. Category / Type filter: Strict category/name matching
    if matched_categories:
        cat_subclauses = []
        for cat in matched_categories:
            cat_subclauses.append("(category LIKE %s OR name LIKE %s)")
            params.extend([f"%{cat}%", f"%{cat}%"])
        where_clauses.append(f"({' OR '.join(cat_subclauses)})")

    # 3. Gender filter
    if matched_gender:
        where_clauses.append("(category LIKE %s)")
        params.append(f"%{matched_gender}%")

    # 4. Brand filter
    if matched_brands:
        brand_subclauses = []
        for b in matched_brands:
            brand_subclauses.append("(brand LIKE %s)")
            params.append(f"%{b}%")
        where_clauses.append(f"({' OR '.join(brand_subclauses)})")

    # 5. Remaining keyword tokens
    for t in remaining_tokens:
        where_clauses.append("(name LIKE %s OR category LIKE %s OR description LIKE %s)")
        params.extend([f"%{t}%", f"%{t}%", f"%{t}%"])

    sql = f"SELECT * FROM clothes WHERE {' AND '.join(where_clauses)} ORDER BY id ASC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return sql, tuple(params)

class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

class TryFitHandler(http.server.BaseHTTPRequestHandler):

    def get_post_data(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        raw_bytes = self.rfile.read(content_length)
        content_type = self.headers.get('Content-Type', '')

        if 'application/x-www-form-urlencoded' in content_type:
            parsed = urllib.parse.parse_qs(raw_bytes.decode('utf-8'))
            return {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed.items()}

        try:
            return json.loads(raw_bytes.decode('utf-8'))
        except Exception:
            parsed = urllib.parse.parse_qs(raw_bytes.decode('utf-8'))
            return {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed.items()}

    def send_json_success(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    # Alias used in some Razorpay handlers
    def send_json_response(self, data, status=200):
        self.send_json_success(data, status)

    def send_json_error(self, message, status=400):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))

    def send_html_response(self, content, status=200):
        raw_bytes = content.encode('utf-8') if isinstance(content, str) else content
        accept_encoding = self.headers.get('Accept-Encoding', '') if hasattr(self, 'headers') and self.headers else ''
        if 'gzip' in accept_encoding and len(raw_bytes) > 256:
            compressed = gzip.compress(raw_bytes, compresslevel=6)
            self.send_response(status)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Vary', 'Accept-Encoding')
            self.send_header('Content-Length', str(len(compressed)))
            self.end_headers()
            self.wfile.write(compressed)
        else:
            self.send_response(status)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(raw_bytes)))
            self.end_headers()
            self.wfile.write(raw_bytes)

    def is_form_submission(self):
        content_type = self.headers.get('Content-Type', '')
        return 'application/x-www-form-urlencoded' in content_type

    def get_current_user(self):
        cookie_header = self.headers.get('Cookie')
        if not cookie_header:
            return None

        cookies = http.cookies.SimpleCookie(cookie_header)
        if 'session_id' not in cookies:
            return None

        session_id = cookies['session_id'].value

        if session_id == 'guest' or not session_id:
            return {'id': 'guest', 'name': 'Guest', 'email': '', 'role': 'user', 'session_id': session_id}

        # Check fast in-memory session cache
        now = time.time()
        cached = _SESSION_CACHE.get(session_id)
        if cached and now < cached[1]:
            return cached[0]

        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT u.id, u.name, u.email, u.role
                    FROM sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_id = %s
                """, (session_id,))
                user = cursor.fetchone()
                if user:
                    user['session_id'] = session_id
                    with _CACHE_LOCK:
                        _SESSION_CACHE[session_id] = (user, now + 60)
                    return user
                guest_user = {'id': 'guest', 'name': 'Guest', 'email': '', 'role': 'user', 'session_id': session_id}
                with _CACHE_LOCK:
                    _SESSION_CACHE[session_id] = (guest_user, now + 60)
                return guest_user
        except Exception as e:
            print("Session validation error:", e)
            return None
        finally:
            conn.close()

    def serve_file(self, filepath, content_type):
        try:
            stat = os.stat(filepath)
            mtime = int(stat.st_mtime)
            size = stat.st_size
            etag = f'"{mtime}-{size}"'

            # HTTP 304 Not Modified check for instant browser cache hit
            if_none_match = self.headers.get('If-None-Match')
            if if_none_match and if_none_match.strip() == etag:
                self.send_response(304)
                self.send_header('ETag', etag)
                self.send_header('Cache-Control', 'public, max-age=604800, stale-while-revalidate=86400')
                self.end_headers()
                return

            # In-memory cache for static files under 2MB
            content = _STATIC_CACHE.get(filepath)
            if content is None:
                with open(filepath, 'rb') as f:
                    content = f.read()
                if size < 2 * 1024 * 1024:
                    with _CACHE_LOCK:
                        _STATIC_CACHE[filepath] = content

            # Gzip compression for text/CSS/SVG assets
            accept_encoding = self.headers.get('Accept-Encoding', '')
            is_text = content_type.startswith('text/') or content_type in ('image/svg+xml', 'application/json', 'application/javascript')

            if 'gzip' in accept_encoding and is_text and len(content) > 256:
                compressed = _GZIP_CACHE.get(filepath)
                if compressed is None:
                    compressed = gzip.compress(content, compresslevel=6)
                    if size < 2 * 1024 * 1024:
                        with _CACHE_LOCK:
                            _GZIP_CACHE[filepath] = compressed
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Encoding', 'gzip')
                self.send_header('Vary', 'Accept-Encoding')
                self.send_header('Content-Length', str(len(compressed)))
                self.send_header('ETag', etag)
                self.send_header('Cache-Control', 'public, max-age=604800, stale-while-revalidate=86400')
                self.end_headers()
                self.wfile.write(compressed)
                return

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('ETag', etag)
            self.send_header('Cache-Control', 'public, max-age=604800, stale-while-revalidate=86400')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(404, f"File not found: {e}")

    def get_cart_count(self, user):
        if not user: return 0
        session_id = user.get('session_id', '')
        if not session_id or session_id == 'guest': return 0

        now = time.time()
        cached = _CART_COUNT_CACHE.get(session_id)
        if cached and now < cached[1]:
            return cached[0]

        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT SUM(quantity) as c FROM cart WHERE session_id = %s", (session_id,))
                res = cursor.fetchone()
                count = int(res['c'] or 0)
                with _CACHE_LOCK:
                    _CART_COUNT_CACHE[session_id] = (count, now + 20)
                return count
        except Exception:
            return 0
        finally:
            conn.close()

    def get_wishlist_count(self, user):
        if not user or user['id'] == 'guest': return 0
        user_id = user['id']

        now = time.time()
        cached = _WISHLIST_COUNT_CACHE.get(user_id)
        if cached and now < cached[1]:
            return cached[0]

        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as c FROM wishlist WHERE user_id = %s", (user_id,))
                res = cursor.fetchone()
                count = int(res['c'] or 0)
                with _CACHE_LOCK:
                    _WISHLIST_COUNT_CACHE[user_id] = (count, now + 30)
                return count
        except Exception:
            return 0
        finally:
            conn.close()

    def get_user_wishlist_ids(self, user):
        """Return a set of cloth_ids that are in the user's wishlist."""
        if not user or user['id'] == 'guest': return set()
        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT cloth_id FROM wishlist WHERE user_id = %s", (user['id'],))
                rows = cursor.fetchall()
                return {str(r['cloth_id']) for r in rows}
        except Exception:
            return set()
        finally:
            conn.close()

    def get_header_html(self, user, show_back_btn=True):
        cart_count = self.get_cart_count(user)
        wishlist_count = self.get_wishlist_count(user)
        wishlist_badge = f'<span class="cart-count" id="wishlist-nav-count" style="background:#e11d48;">{wishlist_count}</span>' if wishlist_count > 0 else '<span class="cart-count" id="wishlist-nav-count" style="background:#e11d48; display:none;">0</span>'

        if user and user['id'] != 'guest':
            account_html = f"""
                    <a href="/dashboard" class="nav-link">
                        <span class="nav-link-small">Hello, {user['name']}</span>
                        <span class="nav-link-main">Dashboard</span>
                    </a>
                    <form method="POST" action="/api/logout" style="margin: 0;">
                        <button type="submit" class="btn-text" style="font-size: 0.75rem; padding: 4px 8px; border: 1px solid var(--border); border-radius: 3px; cursor: pointer;">Logout</button>
                    </form>
            """
        else:
            account_html = """
                    <a href="/account" class="nav-link">
                        <span class="nav-link-small">Hello, Guest</span>
                        <span class="nav-link-main">Sign In</span>
                    </a>
                    <a href="/account" class="nav-link">
                        <span class="nav-link-small">New User?</span>
                        <span class="nav-link-main">Create Account</span>
                    </a>
            """

        back_btn_html = ""
        current_path = getattr(self, 'path', '')
        if show_back_btn and current_path not in ("/", "", "/index", "/index.html"):
            # Determine safe back URL using Referer header (internal TRY-FIT only)
            back_url = "/"
            referer = self.headers.get("Referer") if hasattr(self, 'headers') and self.headers else None
            host = self.headers.get("Host") if hasattr(self, 'headers') and self.headers else None
            if referer and host:
                try:
                    parsed = urllib.parse.urlparse(referer)
                    if parsed.scheme in ("http", "https") and parsed.netloc == host:
                        back_url = parsed.path or "/"
                except Exception:
                    pass
            back_btn_html = f'''<button type="button" class="nav-back-btn" onclick="if(window.history.length > 1){{ window.history.back(); }} else {{ window.location.href='{back_url}'; }}" title="Go Back" aria-label="Go Back" style="all: unset; display: inline-flex; align-items: center; gap: 8px; height: 34px; padding: 0 14px 0 8px; margin-right: 12px; color: #111111; text-decoration: none; font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; background: #FFFFFF; border: 1px solid #E5E2DC; border-radius: 9999px; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; cursor: pointer; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05); transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1); flex-shrink: 0; user-select: none; box-sizing: border-box; vertical-align: middle; -webkit-appearance: none; appearance: none;">
                <span class="nav-back-icon" style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; background: #111111; color: #FFFFFF; flex-shrink: 0; transition: all 0.22s ease;">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="width: 12px; height: 12px; stroke: currentColor; stroke-width: 2.6; fill: none; transition: transform 0.22s ease;">
                        <line x1="19" y1="12" x2="5" y2="12"></line>
                        <polyline points="12 19 5 12 12 5"></polyline>
                    </svg>
                </span>
                <span class="nav-back-text" style="line-height: 1; display: inline-block;">Back</span>
            </button>'''

        return f"""
        <header class="main-header">
            <div class="container nav-wrapper">
                <div class="nav-left">
                    {back_btn_html}
                    <nav class="nav-menu">
                        <a href="/category?category=all" class="nav-menu-link">All</a>
                        <a href="/category?category=men" class="nav-menu-link">Men</a>
                        <a href="/category?category=women" class="nav-menu-link">Women</a>
                        <a href="/category?category=shirts" class="nav-menu-link">Shirts</a>
                        <a href="/category?category=jeans" class="nav-menu-link">Jeans</a>
                        <a href="/category?category=shoes" class="nav-menu-link">Shoes</a>
                        <a href="/category?category=dresses" class="nav-menu-link">Dresses</a>
                    </nav>
                </div>

                <div class="nav-center">
                    <a href="/" class="logo">TRY-FIT</a>
                </div>

                <div class="nav-right">
                    <form action="/search" method="GET" class="search-form" style="position:relative;">
                        <input type="text" name="q" placeholder="Search TRY-FIT..." class="search-input-header" style="text-align: center;" autocomplete="off">
                        <button type="submit" class="search-btn" aria-label="Search">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                        </button>
                        <div class="search-suggestions-dropdown" style="display:none;"></div>
                    </form>
                    {account_html}
                    <a href="/wishlist" class="nav-link cart-link" id="wishlist-nav-link" title="My Wishlist">
                        <div style="position:relative;">
                            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:block;"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                            {wishlist_badge}
                        </div>
                        <span class="nav-link-main">Wishlist</span>
                    </a>
                    <a href="/orders" class="nav-link">
                        <span class="nav-link-small">Returns</span>
                        <span class="nav-link-main">& Orders</span>
                    </a>
                    <a href="/cart" class="nav-link cart-link">
                        <div style="position:relative;">
                            <span class="cart-icon">🛒</span>
                            <span class="cart-count">{cart_count}</span>
                        </div>
                        <span class="nav-link-main">Cart</span>
                    </a>
                </div>
            </div>
        </header>
        """

    def get_footer_html(self):
        return """
        <footer class="main-footer">
            <div class="container">
                <div class="footer-grid">
                    <div class="footer-col">
                        <h4>TRY-FIT</h4>
                        <a href="/page?id=about">About TRY-FIT</a>
                        <a href="/page?id=story">Our Story</a>
                        <a href="/page?id=trial">Try Before You Buy</a>
                        <a href="/page?id=contact">Contact Us</a>
                    </div>
                    <div class="footer-col">
                        <h4>Customer Service</h4>
                        <a href="/page?id=help">Help</a>
                        <a href="/page?id=returns">Returns</a>
                        <a href="/page?id=trial">Trial Policy</a>
                        <a href="/page?id=shipping">Shipping</a>
                    </div>
                    <div class="footer-col">
                        <h4>Account</h4>
                        <a href="/account">My Account</a>
                        <a href="/orders">My Orders</a>
                        <a href="/dashboard">My Trials</a>
                        <a href="/wishlist">Wishlist</a>
                    </div>
                    <div class="footer-col">
                        <h4>Categories</h4>
                        <a href="/category?category=men">Men</a>
                        <a href="/category?category=women">Women</a>
                        <a href="/category?category=shirts">Shirts</a>
                        <a href="/category?category=dresses">Dresses</a>
                    </div>
                </div>
                <div class="footer-bottom">
                    &copy; 2026 TRY-FIT. All rights reserved.
                </div>
            </div>
        </footer>
        <script>
            document.addEventListener("DOMContentLoaded", function() {
                // Instant Link Prefetching on Hover & Touch (Zero Navigation Delay)
                const prefetchedUrls = new Set();
                function prefetchLink(url) {
                    if (!url || prefetchedUrls.has(url)) return;
                    try {
                        const parsed = new URL(url, window.location.origin);
                        if (parsed.origin !== window.location.origin) return;
                        if (parsed.pathname.startsWith('/api/') || parsed.pathname.startsWith('/admin') || parsed.pathname.startsWith('/static/')) return;
                        prefetchedUrls.add(url);
                        const linkTag = document.createElement('link');
                        linkTag.rel = 'prefetch';
                        linkTag.href = url;
                        document.head.appendChild(linkTag);
                    } catch(e) {}
                }

                document.querySelectorAll('a[href]').forEach(a => {
                    const href = a.getAttribute('href');
                    if (!href || href.startsWith('#') || href.startsWith('javascript') || href.startsWith('tel:') || href.startsWith('mailto:') || a.target === '_blank') return;
                    a.addEventListener('mouseenter', () => prefetchLink(a.href), { passive: true });
                    a.addEventListener('touchstart', () => prefetchLink(a.href), { passive: true });
                });

                // Scroll Animations
                const elementsToAnimate = document.querySelectorAll('section, .product-card, .category-tabs, h2, .footer-col');
                elementsToAnimate.forEach(el => el.classList.add('scroll-anim'));

                const observerOptions = {
                    threshold: 0.1,
                    rootMargin: "0px 0px -50px 0px"
                };

                const observer = new IntersectionObserver(function(entries, observer) {
                    entries.forEach(entry => {
                        if(entry.isIntersecting){
                            entry.target.classList.add('visible');
                            observer.unobserve(entry.target);
                        }
                    });
                }, observerOptions);

                document.querySelectorAll('.scroll-anim').forEach(el => {
                    observer.observe(el);
                });

                // Live Search Suggestions
                document.querySelectorAll('.search-form, .search-input-wrapper').forEach(form => {
                    const input = form.querySelector('input[name="q"]');
                    const dropdown = form.querySelector('.search-suggestions-dropdown');
                    if (!input || !dropdown) return;

                    let debounceTimer = null;
                    let selectedIndex = -1;

                    input.addEventListener('input', function() {
                        clearTimeout(debounceTimer);
                        const query = this.value.trim();
                        if (query.length < 2) {
                            dropdown.style.display = 'none';
                            dropdown.innerHTML = '';
                            selectedIndex = -1;
                            return;
                        }

                        debounceTimer = setTimeout(async () => {
                            try {
                                const res = await fetch('/api/search/suggestions?q=' + encodeURIComponent(query));
                                if (!res.ok) return;
                                const items = await res.json();
                                selectedIndex = -1;

                                if (!items || items.length === 0) {
                                    dropdown.innerHTML = '<div class="suggestion-empty"><span style="font-size:1.2rem; display:block; margin-bottom:4px;">🔍</span>No outfit is available sorry</div>';
                                    dropdown.style.display = 'block';
                                    return;
                                }

                                dropdown.innerHTML = items.map((item, idx) => `
                                    <a href="/product?id=${item.id}" class="suggestion-item" data-index="${idx}">
                                        <img src="${item.image_url}" alt="${item.name}" class="suggestion-thumb" onerror="this.src='/static/images/placeholder.svg';">
                                        <div class="suggestion-details">
                                            <span class="suggestion-title">${item.name}</span>
                                            <span class="suggestion-meta">${item.category} • ₹${Math.round(item.price).toLocaleString('en-IN')}</span>
                                            <span class="suggestion-colors">Colors: ${item.available_colors || 'Standard'}</span>
                                        </div>
                                    </a>
                                `).join('') + `
                                    <div class="suggestion-footer">
                                        <button type="button" class="btn-all-results" onclick="this.closest('form').submit();">See all results for "${query}"</button>
                                    </div>
                                `;
                                dropdown.style.display = 'block';
                            } catch (err) {
                                console.error('Error fetching suggestions:', err);
                            }
                        }, 220);
                    });

                    input.addEventListener('keydown', function(e) {
                        const items = dropdown.querySelectorAll('.suggestion-item');
                        if (!items.length || dropdown.style.display === 'none') return;

                        if (e.key === 'ArrowDown') {
                            e.preventDefault();
                            selectedIndex = (selectedIndex + 1) % items.length;
                            updateSelection(items);
                        } else if (e.key === 'ArrowUp') {
                            e.preventDefault();
                            selectedIndex = (selectedIndex - 1 + items.length) % items.length;
                            updateSelection(items);
                        } else if (e.key === 'Enter') {
                            if (selectedIndex >= 0 && items[selectedIndex]) {
                                e.preventDefault();
                                items[selectedIndex].click();
                            }
                        } else if (e.key === 'Escape') {
                            dropdown.style.display = 'none';
                        }
                    });

                    function updateSelection(items) {
                        items.forEach((item, i) => {
                            if (i === selectedIndex) {
                                item.classList.add('active');
                                item.scrollIntoView({ block: 'nearest' });
                            } else {
                                item.classList.remove('active');
                            }
                        });
                    }

                    document.addEventListener('click', function(e) {
                        if (!form.contains(e.target)) {
                            dropdown.style.display = 'none';
                        }
                    });
                });
            });
        </script>

        <script>
        /* ============================================================
           GLOBAL WISHLIST TOGGLE FUNCTION
           Used by all product cards across catalog, category, search
           ============================================================ */
        function showToast(msg, type) {
            var t = document.querySelector('.tryfit-toast');
            if (!t) {
                t = document.createElement('div');
                t.className = 'tryfit-toast';
                document.body.appendChild(t);
            }
            t.textContent = msg;
            t.style.background = type === 'error' ? '#c0392b' : '#111111';
            t.classList.add('show');
            clearTimeout(t._hideTimer);
            t._hideTimer = setTimeout(function() { t.classList.remove('show'); }, 2800);
        }

        function toggleWishlist(event, clothId, btn) {
            if (event) { event.preventDefault(); event.stopPropagation(); }
            var isWishlisted = btn.dataset.wishlisted === 'true';
            var endpoint = isWishlisted ? '/api/wishlist/remove' : '/api/wishlist/add';
            var svg = btn.querySelector('svg');

            // Optimistic UI update
            btn.dataset.wishlisted = isWishlisted ? 'false' : 'true';
            if (svg) {
                svg.setAttribute('fill', isWishlisted ? 'none' : 'var(--primary)');
                svg.setAttribute('stroke', isWishlisted ? 'currentColor' : 'var(--primary)');
            }
            btn.classList.toggle('active', !isWishlisted);

            fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({ cloth_id: String(clothId) })
            })
            .then(function(res) {
                if (res.status === 401) {
                    // Not logged in — revert and redirect
                    btn.dataset.wishlisted = isWishlisted ? 'true' : 'false';
                    if (svg) {
                        svg.setAttribute('fill', isWishlisted ? 'var(--primary)' : 'none');
                        svg.setAttribute('stroke', isWishlisted ? 'var(--primary)' : 'currentColor');
                    }
                    btn.classList.toggle('active', isWishlisted);
                    window.location.href = '/account?error=' + encodeURIComponent('Please sign in to use your Wishlist');
                    return null;
                }
                return res.json();
            })
            .then(function(data) {
                if (!data) return;
                if (data.success) {
                    var msg = isWishlisted ? 'Removed from Wishlist' : 'Added to Wishlist ♥';
                    showToast(msg);
                    // Update nav badge
                    var navBadge = document.getElementById('wishlist-nav-count');
                    if (navBadge && data.wishlist_count !== undefined) {
                        navBadge.textContent = data.wishlist_count;
                        navBadge.style.display = data.wishlist_count > 0 ? '' : 'none';
                    }
                } else {
                    // Revert on server error
                    btn.dataset.wishlisted = isWishlisted ? 'true' : 'false';
                    if (svg) {
                        svg.setAttribute('fill', isWishlisted ? 'var(--primary)' : 'none');
                        svg.setAttribute('stroke', isWishlisted ? 'var(--primary)' : 'currentColor');
                    }
                    btn.classList.toggle('active', isWishlisted);
                    showToast(data.error || 'Something went wrong', 'error');
                }
            })
            .catch(function() {
                // Revert on network error
                btn.dataset.wishlisted = isWishlisted ? 'true' : 'false';
                if (svg) {
                    svg.setAttribute('fill', isWishlisted ? 'var(--primary)' : 'none');
                    svg.setAttribute('stroke', isWishlisted ? 'var(--primary)' : 'currentColor');
                }
                btn.classList.toggle('active', isWishlisted);
                showToast('Network error. Please try again.', 'error');
            });
        }

        /* ============================================================
           SORT DROPDOWN — CLIENT-SIDE WITH 1-SECOND LUXURY ANIMATION
           Works on: index, category, search results pages
           ============================================================ */
        (function() {
            function getCardPrice(card) {
                // Extract numeric price from card text — looks for "Buy: ₹X,XXX" or "Retail: ₹X,XXX"
                var text = card.textContent || '';
                var m = text.match(/₹([₹0-9,]+)/g);
                if (m && m.length > 0) {
                    var priceStr = m[0].replace(/[₹,]/g, '');
                    var p = parseFloat(priceStr);
                    return isNaN(p) ? 0 : p;
                }
                return 0;
            }

            function getCardRating(card) {
                // Try to find rating data attribute, or default 4.5
                return parseFloat(card.dataset.rating || '4.5');
            }

            function getCardDiscount(card) {
                return parseFloat(card.dataset.discount || '0');
            }

            function getCardDate(card) {
                return parseFloat(card.dataset.cardId || card.id.replace(/\\D/g, '') || '0');
            }

            function applySort(selectEl) {
                var sortValue = selectEl.value;
                var grid = document.getElementById('catalog-container') || document.querySelector('.products-grid');
                if (!grid) return;

                var cards = Array.from(grid.querySelectorAll('.product-card'));
                if (cards.length < 2) return;

                /* --- 1. Fade-out animation overlay --- */
                grid.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                grid.style.opacity = '0.15';
                grid.style.transform = 'translateY(6px) scale(0.99)';
                grid.style.pointerEvents = 'none';

                setTimeout(function() {
                    /* --- 2. Sort cards --- */
                    cards.sort(function(a, b) {
                        if (sortValue === 'low-to-high')  return getCardPrice(a) - getCardPrice(b);
                        if (sortValue === 'high-to-low')  return getCardPrice(b) - getCardPrice(a);
                        if (sortValue === 'rating')        return getCardRating(b) - getCardRating(a);
                        if (sortValue === 'discount')      return getCardDiscount(b) - getCardDiscount(a);
                        if (sortValue === 'newest')        return getCardDate(b) - getCardDate(a);
                        // 'featured' / default — restore original DOM order
                        return parseInt(a.dataset.origIndex || '0') - parseInt(b.dataset.origIndex || '0');
                    });

                    /* --- 3. Preserve original indices for featured reset --- */
                    cards.forEach(function(c, i) {
                        if (!c.dataset.origIndex) c.dataset.origIndex = String(i);
                    });

                    /* --- 4. Re-append in sorted order --- */
                    var frag = document.createDocumentFragment();
                    cards.forEach(function(c) { frag.appendChild(c); });
                    grid.appendChild(frag);

                    /* --- 5. Fade-in with shimmer --- */
                    grid.style.opacity = '1';
                    grid.style.transform = 'translateY(0) scale(1)';
                    grid.style.pointerEvents = '';

                    // Gold shimmer on cards
                    cards.forEach(function(c, idx) {
                        setTimeout(function() {
                            c.classList.add('card-3d-shimmer');
                            setTimeout(function() { c.classList.remove('card-3d-shimmer'); }, 900);
                        }, idx * 18);
                    });
                }, 350);
            }

            function bindSortDropdowns() {
                document.querySelectorAll('.luxury-sort-dropdown').forEach(function(sel) {
                    if (sel._sortBound) return;
                    sel._sortBound = true;
                    sel.addEventListener('change', function() { applySort(this); });
                });
            }

            // Bind immediately and after DOMContentLoaded
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', bindSortDropdowns);
            } else {
                bindSortDropdowns();
            }
        })();
        </script>
        """

    def render_template(self, filepath, user=None, show_back_btn=None, **kwargs):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if show_back_btn is None:
                # Do NOT show back button on Home Page (index.html); show on all other pages
                show_back_btn = ('index.html' not in filepath and filepath != 'templates/index.html')

            # Inject Global Header and Footer
            content = content.replace('{{HEADER}}', self.get_header_html(user, show_back_btn=show_back_btn))
            content = content.replace('{{FOOTER}}', self.get_footer_html())

            for k, v in kwargs.items():
                content = content.replace(f'{{{{{k}}}}}', str(v))

            return content
        except Exception as e:
            return f"Error loading template {filepath}: {e}"

    def get_catalog_html(self, limit=None, is_guest=False, user=None):
        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                query = "SELECT * FROM clothes ORDER BY id ASC"
                if limit is not None:
                    query += f" LIMIT {int(limit)}"
                cursor.execute(query)
                items = cursor.fetchall()

            if not items:
                return '<div class="empty-trials"><p>No clothing items available right now.</p></div>'

            # Get wishlist IDs for the current user to mark wishlisted items
            wishlisted_ids = self.get_user_wishlist_ids(user) if user else set()

            cards = []
            for item in items:
                price_int = int(float(item['price']))
                trial_int = int(float(item['trial_price']))
                is_wishlisted = str(item['id']) in wishlisted_ids

                if is_guest:
                    category_html = "Premium Catalog"
                    name_html = "Exclusive Piece"
                    pricing_html = f'<span class="buy-price" style="font-weight: 600; font-size: 1.1rem; color: var(--primary);">Retail: ₹{price_int:,}</span>'
                    btn_text = "SIGN IN TO VIEW"
                    link_href = "/account"
                    wishlist_btn = ''
                else:
                    category_html = item['category']
                    name_html = item['name']
                    pricing_html = f'<span class="buy-price">Buy: ₹{price_int:,}</span><span class="trial-price">Trial from ₹{trial_int}</span>'
                    btn_text = "TRY AT HOME"
                    link_href = f"/product?id={item['id']}"
                    heart_fill = 'var(--primary)' if is_wishlisted else 'none'
                    heart_stroke = 'var(--primary)' if is_wishlisted else 'currentColor'
                    active_class = 'active' if is_wishlisted else ''
                    wishlist_btn = f'''<button type="button" class="wishlist-btn {active_class}" 
                        data-cloth-id="{item['id']}" data-wishlisted="{'true' if is_wishlisted else 'false'}"
                        onclick="toggleWishlist(event, {item['id']}, this)" title="{'Remove from' if is_wishlisted else 'Add to'} Wishlist" aria-label="Wishlist">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="{heart_fill}" stroke="{heart_stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                    </button>'''

                cards.append(f"""
                <div class="product-card" id="product-card-{item['id']}" style="position:relative;">
                    {wishlist_btn}
                    <a href="{link_href}" style="text-decoration: none; color: inherit;">
                        <div class="product-img-wrapper">
                            <img src="{item['image_url']}" alt="{name_html}" class="product-img" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='/static/images/placeholder.svg';">
                        </div>
                        <div class="product-info">
                            <span class="product-category">{category_html}</span>
                            <h3 class="product-title">{name_html}</h3>
                            <div class="product-pricing">
                                {pricing_html}
                            </div>
                        </div>
                    </a>
                    <div style="padding: 0 16px 16px;">
                        <a href="{link_href}" class="btn-try">{btn_text}</a>
                    </div>
                </div>
                """)
            return "\n".join(cards)
        except Exception as e:
            print("Catalog fetch error:", e)
            return '<div class="empty-state"><p>Error loading catalog items.</p></div>'
        finally:
            conn.close()

    def get_trials_html_and_count(self, user_id):
        if user_id == 'guest':
            return '<div class="empty-state"><h3>No trials yet</h3><p>Your first TRY-FIT experience starts here.</p><a href="/#shop" class="btn-primary">Explore Collection</a></div>', 0, 0, 0

        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT t.id, t.cloth_id, t.duration_days, t.trial_fee, t.status,
                           t.start_date, t.end_date, c.name, c.category, c.image_url, c.price as retail_price
                    FROM trials t
                    JOIN clothes c ON t.cloth_id = c.id
                    WHERE t.user_id = %s
                    ORDER BY t.start_date DESC
                """, (user_id,))
                trials = cursor.fetchall()

            active_trials = [t for t in trials if t['status'] == 'trying']
            count = len(active_trials)
            bought_count = len([t for t in trials if t['status'] == 'bought'])
            returned_count = len([t for t in trials if t['status'] == 'returned'])

            if not trials:
                return '<div class="empty-state"><h3>No trials yet</h3><p>Your first TRY-FIT experience starts here.</p><a href="/#shop" class="btn-primary">Explore Collection</a></div>', count, bought_count, returned_count

            cards = []
            now = datetime.datetime.now()
            for t in trials:
                fee_int = int(float(t['trial_fee']))
                retail_int = int(float(t['retail_price']))
                delta = t['end_date'] - now
                days_left = max(0, delta.days + (1 if delta.seconds > 0 else 0)) if delta.total_seconds() > 0 else 0

                status_badge = f'<span class="trial-status status-active">Active Trial ({days_left}d left)</span>'
                if t['status'] == 'bought':
                    status_badge = '<span class="trial-status status-bought">Purchased & Kept</span>'
                elif t['status'] == 'returned':
                    status_badge = '<span class="trial-status status-returned">Returned</span>'

                actions_html = ""
                if t['status'] == 'trying':
                    actions_html = f"""
                    <div style="display: flex; gap: 12px; margin-top: 20px;">
                        <form method="POST" action="/api/action-trial" style="margin: 0;">
                            <input type="hidden" name="trial_id" value="{t['id']}">
                            <input type="hidden" name="action" value="buy">
                            <button type="submit" class="btn-primary" style="padding: 10px 20px;">Keep & Buy (₹{retail_int:,})</button>
                        </form>
                        <form method="POST" action="/api/action-trial" style="margin: 0;">
                            <input type="hidden" name="trial_id" value="{t['id']}">
                            <input type="hidden" name="action" value="return">
                            <button type="submit" class="btn-secondary" style="padding: 10px 20px;">Return Item</button>
                        </form>
                    </div>
                    """

                cards.append(f"""
                <div class="trial-card" id="trial-card-{t['id']}">
                    <img src="{t['image_url']}" alt="{t['name']}" onerror="this.onerror=null; this.src='/static/images/placeholder.svg';">
                    <div style="flex: 1; display: flex; flex-direction: column;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                            <div>
                                <span class="product-category" style="display: block;">{t['category']}</span>
                                <h3 style="font-family: var(--font-serif); font-size: 1.2rem; margin-top: 4px;">{t['name']}</h3>
                            </div>
                            {status_badge}
                        </div>
                        <div style="font-size: 0.9rem; color: var(--muted); margin-bottom: auto;">
                            <p style="margin-bottom: 4px;">Trial Fee Paid: <strong style="color: var(--primary);">₹{fee_int}</strong></p>
                            <p>Duration: <strong style="color: var(--primary);">{t['duration_days']} Days</strong></p>
                        </div>
                        {actions_html}
                    </div>
                </div>
                """)
            return "\n".join(cards), count, bought_count, returned_count
        except Exception as e:
            print("Trials fetch error:", e)
            return '<div class="empty-state"><p>Error loading trials.</p></div>', 0, 0, 0
        finally:
            conn.close()

    def get_catalog_html_by_category(self, categories, limit=None, is_guest=False, user=None):
        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                format_strings = ','.join(['%s'] * len(categories))
                query = f"SELECT * FROM clothes WHERE category IN ({format_strings}) ORDER BY id ASC"
                if limit is not None:
                    query += f" LIMIT {int(limit)}"
                cursor.execute(query, tuple(categories))
                items = cursor.fetchall()

            if not items:
                return '<div class="empty-trials"><p>No clothing items available in this category right now.</p></div>'

            # Get wishlist IDs for the current user to mark wishlisted items
            wishlisted_ids = self.get_user_wishlist_ids(user) if user else set()

            cards = []
            for item in items:
                price_int = int(float(item['price']))
                trial_int = int(float(item['trial_price']))
                is_wishlisted = str(item['id']) in wishlisted_ids

                if is_guest:
                    category_html = "Premium Catalog"
                    name_html = "Exclusive Piece"
                    pricing_html = f'<span class="buy-price" style="font-weight: 600; font-size: 1.1rem; color: var(--primary);">Retail: ₹{price_int:,}</span>'
                    btn_text = "SIGN IN TO VIEW"
                    link_href = "/account"
                    wishlist_btn = ''
                else:
                    category_html = item['category']
                    name_html = item['name']
                    pricing_html = f'<span class="buy-price">Buy: ₹{price_int:,}</span><span class="trial-price">Trial from ₹{trial_int}</span>'
                    btn_text = "TRY AT HOME"
                    link_href = f"/product?id={item['id']}"
                    heart_fill = 'var(--primary)' if is_wishlisted else 'none'
                    heart_stroke = 'var(--primary)' if is_wishlisted else 'currentColor'
                    active_class = 'active' if is_wishlisted else ''
                    wishlist_btn = f'''<button type="button" class="wishlist-btn {active_class}" 
                        data-cloth-id="{item['id']}" data-wishlisted="{'true' if is_wishlisted else 'false'}"
                        onclick="toggleWishlist(event, {item['id']}, this)" title="{'Remove from' if is_wishlisted else 'Add to'} Wishlist" aria-label="Wishlist">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="{heart_fill}" stroke="{heart_stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                    </button>'''

                cards.append(f"""
                <div class="product-card" id="product-card-{item['id']}" style="position:relative;">
                    {wishlist_btn}
                    <a href="{link_href}" style="text-decoration: none; color: inherit;">
                        <div class="product-img-wrapper">
                            <img src="{item['image_url']}" alt="{name_html}" class="product-img" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='/static/images/placeholder.svg';">
                        </div>
                        <div class="product-info">
                            <span class="product-category">{category_html}</span>
                            <h3 class="product-title">{name_html}</h3>
                            <div class="product-pricing">
                                {pricing_html}
                            </div>
                        </div>
                    </a>
                    <div style="padding: 0 16px 16px;">
                        <a href="{link_href}" class="btn-try">{btn_text}</a>
                    </div>
                </div>
                """)
            return "\n".join(cards)
        except Exception as e:
            print("Category catalog fetch error:", e)
            return '<div class="empty-state"><p>Error loading category items.</p></div>'
        finally:
            conn.close()

    def replace_category_placeholders(self, content, limit=None, active_category='all', is_guest=False, user=None):
        # Map category keys to DB exact strings
        cat_map = {
            'men': ['Men – Shirts & Suits', 'Men - Shirts', 'Men - Suits', 'Men – Jackets & Hoodies', 'Jackets & Hoodies', 'Men – Jeans & Trousers', 'Jeans & Trousers', 'Men – Shoes & Footwear', 'Shoes & Accessories'],
            'women': ['Women – Dresses & Western', 'Women - Dresses', 'Women - Skirts', 'Women - Tops', 'Women - Sarees', 'Women - Kurtis', 'Women - Ethnic', 'Women – Footwear & Handbags', 'Footwear & Handbags'],
            'shirts': ['Men – Shirts & Suits', 'Men - Shirts', 'Men - Suits'],
            'jackets': ['Men – Jackets & Hoodies', 'Jackets & Hoodies'],
            'jeans': ['Men – Jeans & Trousers', 'Jeans & Trousers'],
            'shoes': ['Men – Shoes & Footwear', 'Shoes & Accessories'],
            'dresses': ['Women – Dresses & Western', 'Women - Dresses', 'Women - Skirts', 'Women - Tops'],
            'handbags': ['Women – Footwear & Handbags', 'Footwear & Handbags']
        }

        # Determine the HTML to inject
        if active_category in cat_map:
            catalog_html = self.get_catalog_html_by_category(cat_map[active_category], limit=limit, is_guest=is_guest, user=user)
        else:
            catalog_html = self.get_catalog_html(limit=limit, is_guest=is_guest, user=user)

        content = content.replace('{{CATALOG_GRID}}', catalog_html)

        # Set all inactive by default
        for key in ['all', 'men', 'women', 'shirts', 'jackets', 'jeans', 'shoes', 'dresses', 'handbags']:
            content = content.replace(f'{{{{CAT_ACTIVE_{key}}}}}', 'active' if key == active_category else '')

        return content

    def serve_account(self, query_params=None):
        try:
            alert_html = ""
            if query_params:
                if 'error' in query_params:
                    msg = urllib.parse.unquote(query_params['error'][0])
                    alert_html = f'<div class="toast-alert alert-error">{msg}</div>'

            content = self.render_template('templates/account.html', None, ERROR_ALERT=alert_html, INFO_ALERT='')

            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering account page: {e}")

    def serve_index(self, query_params=None):
        try:
            user = self.get_current_user()
            content = self.render_template('templates/index.html', user)

            category = query_params.get('category', ['all'])[0] if query_params else 'all'
            is_guest = (not user or user['id'] == 'guest')
            content = self.replace_category_placeholders(
                content,
                limit=20,
                active_category=category,
                is_guest=is_guest,
                user=user
            )

            alert_html = ""
            if query_params:
                if 'error' in query_params:
                    msg = urllib.parse.unquote(query_params['error'][0])
                    alert_html = f'<div class="toast-alert alert-error">{msg}</div>'
                elif 'success' in query_params:
                    msg = urllib.parse.unquote(query_params['success'][0])
                    alert_html = f'<div class="toast-alert alert-success">{msg}</div>'

            content = content.replace('{{MESSAGE_ALERT}}', alert_html)

            self.send_html_response(content, 200)

        except Exception as e:
            self.send_error(500, f"Error rendering index: {e}")

    def serve_page(self, query_params, user):
        try:
            page_id = query_params.get('id', [''])[0] if query_params else ''

            pages = {
                'about': ('About TRY-FIT', 'TRY-FIT is your ultimate luxury fashion marketplace, revolutionizing the way you shop with our exclusive "Try Before You Buy" model.'),
                'story': ('Our Story', 'Founded with a vision to eliminate the guesswork of online shopping, TRY-FIT allows you to experience the perfect fit in the comfort of your home.'),
                'trial': ('Try Before You Buy', 'Select items, book a home trial, and only pay for what you decide to keep. Enjoy a hassle-free fitting experience without the commitment.'),
                'contact': ('Contact Us', 'Reach out to our customer support team at support@tryfit.com or call 1-800-TRY-FIT for assistance.'),
                'help': ('Help Center', 'Need assistance? Browse our FAQs or contact our 24/7 support team to resolve your queries.'),
                'returns': ('Returns Policy', 'We offer an easy 30-day return policy for all purchases. Items must be unworn and in original condition with tags attached.'),
                'shipping': ('Shipping Information', 'Enjoy free expedited shipping on all orders over ₹10,000. Track your deliveries easily through the My Orders dashboard.'),
                'faq': ('Frequently Asked Questions', 'Have questions? From trial periods to payment options, find all your answers here in our comprehensive FAQ.'),
                'terms': ('Terms of Service', 'By accessing TRY-FIT, you agree to our Terms of Service outlining user responsibilities, account management, and marketplace rules.'),
                'privacy': ('Privacy Policy', 'Your privacy is our priority. Learn how TRY-FIT secures your personal data and ensures a safe shopping environment.')
            }

            title, content_text = pages.get(page_id, ('Information', 'Content coming soon.'))

            content = self.render_template('templates/page.html', user, TITLE=title, CONTENT=content_text)
            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering page: {e}")

    def serve_dashboard(self, user, query_params=None):
        try:
            content = self.render_template('templates/dashboard.html', user)

            category = query_params.get('category', ['all'])[0] if query_params else 'all'
            content = self.replace_category_placeholders(content, limit=None, active_category=category, user=user)
            content = content.replace('{{USER_NAME}}', user['name'])
            content = content.replace(
                '<div class="avatar" id="user-avatar">U</div>',
                f'<div class="avatar" id="user-avatar">{user["name"][0].upper() if user["name"] else "U"}</div>'
            )

            guest_alert = ""
            if user['id'] == 'guest':
                content = content.replace(
                    '<button type="button" class="btn-logout" id="btn-logout">Logout</button>',
                    '<a href="/" class="btn-logout" id="btn-logout" style="border-color: var(--accent); color: var(--accent); text-decoration: none; display: inline-block;">Login / Register</a>'
                )
                content = content.replace(
                    '<form method="POST" action="/api/logout">',
                    '<!-- guest no logout form -->'
                )
                guest_alert = '<div style="background: #FFF8E7; border: 1px solid #FFE0B2; color: #8D6E63; padding: 14px 20px; text-align: center; font-size: 0.95rem; margin: 20px auto; max-width: 1200px; border-radius: 10px; font-weight: 500;">👀 <strong>Guest Browsing Mode:</strong> You are exploring our catalog as a guest. To book home trials or purchase any clothing item, please <a href="/#login-section" style="color: #D81B60; font-weight: 700; text-decoration: underline;">Sign Up or Log In</a>.</div>'

            content = self.replace_category_placeholders(content)

            trials_html, trial_count, bought_count, returned_count = self.get_trials_html_and_count(user['id'])
            content = content.replace('{{TRIALS_GRID}}', trials_html)
            content = content.replace('{{TRIAL_COUNT}}', str(trial_count))
            content = content.replace('{{BOUGHT_COUNT}}', str(bought_count))
            content = content.replace('{{RETURNED_COUNT}}', str(returned_count))

            alert_html = guest_alert
            if query_params:
                if 'error' in query_params:
                    msg = urllib.parse.unquote(query_params['error'][0])
                    alert_html += f'<div class="toast-alert alert-error">{msg}</div>'
                elif 'success' in query_params:
                    msg = urllib.parse.unquote(query_params['success'][0])
                    alert_html += f'<div class="toast-alert alert-success">{msg}</div>'
            content = content.replace('{{MESSAGE_ALERT}}', alert_html)

            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering dashboard: {e}")

    def serve_verify_otp(self, query_params=None):
        try:
            email = query_params.get('email', [''])[0] if query_params else ''
            purpose = query_params.get('purpose', ['register'])[0] if query_params else 'register'
            name = query_params.get('name', [''])[0] if query_params else ''
            info_msg = urllib.parse.unquote(query_params.get('info', [''])[0]) if query_params and 'info' in query_params else ''
            error_msg = urllib.parse.unquote(query_params.get('error', [''])[0]) if query_params and 'error' in query_params else ''

            info_html = f'<div class="toast-alert alert-success" style="background: rgba(34, 197, 94, 0.1); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.2); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.9rem; text-align: center;">{info_msg}</div>' if info_msg else ''
            error_html = f'<div class="toast-alert alert-error">{error_msg}</div>' if error_msg else ''

            with open('templates/verify.html', 'r', encoding='utf-8') as f:
                content = f.read()

            content = content.replace('{{MOBILE_NUMBER}}', email)
            content = content.replace('{{PURPOSE}}', purpose)
            content = content.replace('{{NAME}}', name)
            content = content.replace('{{INFO_ALERT}}', info_html)
            content = content.replace('{{ERROR_ALERT}}', error_html)

            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering OTP verify page: {e}")

    def serve_book_trial(self, cloth_id, user):
        try:
            conn = db.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM clothes WHERE id = %s", (cloth_id,))
                cloth = cursor.fetchone()
            conn.close()

            if not cloth:
                self.send_error(404, "Clothing item not found")
                return

            with open('templates/book_trial.html', 'r', encoding='utf-8') as f:
                content = f.read()

            price_int = int(float(cloth['price']))
            trial_int = int(float(cloth['trial_price']))

            content = content.replace('{{CLOTH_ID}}', str(cloth['id']))
            content = content.replace('{{CLOTH_NAME}}', cloth['name'])
            content = content.replace('{{CLOTH_CATEGORY}}', cloth['category'])
            content = content.replace('{{CLOTH_IMAGE}}', cloth['image_url'])
            content = content.replace('{{CLOTH_PRICE}}', f"{price_int:,}")
            content = content.replace('{{TRIAL_PRICE}}', str(trial_int))
            content = content.replace('{{USER_NAME}}', user['name'] if user and 'name' in user else '')

            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering booking page: {e}")

    def serve_admin_login(self, query_params=None):
        try:
            with open('templates/admin_login.html', 'r', encoding='utf-8') as f:
                content = f.read()
            alert_html = ""
            if query_params:
                if 'error' in query_params:
                    msg = urllib.parse.unquote(query_params['error'][0])
                    alert_html = f'<div class="toast-alert alert-error">{msg}</div>'
            content = content.replace('{{MESSAGE_ALERT}}', alert_html)
            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering admin login: {e}")

    def serve_admin_dashboard(self, user, query_params=None):
        try:
            with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
                content = f.read()

            # Fetch summary data
            conn = db.get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) as c FROM users")
                    users_count = cursor.fetchone()['c']
                    cursor.execute("SELECT COUNT(*) as c FROM clothes")
                    clothes_count = cursor.fetchone()['c']
                    cursor.execute("SELECT COUNT(*) as c FROM trials WHERE status='trying'")
                    trials_count = cursor.fetchone()['c']
            finally:
                conn.close()

            content = content.replace('{{USERS_COUNT}}', str(users_count))
            content = content.replace('{{CLOTHES_COUNT}}', str(clothes_count))
            content = content.replace('{{TRIALS_COUNT}}', str(trials_count))

            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering admin dashboard: {e}")

    def serve_product(self, query_params=None, user=None):
        cloth_id = query_params.get('id', [''])[0] if query_params else ''
        selected_size = query_params.get('size', ['M'])[0] if query_params else 'M'

        if not cloth_id:
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
            return

        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM clothes WHERE id = %s", (cloth_id,))
                cloth = cursor.fetchone()

            if not cloth:
                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
                return

            price_int = int(float(cloth['price']))
            trial_int = int(float(cloth['trial_price']))

            content = self.render_template('templates/product.html', user,
                CLOTH_ID=str(cloth['id']),
                CLOTH_NAME=cloth['name'],
                CLOTH_CATEGORY=cloth['category'],
                CLOTH_IMAGE=cloth['image_url'],
                CLOTH_PRICE=f"{price_int:,}",
                TRIAL_PRICE=str(trial_int),
                CLOTH_DESCRIPTION=cloth.get('description', "Experience this piece in the comfort of your home before making a commitment. Our signature 'Try Before You Buy' service ensures the perfect fit and feel.<br><br>Choose between a 3-day or 7-day trial period. If you love it, keep it and pay the retail price. If not, simply return it with our complimentary pickup service."),
                SELECTED_SIZE=selected_size,
                SIZE_S_ACTIVE="active" if selected_size == "S" else "",
                SIZE_M_ACTIVE="active" if selected_size == "M" else "",
                SIZE_L_ACTIVE="active" if selected_size == "L" else "",
                SIZE_XL_ACTIVE="active" if selected_size == "XL" else ""
            )

            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering product: {e}")
        finally:
            conn.close()

    def handle_search_suggestions(self, query_params):
        q = query_params.get('q', [''])[0].strip() if query_params else ''
        if not q or len(q) < 1:
            self.send_json_success([])
            return

        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                sql, params = build_search_query(q, limit=6)
                cursor.execute(sql, params)
                items = cursor.fetchall()
                results = []
                for item in items:
                    results.append({
                        'id': item['id'],
                        'name': item['name'].strip(),
                        'category': item['category'],
                        'price': float(item['price']),
                        'trial_price': float(item['trial_price']),
                        'image_url': item['image_url'],
                        'available_colors': item.get('available_colors', '')
                    })
                self.send_json_success(results)
        except Exception as e:
            self.send_json_error(f"Suggestion error: {str(e)}", 500)
        finally:
            conn.close()

    def serve_search(self, query_params=None, user=None):
        q = query_params.get('q', [''])[0].strip() if query_params else ''
        sort_param = query_params.get('sort', ['featured'])[0] if query_params else 'featured'
        is_guest = not user or user['id'] == 'guest'

        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                # Build base search SQL
                sql, params = build_search_query(q)

                # Append server-side ORDER BY based on sort param
                sort_map = {
                    'low-to-high':  'price ASC',
                    'high-to-low':  'price DESC',
                    'rating':       'rating DESC',
                    'newest':       'id DESC',
                    'discount':     'discount_percent DESC',
                }
                order_clause = sort_map.get(sort_param, 'id ASC')
                # Replace the default ORDER BY with the user's chosen one
                sql = re.sub(r'ORDER BY \S+(?: \S+)?$', f'ORDER BY {order_clause}', sql)

                cursor.execute(sql, params)
                items = cursor.fetchall()

            # Get wishlist IDs for logged-in user
            wishlisted_ids = self.get_user_wishlist_ids(user) if user else set()

            if not items:
                sort_bar_html = ""
                catalog_html = f'''
                <div class="empty-state" style="grid-column: 1 / -1; padding: 70px 20px; text-align: center;">
                    <div style="font-size: 3.5rem; margin-bottom: 16px;">🔍</div>
                    <h3 style="font-family: var(--font-serif); font-size: 2.2rem; margin-bottom: 12px; color: var(--primary);">No outfit is available sorry</h3>
                    <p style="color: var(--muted); font-size: 1.05rem; max-width: 500px; margin: 0 auto 24px; line-height: 1.6;">
                        We couldn't find any available outfit matching "<strong>{html.escape(q)}</strong>". Try searching for specific colors (e.g. Blue, Black, Navy), categories (e.g. Shirts, Suits, Jeans, Boots), or brands.
                    </p>
                    <a href="/category?category=all" class="btn-primary" style="padding: 12px 34px; display:inline-block;">Explore All Collections</a>
                </div>
                '''
            else:
                q_escaped = html.escape(q)
                sort_options = [
                    ('featured',    'Sort: Featured'),
                    ('low-to-high', 'Price: Low to High'),
                    ('high-to-low', 'Price: High to Low'),
                    ('rating',      'Rating'),
                    ('newest',      'Newest'),
                    ('discount',    'Discount'),
                ]
                options_html = ''.join(
                    f'<option value="{v}" {"selected" if v == sort_param else ""}>{lbl}</option>'
                    for v, lbl in sort_options
                )
                sort_bar_html = f'''
                <!-- 3D Shuffle Catalog Sort Bar -->
                <div class="catalog-sort-bar">
                    <div class="catalog-sort-info">
                        <span class="catalog-sort-title">{len(items)} Matched Piece{"s" if len(items) != 1 else ""}</span>
                        <span class="sort-3d-badge">3D Interactive</span>
                    </div>
                    <div class="catalog-sort-controls">
                        <select class="luxury-sort-dropdown" id="search-sort-dropdown" aria-label="Sort products"
                            onchange="window.location.href='/search?q=' + encodeURIComponent('{q_escaped}') + '&sort=' + this.value;">
                            {options_html}
                        </select>
                    </div>
                </div>
                '''
                cards = []
                for item in items:
                    price_int = int(float(item['price']))
                    trial_int = int(float(item['trial_price']))
                    is_wishlisted = str(item['id']) in wishlisted_ids

                    if is_guest:
                        category_html = "Premium Catalog"
                        name_html = "Exclusive Piece"
                        pricing_html = f'<span class="buy-price" style="font-weight: 600; font-size: 1.1rem; color: var(--primary);">Retail: ₹{price_int:,}</span>'
                        btn_text = "SIGN IN TO VIEW"
                        link_href = "/account"
                        wishlist_btn = ''
                    else:
                        category_html = item['category']
                        name_html = item['name']
                        pricing_html = f'<span class="buy-price">Buy: ₹{price_int:,}</span><span class="trial-price">Trial from ₹{trial_int}</span>'
                        btn_text = "TRY AT HOME"
                        link_href = f"/product?id={item['id']}"
                        heart_fill = 'var(--primary)' if is_wishlisted else 'none'
                        heart_stroke = 'var(--primary)' if is_wishlisted else 'currentColor'
                        active_class = 'active' if is_wishlisted else ''
                        wishlist_btn = f'''<button type="button" class="wishlist-btn {active_class}"
                            data-cloth-id="{item['id']}" data-wishlisted="{'true' if is_wishlisted else 'false'}"
                            onclick="toggleWishlist(event, {item['id']}, this)" title="{'Remove from' if is_wishlisted else 'Add to'} Wishlist" aria-label="Wishlist">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="{heart_fill}" stroke="{heart_stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                        </button>'''

                    cards.append(f"""
                    <div class="product-card" id="product-card-{item['id']}" style="position:relative;">
                        {wishlist_btn}
                        <a href="{link_href}" style="text-decoration: none; color: inherit;">
                            <div class="product-img-wrapper">
                                <img src="{item['image_url']}" alt="{name_html}" class="product-img" loading="lazy" onerror="this.onerror=null; this.src='/static/images/placeholder.svg';">
                            </div>
                            <div class="product-info">
                                <span class="product-category">{category_html}</span>
                                <h3 class="product-title">{name_html}</h3>
                                <div class="product-pricing">
                                    {pricing_html}
                                </div>
                            </div>
                        </a>
                        <div style="padding: 0 16px 16px;">
                            <a href="{link_href}" class="btn-try">{btn_text}</a>
                        </div>
                    </div>
                    """)
                catalog_html = "\n".join(cards)

            content = self.render_template('templates/search_results.html', user, CATALOG_GRID=catalog_html, SEARCH_QUERY=html.escape(q), SORT_BAR=sort_bar_html)
            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering search: {e}")
        finally:
            conn.close()

    def serve_category(self, query_params, user):
        try:
            category = query_params.get('category', ['all'])[0] if query_params else 'all'

            with open('templates/category.html', 'r', encoding='utf-8') as f:
                content = f.read()
            content = self.replace_category_placeholders(content, limit=None, active_category=category, is_guest=(not user or user['id']=='guest'), user=user)

            # Inject Global Header and Footer
            content = content.replace('{{HEADER}}', self.get_header_html(user))
            content = content.replace('{{FOOTER}}', self.get_footer_html())
            content = content.replace('{{CATEGORY_TITLE}}', category.upper())

            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering category: {e}")

    def serve_cart(self, query_params, user):
        try:
            items = []
            total = 0
            if user:
                conn = db.get_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT c.id as cart_id, cl.name, cl.image_url, cl.price, c.quantity, c.size, c.color
                            FROM cart c JOIN clothes cl ON c.cloth_id = cl.id
                            WHERE c.session_id = %s
                        """, (user.get('session_id', ''),))
                        items = cursor.fetchall()
                        for i in items:
                            item_total = float(i['price']) * i['quantity']
                            total += item_total
                finally:
                    conn.close()

            alert_html = ""
            if query_params:
                if 'error' in query_params:
                    msg = urllib.parse.unquote(query_params['error'][0])
                    alert_html = f'<div class="toast-alert alert-error">{msg}</div>'
                elif 'success' in query_params:
                    msg = urllib.parse.unquote(query_params['success'][0])
                    alert_html = f'<div class="toast-alert alert-success">{msg}</div>'

            if items and total > 0:
                cart_items_html = ""
                for i in items:
                    cart_items_html += f"""
                    <div class="cart-item">
                        <img src="{i['image_url']}" alt="{i['name']}">
                        <div class="cart-details">
                            <h3>{i['name']}</h3>
                            <p class="cart-meta">Size: {i['size']} | Color: {i['color']}</p>
                            <p class="cart-meta">In Stock</p>
                            <div class="cart-actions">
                                <form method="POST" action="/cart/update" style="display:flex; gap:10px; align-items:center;">
                                    <input type="hidden" name="cart_id" value="{i['cart_id']}">
                                    <select name="quantity" onchange="this.form.submit()" style="padding:5px; border:1px solid var(--border);">
                                        <option value="1" {'selected' if i['quantity']==1 else ''}>Qty: 1</option>
                                        <option value="2" {'selected' if i['quantity']==2 else ''}>Qty: 2</option>
                                        <option value="3" {'selected' if i['quantity']==3 else ''}>Qty: 3</option>
                                        <option value="4" {'selected' if i['quantity']==4 else ''}>Qty: 4</option>
                                    </select>
                                    <noscript><button type="submit" class="btn-secondary" style="padding:5px 10px;">Update</button></noscript>
                                </form>
                                <span style="color:var(--border);">|</span>
                                <form method="POST" action="/cart/remove">
                                    <input type="hidden" name="cart_id" value="{i['cart_id']}">
                                    <button type="submit" class="btn-text" style="font-size:0.75rem;">Delete</button>
                                </form>
                            </div>
                        </div>
                        <div class="cart-price">₹{float(i['price']):,.2f}</div>
                    </div>
                    """

                cart_body = f"""
                <h1 style="font-family: var(--font-serif); font-size: 2.5rem; margin-bottom: 30px;">Shopping Cart</h1>
                <div class="cart-layout">
                    <!-- Items -->
                    <div>
                        {cart_items_html}
                    </div>
                    
                    <!-- Summary -->
                    <aside class="order-summary">
                        <h3 style="margin-bottom: 20px; font-family: var(--font-serif); font-size: 1.5rem;">Order Summary</h3>
                        <div class="summary-row">
                            <span>Subtotal</span>
                            <span>₹{total:,.2f}</span>
                        </div>
                        <div class="summary-row">
                            <span>Shipping</span>
                            <span>Free</span>
                        </div>
                        <div class="summary-row">
                            <span>Taxes</span>
                            <span>Calculated at checkout</span>
                        </div>
                        <div class="summary-total">
                            <span>Estimated Total</span>
                            <span>₹{total:,.2f}</span>
                        </div>
                        <a href="/checkout" class="btn-primary" style="width:100%; margin-top:20px; text-align:center; display:block;">Proceed to Checkout</a>
                    </aside>
                </div>
                """
            else:
                cart_body = """
                <div class="cart-empty-container">
                    <div class="cart-empty-icon">
                        <svg viewBox="0 0 24 24" width="68" height="68" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
                            <line x1="3" y1="6" x2="21" y2="6"></line>
                            <path d="M16 10a4 4 0 0 1-8 0"></path>
                        </svg>
                    </div>
                    <h2 style="font-family: var(--font-serif); font-size: 2.2rem; margin-top: 24px; margin-bottom: 12px; color: var(--primary);">Your cart is empty</h2>
                    <p style="color: var(--muted); font-size: 1.05rem; max-width: 480px; margin: 0 auto 32px; line-height: 1.6;">
                        Your shopping bag is waiting for its first bespoke piece. Browse our seasonal catalog to find exclusive pieces and book your home trials.
                    </p>
                    <a href="/category?category=all" class="btn-primary" style="padding: 14px 40px; font-size: 0.95rem; letter-spacing: 1.5px; text-transform: uppercase; display:inline-block;">
                        Continue Shopping
                    </a>
                </div>
                """

            content = self.render_template('templates/cart.html', user, CART_BODY=cart_body, MESSAGE_ALERT=alert_html)
            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering cart: {e}")

    def serve_checkout(self, query_params, user):
        try:
            session_id = user.get('session_id', '') if user else ''

            # Prevent access to checkout if cart has no items (check this first for all users)
            conn = db.get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT c.id as cart_id, cl.name, cl.image_url, cl.price, c.quantity, c.size, c.color
                        FROM cart c JOIN clothes cl ON c.cloth_id = cl.id
                        WHERE c.session_id = %s
                    """, (session_id,))
                    items = cursor.fetchall()

                    if not items:
                        self.send_response(303)
                        self.send_header('Location', '/cart?error=' + urllib.parse.quote("Your cart is empty. Please add items before proceeding to checkout."))
                        self.end_headers()
                        return

                    total = sum(float(i['price']) * i['quantity'] for i in items)
                    if total <= 0:
                        self.send_response(303)
                        self.send_header('Location', '/cart?error=' + urllib.parse.quote("Your cart is empty. Please add items before proceeding to checkout."))
                        self.end_headers()
                        return

                    # Require login if user is guest and cart has items
                    if not user or user.get('id') == 'guest':
                        self.send_response(303)
                        self.send_header('Location', '/account?error=' + urllib.parse.quote("Please login to proceed to checkout."))
                        self.end_headers()
                        return

                    checkout_html = ""
                    for i in items:
                        checkout_html += f"""
                        <div class="checkout-summary">
                            <img src="{i['image_url']}" alt="{i['name']}">
                            <div>
                                <h4 style="margin-bottom:10px;">{i['name']}</h4>
                                <p style="color:var(--muted); font-size:0.85rem;">Size: {i['size']} | Color: {i['color']}</p>
                                <p style="color:var(--muted); font-size:0.85rem; margin-top:5px;">Qty: {i['quantity']}</p>
                                <p style="font-weight:600; margin-top:10px;">₹{float(i['price']):,.2f}</p>
                            </div>
                        </div>
                        """
            finally:
                conn.close()

            content = self.render_template('templates/checkout.html', user, CHECKOUT_ITEMS=checkout_html, CART_TOTAL=f"₹{total:,.2f}", USER_NAME=user.get('name', ''))
            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering checkout: {e}")

    def serve_orders(self, query_params, user):
        try:
            orders_html = ""
            if user and user['id'] != 'guest':
                conn = db.get_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC", (user['id'],))
                        orders = cursor.fetchall()
                        for o in orders:
                            cursor.execute("SELECT oi.*, c.name, c.image_url FROM order_items oi JOIN clothes c ON oi.cloth_id = c.id WHERE oi.order_id = %s", (o['id'],))
                            items = cursor.fetchall()
                            items_html = ""
                            for i in items:
                                items_html += f"""
                                <div style="display:flex; gap:20px; border-bottom:1px solid var(--border); padding-bottom:15px; margin-bottom:15px;">
                                    <img src="{i['image_url']}" style="width:80px; height:100px; object-fit:cover;">
                                    <div>
                                        <h4 style="margin-bottom:5px;">{i['name']}</h4>
                                        <p style="font-size:0.85rem; color:var(--muted);">Size: {i['size']} | Color: {i['color']}</p>
                                        <p style="font-size:0.85rem; margin-top:5px;">Qty: {i['quantity']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>₹{float(i['price']):,.2f}</b></p>
                                    </div>
                                </div>
                                """
                            orders_html += f"""
                            <div class="order-card">
                                <div class="order-header">
                                    <div>
                                        <span style="display:block; color:var(--muted); margin-bottom:5px;">ORDER PLACED</span>
                                        <span>{o['created_at'].strftime('%B %d, %Y')}</span>
                                    </div>
                                    <div>
                                        <span style="display:block; color:var(--muted); margin-bottom:5px;">TOTAL</span>
                                        <span>₹{float(o['final_total']):,.2f}</span>
                                    </div>
                                    <div>
                                        <span style="display:block; color:var(--muted); margin-bottom:5px;">ORDER # {o['id']}</span>
                                        <a href="#" style="color:var(--primary); text-decoration:underline;">View Details</a>
                                    </div>
                                </div>
                                <div class="order-body">
                                    {items_html}
                                </div>
                            </div>
                            """
                finally:
                    conn.close()

            if not orders_html:
                orders_html = "<div class='empty-state'><h3>You have no previous orders.</h3><a href='/category' class='btn-primary'>Start Shopping</a></div>"

            content = self.render_template('templates/orders.html', user, ORDERS_LIST=orders_html)
            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering orders: {e}")

    def serve_wishlist(self, query_params, user):
        try:
            wishlist_html = ""
            wishlist_count = 0
            if user and user['id'] != 'guest':
                conn = db.get_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT w.id as wish_id, c.*
                            FROM wishlist w JOIN clothes c ON w.cloth_id = c.id
                            WHERE w.user_id = %s
                            ORDER BY w.id DESC
                        """, (user['id'],))
                        items = cursor.fetchall()
                        wishlist_count = len(items)
                        for i in items:
                            price_int = int(float(i['price']))
                            trial_int = int(float(i['trial_price']))
                            wishlist_html += f"""
                            <div class="product-card" id="wishlist-card-{i['wish_id']}" style="position:relative;">
                                <button type="button" class="wishlist-btn active" 
                                    data-cloth-id="{i['id']}" data-wishlisted="true" data-wish-id="{i['wish_id']}"
                                    onclick="toggleWishlist(event, {i['id']}, this)" title="Remove from Wishlist" aria-label="Remove from Wishlist">
                                    <svg viewBox="0 0 24 24" width="16" height="16" fill="var(--primary)" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                                </button>
                                <a href="/product?id={i['id']}" style="text-decoration:none; color:inherit;">
                                    <div class="product-img-wrapper">
                                        <img src="{i['image_url']}" class="product-img" alt="{i['name']}" loading="lazy" onerror="this.onerror=null;this.src='/static/images/placeholder.svg';">
                                    </div>
                                    <div class="product-info">
                                        <span class="product-category">{i['category']}</span>
                                        <h3 class="product-title">{i['name']}</h3>
                                        <div class="product-pricing">
                                            <span class="buy-price">Buy: ₹{price_int:,}</span>
                                            <span class="trial-price">Trial from ₹{trial_int}</span>
                                        </div>
                                    </div>
                                </a>
                                <div style="padding: 0 16px 16px; display:flex; gap:8px;">
                                    <a href="/product?id={i['id']}" class="btn-try" style="flex:1;">View Details</a>
                                </div>
                            </div>
                            """
                finally:
                    conn.close()
            elif not user or user['id'] == 'guest':
                wishlist_html = "<div class='empty-state' style='grid-column:1/-1; text-align:center; padding:60px 20px;'><div style='font-size:4rem; margin-bottom:16px;'>♡</div><h3 style='font-size:1.8rem; margin-bottom:12px;'>Please sign in</h3><p style='color:var(--muted); margin-bottom:24px;'>Sign in to view your saved wishlist items.</p><a href='/account' class='btn-primary' style='display:inline-block; padding:14px 40px;'>Sign In</a></div>"

            if user and user['id'] != 'guest' and not wishlist_html:
                wishlist_html = "<div class='empty-state' style='grid-column:1/-1; text-align:center; padding:60px 20px;'><div style='font-size:4rem; margin-bottom:16px;'>♡</div><h3 style='font-size:1.8rem; margin-bottom:12px;'>Your Wishlist is empty</h3><p style='color:var(--muted); margin-bottom:24px;'>Save the pieces you love and find them here.</p><a href='/category?category=all' class='btn-primary' style='display:inline-block; padding:14px 40px;'>Discover Fashion</a></div>"

            count_badge = f'<span class="wishlist-count-badge">{wishlist_count} item{"s" if wishlist_count != 1 else ""}</span>' if wishlist_count > 0 else ''
            content = self.render_template('templates/wishlist.html', user, WISHLIST_ITEMS=wishlist_html, MESSAGE_ALERT="", WISHLIST_COUNT_BADGE=count_badge)
            self.send_html_response(content, 200)
        except Exception as e:
            self.send_error(500, f"Error rendering wishlist: {e}")

    def do_HEAD(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            return

        if path.startswith('/static/'):
            filepath = path.lstrip('/')

            if not os.path.exists(filepath):
                self.send_error(404, "Asset not found")
                return

            if path.endswith('.css'):
                content_type = 'text/css'
            elif path.endswith('.jpg') or path.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif path.endswith('.png'):
                content_type = 'image/png'
            elif path.endswith('.webp'):
                content_type = 'image/webp'
            elif path.endswith('.gif'):
                content_type = 'image/gif'
            elif path.endswith('.svg'):
                content_type = 'image/svg+xml'
            elif path.endswith('.ico'):
                content_type = 'image/x-icon'
            else:
                content_type = 'application/octet-stream'

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header(
                'Content-Length',
                str(os.path.getsize(filepath))
            )
            self.end_headers()
            return

        self.send_error(404, "Page not found")
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Serve static assets
        if path.startswith('/static/'):
            filepath = path.lstrip('/')
            if not os.path.exists(filepath):
                self.send_error(404, "Asset not found")
                return

            if path.endswith('.css'):
                self.serve_file(filepath, 'text/css')
            elif path.endswith('.jpg') or path.endswith('.jpeg'):
                self.serve_file(filepath, 'image/jpeg')
            elif path.endswith('.png'):
                self.serve_file(filepath, 'image/png')
            elif path.endswith('.webp'):
                self.serve_file(filepath, 'image/webp')
            elif path.endswith('.gif'):
                self.serve_file(filepath, 'image/gif')
            elif path.endswith('.svg'):
                self.serve_file(filepath, 'image/svg+xml')
            elif path.endswith('.ico'):
                self.serve_file(filepath, 'image/x-icon')
            else:
                self.serve_file(filepath, 'application/octet-stream')
            return

        # Core routes
        if path == '/':
            self.serve_index(query_params)
            return

        elif path == '/account':
            user = self.get_current_user()
            if user and user['id'] != 'guest':
                self.send_response(303)
                self.send_header('Location', '/dashboard')
                self.end_headers()
            else:
                self.serve_account(query_params)
            return

        elif path == '/category':
            user = self.get_current_user()
            self.serve_category(query_params, user)
            return

        elif path == '/cart':
            user = self.get_current_user()
            self.serve_cart(query_params, user)
            return

        elif path == '/checkout':
            user = self.get_current_user()
            self.serve_checkout(query_params, user)
            return

        elif path == '/orders':
            user = self.get_current_user()
            self.serve_orders(query_params, user)
            return

        elif path == '/wishlist':
            user = self.get_current_user()
            self.serve_wishlist(query_params, user)
            return

        elif path == '/product':
            user = self.get_current_user()
            self.serve_product(query_params, user)
            return

        elif path == '/api/search/suggestions':
            self.handle_search_suggestions(query_params)
            return

        elif path == '/search':
            user = self.get_current_user()
            self.serve_search(query_params, user)
            return

        elif path == '/dashboard':
            user = self.get_current_user()
            if not user:
                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                self.serve_dashboard(user, query_params)
            return

        elif path == '/admin':
            self.send_response(303)
            self.send_header('Location', '/admin/dashboard')
            self.end_headers()
            return

        elif path == '/admin/login':
            user = self.get_current_user()
            if user and user.get('role') == 'admin':
                self.send_response(303)
                self.send_header('Location', '/admin/dashboard')
                self.end_headers()
            else:
                self.serve_admin_login(query_params)
            return

        elif path == '/admin/dashboard':
            user = self.get_current_user()
            if not user or user.get('role') != 'admin':
                self.send_response(303)
                self.send_header('Location', '/admin/login')
                self.end_headers()
            else:
                self.serve_admin_dashboard(user, query_params)
            return

        elif path == '/guest-login':
            self.send_response(303)
            self.send_header('Set-Cookie', 'session_id=guest; Path=/; HttpOnly; Max-Age=86400')
            self.send_header('Location', '/')
            self.end_headers()
            return

        elif path == '/verify-otp':
            self.serve_verify_otp(query_params)
            return

        elif path == '/book-trial':
            user = self.get_current_user()
            cloth_id = query_params.get('id', [''])[0] if query_params else ''
            size = query_params.get('size', ['M'])[0] if query_params else 'M'
            if not user or user['id'] == 'guest':
                msg = urllib.parse.quote("Please log in or register to book a home trial.")
                dest = '/dashboard' if user and user['id'] == 'guest' else '/'
                self.send_response(303)
                self.send_header('Location', f'{dest}?error={msg}')
                self.end_headers()
                return
            if not cloth_id:
                self.send_response(303)
                self.send_header('Location', '/dashboard')
                self.end_headers()
                return
            self.serve_book_trial(cloth_id, user)
            return

        elif path == '/logout':
            self.send_response(303)
            self.send_header('Set-Cookie', 'session_id=; Path=/; HttpOnly; Max-Age=0')
            self.send_header('Location', '/')
            self.end_headers()
            return

        # Clothes Catalog API
        elif path == '/api/clothes':
            user = self.get_current_user()
            if not user:
                self.send_json_error("Unauthorized", 401)
                return

            conn = db.get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM clothes")
                    items = cursor.fetchall()
                    for item in items:
                        item['price'] = float(item['price'])
                        item['trial_price'] = float(item['trial_price'])
                    self.send_json_success(items)
            except Exception as e:
                self.send_json_error(str(e), 500)
            finally:
                conn.close()
            return

        # Active Trials API
        elif path == '/api/trials':
            user = self.get_current_user()
            if not user:
                self.send_json_error("Unauthorized", 401)
                return

            if user['id'] == 'guest':
                self.send_json_success([])
                return

            conn = db.get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT t.id, t.cloth_id, t.duration_days, t.trial_fee, t.status,
                               t.start_date, t.end_date, c.name, c.category, c.image_url, c.price as retail_price
                        FROM trials t
                        JOIN clothes c ON t.cloth_id = c.id
                        WHERE t.user_id = %s
                        ORDER BY t.start_date DESC
                    """, (user['id'],))
                    trials = cursor.fetchall()
                    now = datetime.datetime.now()
                    for t in trials:
                        t['trial_fee'] = float(t['trial_fee'])
                        t['retail_price'] = float(t['retail_price'])
                        end_dt = t['end_date']
                        delta = end_dt - now
                        days_left = max(0, delta.days + (1 if delta.seconds > 0 else 0)) if delta.total_seconds() > 0 else 0
                        t['days_left'] = days_left
                        t['start_date'] = t['start_date'].isoformat()
                        t['end_date'] = t['end_date'].isoformat()
                    self.send_json_success(trials)
            except Exception as e:
                self.send_json_error(str(e), 500)
            finally:
                conn.close()
            return

        elif path == '/page':
            user = self.get_current_user()
            self.serve_page(query_params, user)
            return

        elif path.startswith('/admin/') and path not in ('/admin/login', '/admin/dashboard', '/admin/api/login', '/admin/api/seed'):
            user = self.get_current_user()
            title = path.replace('/admin/', '').replace('_', ' ').title()
            try:
                content = self.render_template('templates/admin_stub.html', user, TITLE=title)
                self.send_html_response(content, 200)
            except Exception as e:
                self.send_error(500, f"Error rendering admin stub: {e}")
            return

        else:
            self.send_error(404, "Page not found")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == '/api/send-otp' or path == '/send-otp':
            self.handle_send_otp()
        elif path == '/api/verify-otp' or path == '/verify-otp':
            self.handle_verify_otp()
        elif path == '/api/guest-login' or path == '/guest-login':
            self.handle_guest_login()
        elif path == '/api/logout' or path == '/logout':
            self.handle_logout()
        elif path == '/api/book-trial' or path == '/book-trial':
            self.handle_book_trial()
        elif path == '/api/action-trial' or path == '/action-trial':
            self.handle_action_trial()
        elif path == '/api/admin/login' or path == '/admin-login':
            self.handle_admin_login()
        elif path == '/api/cart/add' or path == '/cart/add':
            self.handle_cart_add()
        elif path == '/api/cart/update' or path == '/cart/update':
            self.handle_cart_update()
        elif path == '/api/cart/remove' or path == '/cart/remove':
            self.handle_cart_remove()
        elif path == '/api/razorpay/create-order':
            self.handle_razorpay_create_order()
        elif path == '/api/razorpay/verify-payment':
            self.handle_razorpay_verify_payment()
        elif path == '/api/checkout/submit' or path == '/checkout/submit':
            self.handle_checkout_submit()
        elif path == '/api/wishlist/add' or path == '/wishlist/add':
            self.handle_wishlist_add()
        elif path == '/api/wishlist/remove' or path == '/wishlist/remove':
            self.handle_wishlist_remove()
        else:
            self.send_json_error("Endpoint not found", 404)

    def handle_cart_add(self):
        user = self.get_current_user()
        if not user:
            self.send_response(303)
            self.send_header('Location', '/account?error=' + urllib.parse.quote("Please login first"))
            self.end_headers()
            return

        data = self.get_post_data()
        cloth_id = data.get('cloth_id')
        size = str(data.get('size', 'M')).strip()
        color = str(data.get('color', 'Black')).strip()
        qty = int(data.get('quantity', 1))

        session_id = user.get('session_id', '')

        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, quantity FROM cart WHERE session_id = %s AND cloth_id = %s AND size = %s AND color = %s",
                               (session_id, cloth_id, size, color))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("UPDATE cart SET quantity = quantity + %s WHERE id = %s", (qty, existing['id']))
                else:
                    cursor.execute("INSERT INTO cart (session_id, cloth_id, size, color, quantity) VALUES (%s, %s, %s, %s, %s)",
                                   (session_id, cloth_id, size, color, qty))
                conn.commit()
                _CART_COUNT_CACHE.clear()

            if self.is_form_submission():
                self.send_response(303)
                self.send_header('Location', '/cart?success=' + urllib.parse.quote("Added to cart"))
                self.end_headers()
        except Exception as e:
            self.send_error(500, f"Cart Add Error: {e}")
        finally:
            conn.close()

    def handle_cart_update(self):
        data = self.get_post_data()
        cart_id = data.get('cart_id')
        qty = int(data.get('quantity', 1))

        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE cart SET quantity = %s WHERE id = %s", (qty, cart_id))
                conn.commit()
                _CART_COUNT_CACHE.clear()
            if self.is_form_submission():
                self.send_response(303)
                self.send_header('Location', '/cart')
                self.end_headers()
        except Exception as e:
            pass
        finally:
            conn.close()

    def handle_cart_remove(self):
        data = self.get_post_data()
        cart_id = data.get('cart_id')
        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
                conn.commit()
                _CART_COUNT_CACHE.clear()
            if self.is_form_submission():
                self.send_response(303)
                self.send_header('Location', '/cart?success=' + urllib.parse.quote("Item removed"))
                self.end_headers()
        except Exception:
            pass
        finally:
            conn.close()

    def handle_checkout_submit(self):
        user = self.get_current_user()
        if not user or user['id'] == 'guest':
            self.send_response(303)
            self.send_header('Location', '/account?error=' + urllib.parse.quote("Please login to checkout"))
            self.end_headers()
            return

        data = self.get_post_data()
        address = str(data.get('address', '')).strip()
        payment_method = str(data.get('payment_method', 'Cash on Delivery')).strip()

        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT c.id as cart_id, cl.id as cloth_id, cl.price, c.quantity, c.size, c.color
                    FROM cart c JOIN clothes cl ON c.cloth_id = cl.id
                    WHERE c.session_id = %s
                """, (user['session_id'],))
                items = cursor.fetchall()

                if not items:
                    self.send_response(303)
                    self.send_header('Location', '/cart?error=' + urllib.parse.quote("Cart is empty"))
                    self.end_headers()
                    return

                total = sum(float(i['price']) * i['quantity'] for i in items)

                cursor.execute("""
                    INSERT INTO orders (user_id, total_amount, final_total, delivery_address, payment_method)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user['id'], total, total, address, payment_method))
                order_id = cursor.lastrowid

                for i in items:
                    cursor.execute("""
                        INSERT INTO order_items (order_id, cloth_id, quantity, price, size, color)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (order_id, i['cloth_id'], i['quantity'], i['price'], i['size'], i['color']))

                cursor.execute("DELETE FROM cart WHERE session_id = %s", (user['session_id'],))
                conn.commit()

            self.send_response(303)
            self.send_header('Location', '/orders?success=' + urllib.parse.quote("Order placed successfully!"))
            self.end_headers()
        except Exception as e:
            self.send_error(500, f"Checkout Error: {e}")
        finally:
            conn.close()
    def handle_razorpay_create_order(self):
        """
        Step 1 of Razorpay flow:
        - Compute total server-side from DB cart (never trust frontend amount)
        - Pre-create TRY-FIT order record with payment_status='created'
        - Create Razorpay order and store razorpay_order_id on the TRY-FIT order
        - Return tryfit_order_id + razorpay order details to frontend
        """
        user = self.get_current_user()

        if not user or user['id'] == 'guest':
            self.send_json_error("Please login to checkout", 401)
            return

        data = self.get_post_data()
        address = str(data.get('address', '')).strip()
        customer_name = str(data.get('name', user.get('name', ''))).strip()

        if not address:
            self.send_json_error("Delivery address is required", 400)
            return

        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. Fetch cart from DB (never trust frontend amount)
                cursor.execute("""
                    SELECT cl.id as cloth_id, cl.price, c.quantity, c.size, c.color
                    FROM cart c
                    JOIN clothes cl ON c.cloth_id = cl.id
                    WHERE c.session_id = %s
                """, (user['session_id'],))
                cart_items = cursor.fetchall()

                if not cart_items:
                    self.send_json_error("Cart is empty", 400)
                    return

                total = sum(float(i['price']) * int(i['quantity']) for i in cart_items)
                amount_paise = int(round(total * 100))

                # 2. Create Razorpay order
                receipt = f"tryfit_{user['id']}_{random.randint(100000, 999999)}"
                try:
                    razorpay_order = razorpay_client.order.create({
                        "amount": amount_paise,
                        "currency": "INR",
                        "receipt": receipt,
                        "payment_capture": 1
                    })
                except Exception as rz_err:
                    self.send_json_error(f"Razorpay order creation failed: {rz_err}", 500)
                    return

                razorpay_order_id = razorpay_order["id"]

                # 3. Pre-create TRY-FIT order (payment_status='created')
                cursor.execute("""
                    INSERT INTO orders
                    (user_id, customer_name, total_amount, final_total,
                     delivery_address, payment_method,
                     razorpay_order_id, payment_status, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'created', 'Pending')
                """, (
                    user['id'], customer_name, total, total,
                    address, 'Razorpay', razorpay_order_id
                ))
                tryfit_order_id = cursor.lastrowid

                # 4. Insert order items
                for item in cart_items:
                    cursor.execute("""
                        INSERT INTO order_items (order_id, cloth_id, quantity, price, size, color)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (tryfit_order_id, item['cloth_id'], item['quantity'],
                          item['price'], item['size'], item['color']))

                conn.commit()

            self.send_json_success({
                "success": True,
                "tryfit_order_id": tryfit_order_id,
                "order_id": razorpay_order_id,
                "amount": amount_paise,
                "currency": "INR",
                "key_id": config.RAZORPAY_KEY_ID
            })

        except Exception as e:
            try: conn.rollback()
            except Exception: pass
            self.send_json_error(f"Order creation error: {e}", 500)
        finally:
            conn.close()

    def handle_razorpay_verify_payment(self):
        """
        Step 2 of Razorpay flow:
        - Verify HMAC-SHA256 signature server-side
        - Verify the TRY-FIT order belongs to the current user and matches the Razorpay order
        - Idempotent: if already paid, return success without duplicating
        - Update order: payment_status='paid', store all Razorpay IDs, clear cart
        """
        user = self.get_current_user()

        if not user or user['id'] == 'guest':
            self.send_json_error("Please login to checkout", 401)
            return

        data = self.get_post_data()

        tryfit_order_id  = str(data.get('tryfit_order_id', '')).strip()
        razorpay_order_id   = str(data.get('razorpay_order_id', '')).strip()
        razorpay_payment_id = str(data.get('razorpay_payment_id', '')).strip()
        razorpay_signature  = str(data.get('razorpay_signature', '')).strip()

        if not all([tryfit_order_id, razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            self.send_json_error("Payment verification data is incomplete", 400)
            return

        # 1. Verify HMAC-SHA256 signature (server-side, using secret key)
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
        except Exception:
            self.send_json_error("Payment signature verification failed. This payment cannot be confirmed.", 400)
            return

        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                # 2. Fetch TRY-FIT order — verify it belongs to this user and matches razorpay_order_id
                cursor.execute("""
                    SELECT id, user_id, razorpay_order_id, payment_status, final_total
                    FROM orders
                    WHERE id = %s
                """, (tryfit_order_id,))
                order = cursor.fetchone()

                if not order:
                    self.send_json_error("Order not found", 404)
                    return

                if str(order['user_id']) != str(user['id']):
                    self.send_json_error("Order does not belong to current user", 403)
                    return

                if order['razorpay_order_id'] != razorpay_order_id:
                    self.send_json_error("Razorpay order ID mismatch", 400)
                    return

                # 3. Idempotency check — already paid, just return success
                if order['payment_status'] in ('paid', 'captured'):
                    # Clear cart in case it wasn't cleared before
                    cursor.execute("DELETE FROM cart WHERE session_id = %s", (user['session_id'],))
                    conn.commit()
                    with _CACHE_LOCK:
                        _CART_COUNT_CACHE.pop(user.get('session_id', ''), None)
                    self.send_json_success({
                        "success": True,
                        "message": "Payment already confirmed",
                        "order_id": order['id']
                    })
                    return

                # 4. Mark order as paid — store all Razorpay fields
                verified_at = datetime.datetime.now()
                cursor.execute("""
                    UPDATE orders
                    SET razorpay_payment_id = %s,
                        razorpay_signature  = %s,
                        payment_status      = 'paid',
                        payment_verified_at = %s,
                        status              = 'Confirmed'
                    WHERE id = %s
                """, (razorpay_payment_id, razorpay_signature, verified_at, tryfit_order_id))

                # 5. Clear cart
                cursor.execute("DELETE FROM cart WHERE session_id = %s", (user['session_id'],))

                conn.commit()

            # Clear in-memory cart count cache
            with _CACHE_LOCK:
                _CART_COUNT_CACHE.pop(user.get('session_id', ''), None)

            self.send_json_success({
                "success": True,
                "message": "Payment verified and order confirmed",
                "order_id": int(tryfit_order_id)
            })

        except Exception as e:
            try: conn.rollback()
            except Exception: pass
            self.send_json_error(f"Payment confirmation error: {e}", 500)
        finally:
            conn.close()

    
    def handle_wishlist_add(self):
        user = self.get_current_user()
        if not user or user['id'] == 'guest':
            if self.is_form_submission():
                self.send_response(303)
                self.send_header('Location', '/account?error=' + urllib.parse.quote("Please login first"))
                self.end_headers()
            else:
                self.send_json_error("Please login first", 401)
            return

        data = self.get_post_data()
        cloth_id = data.get('cloth_id')
        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT IGNORE INTO wishlist (user_id, cloth_id) VALUES (%s, %s)", (user['id'], cloth_id))
                conn.commit()
                # Get the new wishlist count
                cursor.execute("SELECT COUNT(*) as c FROM wishlist WHERE user_id = %s", (user['id'],))
                res = cursor.fetchone()
                new_count = int(res['c'] or 0)
                # Clear wishlist count cache so navbar updates on next load
                with _CACHE_LOCK:
                    _WISHLIST_COUNT_CACHE.pop(user['id'], None)
            if self.is_form_submission():
                self.send_response(303)
                self.send_header('Location', '/wishlist?success=' + urllib.parse.quote("Added to wishlist"))
                self.end_headers()
            else:
                self.send_json_success({"success": True, "action": "added", "wishlist_count": new_count})
        except Exception as e:
            self.send_json_error(f"Error adding to wishlist: {e}", 500)
        finally:
            conn.close()

    def handle_wishlist_remove(self):
        user = self.get_current_user()
        data = self.get_post_data()
        # Support removal by wish_id or cloth_id
        wish_id = data.get('wish_id')
        cloth_id = data.get('cloth_id')
        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                if wish_id:
                    cursor.execute("DELETE FROM wishlist WHERE id = %s", (wish_id,))
                elif cloth_id and user and user['id'] != 'guest':
                    cursor.execute("DELETE FROM wishlist WHERE user_id = %s AND cloth_id = %s", (user['id'], cloth_id))
                conn.commit()
                new_count = 0
                if user and user['id'] != 'guest':
                    cursor.execute("SELECT COUNT(*) as c FROM wishlist WHERE user_id = %s", (user['id'],))
                    res = cursor.fetchone()
                    new_count = int(res['c'] or 0)
                    # Clear wishlist count cache so navbar updates on next load
                    with _CACHE_LOCK:
                        _WISHLIST_COUNT_CACHE.pop(user['id'], None)
            if self.is_form_submission():
                self.send_response(303)
                self.send_header('Location', '/wishlist?success=' + urllib.parse.quote("Removed from wishlist"))
                self.end_headers()
            else:
                self.send_json_success({"success": True, "action": "removed", "wishlist_count": new_count})
        except Exception as e:
            self.send_json_error(f"Error removing from wishlist: {e}", 500)
        finally:
            conn.close()

    def handle_admin_login(self):
        data = self.get_post_data()
        password = str(data.get('password', '')).strip()
        email = str(data.get('email', '')).strip()

        # Check against database where role='admin'
        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s AND role = 'admin'", (email,))
                user = cursor.fetchone()

                # Using a hardcoded password for simplicity for the admin account for now
                if user and password == "admin123":
                    session_id = uuid.uuid4().hex
                    cursor.execute("INSERT INTO sessions (session_id, user_id) VALUES (%s, %s)", (session_id, user['id']))
                    conn.commit()

                    self.send_response(303 if self.is_form_submission() else 200)
                    if not self.is_form_submission():
                        self.send_header('Content-Type', 'application/json')
                    self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; HttpOnly; Max-Age=86400')
                    if self.is_form_submission():
                        self.send_header('Location', '/admin/dashboard')
                    self.end_headers()
                    if not self.is_form_submission():
                        self.wfile.write(json.dumps({"message": "Admin logged in"}).encode('utf-8'))
                else:
                    err = "Invalid admin credentials"
                    if self.is_form_submission():
                        self.send_response(303)
                        self.send_header('Location', f'/admin/login?error={urllib.parse.quote(err)}')
                        self.end_headers()
                    else:
                        self.send_json_error(err, 401)
        except Exception as e:
            self.send_error(500, f"Error: {e}")
        finally:
            conn.close()

    def handle_send_otp(self):
        try:
            data = self.get_post_data()
            email = str(data.get('email', '')).strip()
            purpose = str(data.get('purpose', '')).strip()
            name = str(data.get('name', '')).strip()

            if not email or purpose not in ('register', 'login'):
                err = "Invalid or missing parameters"
                if self.is_form_submission():
                    self.send_response(303)
                    self.send_header('Location', f'/?error={urllib.parse.quote(err)}')
                    self.end_headers()
                    return
                self.send_json_error(err, 400)
                return

            if '@' not in email or '.' not in email:
                err = "Invalid email format"
                if self.is_form_submission():
                    self.send_response(303)
                    self.send_header('Location', f'/?error={urllib.parse.quote(err)}')
                    self.end_headers()
                    return
                self.send_json_error(err, 400)
                return

            conn = db.get_connection()
            cursor = conn.cursor()

            if purpose == 'register':
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    conn.close()
                    err = "This email is already registered. Please log in."
                    if self.is_form_submission():
                        self.send_response(303)
                        self.send_header('Location', f'/?error={urllib.parse.quote(err)}')
                        self.end_headers()
                        return
                    self.send_json_error(err, 400)
                    return
            else:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                if not user:
                    conn.close()
                    err = "Email is not registered. Please sign up first."
                    if self.is_form_submission():
                        self.send_response(303)
                        self.send_header('Location', f'/?error={urllib.parse.quote(err)}')
                        self.end_headers()
                        return
                    self.send_json_error(err, 400)
                    return

            otp = f"{random.randint(100000, 999999)}"
            expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)

            cursor.execute("""
                INSERT INTO otp_verifications (email, otp, purpose, expires_at)
                VALUES (%s, %s, %s, %s)
            """, (email, otp, purpose, expires_at))
            conn.commit()
            conn.close()

            success, message = sms.send_gmail_otp(email, otp)
            if success:
                if self.is_form_submission():
                    redirect_url = f"/verify-otp?email={urllib.parse.quote(email)}&purpose={urllib.parse.quote(purpose)}&name={urllib.parse.quote(name)}&info={urllib.parse.quote(message)}"
                    self.send_response(303)
                    self.send_header('Location', redirect_url)
                    self.end_headers()
                    return
                self.send_json_success({"message": message, "otp": otp})
            else:
                if self.is_form_submission():
                    self.send_response(303)
                    self.send_header('Location', f'/?error={urllib.parse.quote(message)}')
                    self.end_headers()
                    return
                self.send_json_error(message, 500)

        except Exception as e:
            print("Send OTP exception:", e)
            if self.is_form_submission():
                self.send_response(303)
                self.send_header('Location', f'/?error={urllib.parse.quote("Server error occurred")}')
                self.end_headers()
                return
            self.send_json_error(f"Server error: {str(e)}", 500)

    def handle_verify_otp(self):
        try:
            data = self.get_post_data()
            email = str(data.get('email', '')).strip()
            otp_val = str(data.get('otp', '')).strip()
            purpose = str(data.get('purpose', '')).strip()
            name = str(data.get('name', '')).strip()

            if not email or '@' not in email or not otp_val or not otp_val.isdigit() or purpose not in ('register', 'login'):
                err = "Invalid parameters (check email and OTP)"
                if self.is_form_submission():
                    self.send_response(303)
                    self.send_header('Location', f'/verify-otp?email={urllib.parse.quote(email)}&purpose={urllib.parse.quote(purpose)}&name={urllib.parse.quote(name)}&error={urllib.parse.quote(err)}')
                    self.end_headers()
                    return
                self.send_json_error(err, 400)
                return

            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, otp, expires_at FROM otp_verifications
                WHERE email = %s AND purpose = %s AND is_verified = FALSE
                ORDER BY created_at DESC LIMIT 1
            """, (email, purpose))
            otp_rec = cursor.fetchone()

            if not otp_rec:
                conn.close()
                err = "Verification code not found. Please request a new one."
                if self.is_form_submission():
                    self.send_response(303)
                    self.send_header('Location', f'/verify-otp?email={urllib.parse.quote(email)}&purpose={urllib.parse.quote(purpose)}&name={urllib.parse.quote(name)}&error={urllib.parse.quote(err)}')
                    self.end_headers()
                    return
                self.send_json_error(err, 400)
                return

            now = datetime.datetime.now()
            if otp_rec['otp'] != otp_val:
                conn.close()
                err = "Incorrect verification code. Please check and try again."
                if self.is_form_submission():
                    self.send_response(303)
                    self.send_header('Location', f'/verify-otp?email={urllib.parse.quote(email)}&purpose={urllib.parse.quote(purpose)}&name={urllib.parse.quote(name)}&error={urllib.parse.quote(err)}')
                    self.end_headers()
                    return
                self.send_json_error(err, 400)
                return
            elif otp_rec['expires_at'] < now:
                conn.close()
                err = "Verification code has expired. Please request a new one."
                if self.is_form_submission():
                    self.send_response(303)
                    self.send_header('Location', f'/?error={urllib.parse.quote(err)}')
                    self.end_headers()
                    return
                self.send_json_error(err, 400)
                return

            cursor.execute("UPDATE otp_verifications SET is_verified = TRUE WHERE id = %s", (otp_rec['id'],))

            user_id = None
            if purpose == 'register':
                try:
                    cursor.execute("""
                        INSERT INTO users (name, email)
                        VALUES (%s, %s)
                    """, (name, email))
                    conn.commit()
                    user_id = cursor.lastrowid
                except Exception as e:
                    conn.close()
                    err = "User registration failed. Email already in use."
                    if self.is_form_submission():
                        self.send_response(303)
                        self.send_header('Location', f'/?error={urllib.parse.quote(err)}')
                        self.end_headers()
                        return
                    self.send_json_error(err, 400)
                    return
            else:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                user_rec = cursor.fetchone()
                user_id = user_rec['id']

            session_id = uuid.uuid4().hex
            cursor.execute("INSERT INTO sessions (session_id, user_id) VALUES (%s, %s)", (session_id, user_id))
            conn.commit()
            conn.close()

            self.send_response(303 if self.is_form_submission() else 200)
            if not self.is_form_submission():
                self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; HttpOnly; Max-Age=86400')
            if self.is_form_submission():
                success_msg = "Account created successfully! Welcome to TRY-FIT." if purpose == 'register' else "Successfully logged in! Welcome back."
                self.send_header('Location', '/?success=' + urllib.parse.quote(success_msg))
            self.end_headers()
            if not self.is_form_submission():
                self.wfile.write(json.dumps({"message": "Successfully verified and logged in"}).encode('utf-8'))

        except Exception as e:
            print("Verify OTP exception:", e)
            if self.is_form_submission():
                self.send_response(303)
                self.send_header('Location', f'/?error={urllib.parse.quote("Server verification error")}')
                self.end_headers()
                return
            self.send_json_error(f"Server error: {str(e)}", 500)

    def handle_logout(self):
        cookie_header = self.headers.get('Cookie')
        if cookie_header:
            cookies = http.cookies.SimpleCookie(cookie_header)
            if 'session_id' in cookies:
                session_id = cookies['session_id'].value

                _SESSION_CACHE.pop(session_id, None)
                _CART_COUNT_CACHE.pop(session_id, None)
                conn = db.get_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
                    conn.commit()
                except Exception as e:
                    print("Logout database deletion error:", e)
                finally:
                    conn.close()

        self.send_response(303 if self.is_form_submission() or 'text/html' in self.headers.get('Accept', '') else 200)
        if not self.is_form_submission() and 'text/html' not in self.headers.get('Accept', ''):
            self.send_header('Content-Type', 'application/json')
        self.send_header('Set-Cookie', 'session_id=; Path=/; HttpOnly; Max-Age=0')
        if self.is_form_submission() or 'text/html' in self.headers.get('Accept', ''):
            self.send_header('Location', '/')
        self.end_headers()
        if not self.is_form_submission() and 'text/html' not in self.headers.get('Accept', ''):
            self.wfile.write(json.dumps({"message": "Successfully logged out"}).encode('utf-8'))

    def handle_guest_login(self):
        session_id = uuid.uuid4().hex
        self.send_response(303 if self.is_form_submission() or 'text/html' in self.headers.get('Accept', '') else 200)
        if not self.is_form_submission() and 'text/html' not in self.headers.get('Accept', ''):
            self.send_header('Content-Type', 'application/json')
        self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; HttpOnly; Max-Age=86400')
        if self.is_form_submission() or 'text/html' in self.headers.get('Accept', ''):
            self.send_header('Location', '/')
        self.end_headers()
        if not self.is_form_submission() and 'text/html' not in self.headers.get('Accept', ''):
            self.wfile.write(json.dumps({"message": "Logged in as guest"}).encode('utf-8'))

    def handle_book_trial(self):
        user = self.get_current_user()
        if not user or user['id'] == 'guest':
            err = "Please log in or register to book a home trial."
            if self.is_form_submission():
                dest = '/dashboard' if user and user['id'] == 'guest' else '/'
                self.send_response(303)
                self.send_header('Location', f'{dest}?error={urllib.parse.quote(err)}')
                self.end_headers()
                return
            self.send_json_error(err, 403)
            return

        try:
            data = self.get_post_data()
            cloth_id = data.get('cloth_id')
            duration_days = int(data.get('duration_days', 3))
            address = str(data.get('address', '')).strip()

            if not cloth_id or not address or duration_days not in (3, 7):
                err = "Missing or invalid trial parameters"
                if self.is_form_submission():
                    self.send_response(303)
                    self.send_header('Location', f'/dashboard?error={urllib.parse.quote(err)}')
                    self.end_headers()
                    return
                self.send_json_error(err, 400)
                return

            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT name, trial_price FROM clothes WHERE id = %s", (cloth_id,))
            cloth = cursor.fetchone()

            if not cloth:
                conn.close()
                err = "Clothing item not found in catalog"
                if self.is_form_submission():
                    self.send_response(303)
                    self.send_header('Location', f'/dashboard?error={urllib.parse.quote(err)}')
                    self.end_headers()
                    return
                self.send_json_error(err, 404)
                return

            standard_price = float(cloth['trial_price'])
            if duration_days == 3:
                trial_fee = standard_price - 20.0
            else:
                trial_fee = standard_price + 30.0
            trial_fee = max(100.0, min(200.0, trial_fee))

            start_date = datetime.datetime.now()
            end_date = start_date + datetime.timedelta(days=duration_days)

            cursor.execute("""
                INSERT INTO trials (user_id, cloth_id, duration_days, trial_fee, status, start_date, end_date)
                VALUES (%s, %s, %s, %s, 'trying', %s, %s)
            """, (user['id'], cloth_id, duration_days, trial_fee, start_date, end_date))

            conn.commit()
            conn.close()

            success_msg = f"Successfully booked {duration_days}-day home trial for {cloth['name']} (₹{int(trial_fee)})!"
            if self.is_form_submission():
                self.send_response(303)
                self.send_header('Location', f'/dashboard?success={urllib.parse.quote(success_msg)}')
                self.end_headers()
                return
            self.send_json_success({"message": success_msg})

        except Exception as e:
            print("Book trial error:", e)
            if self.is_form_submission():
                self.send_response(303)
                self.send_header('Location', f'/dashboard?error={urllib.parse.quote("Booking failed")}')
                self.end_headers()
                return
            self.send_json_error(f"Booking failed: {str(e)}", 500)

    def handle_action_trial(self):
        user = self.get_current_user()
        if not user or user['id'] == 'guest':
            err = "Please log in or register to perform this action."
            if self.is_form_submission():
                dest = '/dashboard' if user and user['id'] == 'guest' else '/'
                self.send_response(303)
                self.send_header('Location', f'{dest}?error={urllib.parse.quote(err)}')
                self.end_headers()
                return
            self.send_json_error(err, 403)
            return

        try:
            data = self.get_post_data()
            trial_id = data.get('trial_id')
            action = str(data.get('action', '')).strip()

            if not trial_id or action not in ('buy', 'return'):
                err = "Invalid trial actions parameters"
                if self.is_form_submission():
                    self.send_response(303)
                    self.send_header('Location', f'/dashboard?error={urllib.parse.quote(err)}')
                    self.end_headers()
                    return
                self.send_json_error(err, 400)
                return

            new_status = 'bought' if action == 'buy' else 'returned'

            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id, status FROM trials WHERE id = %s AND user_id = %s", (trial_id, user['id']))
            trial = cursor.fetchone()

            if not trial:
                conn.close()
                err = "Trial order record not found"
                if self.is_form_submission():
                    self.send_response(303)
                    self.send_header('Location', f'/dashboard?error={urllib.parse.quote(err)}')
                    self.end_headers()
                    return
                self.send_json_error(err, 404)
                return

            if trial['status'] != 'trying':
                conn.close()
                err = f"Cannot perform action. Current trial status is '{trial['status']}'"
                if self.is_form_submission():
                    self.send_response(303)
                    self.send_header('Location', f'/dashboard?error={urllib.parse.quote(err)}')
                    self.end_headers()
                    return
                self.send_json_error(err, 400)
                return

            cursor.execute("UPDATE trials SET status = %s WHERE id = %s", (new_status, trial_id))
            conn.commit()
            conn.close()

            outcome = "purchased" if action == "buy" else "returned (scheduled pickup)"
            success_msg = f"Success! Clothing item marked as {outcome}."
            if self.is_form_submission():
                self.send_response(303)
                self.send_header('Location', f'/dashboard?success={urllib.parse.quote(success_msg)}')
                self.end_headers()
                return
            self.send_json_success({"message": success_msg})

        except Exception as e:
            print("Action trial error:", e)
            if self.is_form_submission():
                self.send_response(303)
                self.send_header('Location', f'/dashboard?error={urllib.parse.quote("Action failed")}')
                self.end_headers()
                return
            self.send_json_error(f"Action failed: {str(e)}", 500)

def run_server():
    db.init_db()

    server_address = ('', config.PORT)
    httpd = ReusableTCPServer(server_address, TryFitHandler)
    print(f"TRY-FIT web server running at: http://localhost:{config.PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
