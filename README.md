# TRY-FIT

**TRY-FIT** is a full-featured e-commerce platform designed for clothing retail. It leverages a lightweight, custom Python backend with a MySQL database and a pure HTML/CSS/JavaScript frontend to deliver a highly responsive and feature-rich shopping experience.

This README is designed to provide comprehensive context for any developer or AI assistant working on this codebase in the future.

---

## 🚀 Project Architecture

The TRY-FIT project strictly avoids heavy frontend or backend frameworks (like React, Django, or Flask), relying instead on standard built-in libraries and raw web technologies to maximize performance, customizability, and learnability.

### Tech Stack
*   **Backend:** Python (`http.server.BaseHTTPRequestHandler`)
*   **Database:** MySQL (Hosted on Aiven Cloud)
*   **Frontend:** Vanilla HTML5, CSS3, and JavaScript (ES6)
*   **Payment Gateway:** Razorpay API

### Core Components
*   **`server.py`:** The heart of the application. It contains the custom HTTP request handler, routing logic (`serve_search`, `serve_book_trial`), API endpoints, and Razorpay integration handlers.
*   **`db.py`:** Handles database connections, initialization scripts, and table creation (including migrations).
*   **`config.py` / `.env`:** Manages environment variables and application secrets.
*   **`templates/`:** Contains all the HTML templates used for rendering pages.
*   **`static/`:** Stores CSS stylesheets and client-side JavaScript.

---

## ✨ Features Implemented

*   **Product Catalog:** Dynamic product grids with support for multiple categories.
*   **Attribute-Aware Search:** Custom search engine that gracefully matches categories, brands, and colors using complex SQL `LIKE` filtering, ensuring exact matches don't leak into unrelated categories.
*   **Wishlist System:** Users can save their favorite items via a toggleable heart button. The state is synchronized with the database (preventing duplicates via a `UNIQUE` constraint).
*   **Cart & Checkout:** Full cart lifecycle management.
*   **Payments (Razorpay):** Secure, server-side Razorpay integration. Orders are pre-created in the database, amounts are calculated on the server to prevent tampering, and payment signatures are verified securely.
*   **Sorting & Filtering:** Client-side UI coupled with server-side queries for robust product discovery (includes a 1-second shimmer animation for a premium feel).
*   **Trial Bookings:** Specialized flow for booking clothing trials.

---

## 🛠️ Setup & Execution

### Prerequisites
*   Python 3.10+
*   MySQL Server (or an Aiven Cloud instance)
*   Razorpay API Keys

### Installation
1.  **Clone the repository.**
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Ensure `razorpay` and `mysql-connector-python` are installed)*
3.  **Environment Variables:**
    Copy `.env.example` to `.env` and fill in the necessary values:
    *   `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`
    *   `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`
4.  **Initialize the Database:**
    ```bash
    python db.py
    ```
5.  **Run the Server:**
    ```bash
    python server.py
    ```

---

## 🤖 Guide for Future AI Assistants

If you are an AI assistant picking up this project, please adhere to the following architectural constraints and guidelines:

1.  **Do NOT Rebuild from Scratch:** The user explicitly prefers the existing custom Python + HTML/JS stack. Do not attempt to migrate this to React, Next.js, Django, or Flask.
2.  **Maintain the UI Design:** The frontend employs a specific design language (product cards, luxury sorting animations, specific navbars). Ensure new components match the existing CSS classes in `style.css`.
3.  **Security First:** Never calculate payment amounts on the frontend. Always manage Razorpay order creation and HMAC verification strictly within `server.py`.
4.  **Database Migrations:** When altering tables (like the recent `wishlist` unique constraint), ensure you write safe, idempotent SQL in `db.py` that handles existing data anomalies gracefully before applying constraints.
5.  **Avoid Global State Leaks:** The `http.server` handles requests in threads. Be careful with global variables; rely on session IDs and database lookups.

---

## 🎯 Future Goals & Roadmap

The following features represent the next steps for TRY-FIT's evolution:

*   [ ] **Admin Dashboard Completion:** Fully build out `admin_stub.html` to allow administrators to add/edit/remove products, view global orders, and manage users.
*   [ ] **Order History & Tracking:** Enhance the user dashboard to show past orders with real-time status updates (Pending, Shipped, Delivered).
*   [ ] **Advanced AI Integrations:**
    *   *Virtual Try-On / Size Recommender:* Integrate AI models to recommend sizes based on user measurements.
    *   *Smart Recommendations:* Show "Frequently Bought Together" or "Similar Items" on product pages based on browsing history.
*   [ ] **Email Notifications:** Integrate the configured email providers (Resend/Brevo) to send order confirmations and tracking updates.
*   [ ] **Performance Optimization:** Implement caching (e.g., Redis) for the product catalog to reduce database load during traffic spikes.
*   [ ] **Comprehensive Test Suite:** Add `pytest` modules to automatically test the Razorpay payment flow, search logic, and database constraints.
