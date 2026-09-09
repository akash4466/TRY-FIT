import pymysql
import pymysql.cursors
from config import config

def get_db_connection():
    """Establishes and returns PyMySQL connection with dictionary cursor."""
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

def init_db():
    """Ensures database and production tables exist on startup."""
    try:
        conn = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS `users` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `full_name` VARCHAR(100) NOT NULL,
            `email` VARCHAR(150) NOT NULL,
            `phone` VARCHAR(15) NULL UNIQUE,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX `idx_users_phone` (`phone`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # Migration check: ensure 'full_name' and 'phone' columns exist if users table was created previously
        cursor.execute("SHOW COLUMNS FROM `users` LIKE 'full_name';")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE `users` ADD COLUMN `full_name` VARCHAR(100) NULL AFTER `id`;")

        cursor.execute("SHOW COLUMNS FROM `users` LIKE 'phone';")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE `users` ADD COLUMN `phone` VARCHAR(15) NULL UNIQUE AFTER `email`;")

        # Create otp_verification table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS `otp_verification` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `email` VARCHAR(150) NOT NULL,
            `otp_hash` VARCHAR(128) NOT NULL,
            `expires_at` DATETIME NOT NULL,
            `attempts` INT DEFAULT 0,
            `verified` BOOLEAN DEFAULT FALSE,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX `idx_otp_email` (`email`),
            INDEX `idx_otp_email_verified` (`email`, `verified`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        conn.commit()
        conn.close()
        print("[Database] Schema initialized successfully.")
    except Exception as e:
        print(f"[Database] Error initializing database: {e}")
