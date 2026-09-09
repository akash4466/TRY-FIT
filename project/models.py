import datetime
from database import get_db_connection

class UserModel:
    """Database Access Object for Users table using parameterized queries."""

    @staticmethod
    def get_by_email(email: str) -> dict:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def create(full_name: str, email: str) -> int:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (full_name, email) VALUES (%s, %s)",
                    (full_name, email)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class OTPModel:
    """Database Access Object for OTP Verification table using parameterized queries."""

    @staticmethod
    def get_latest_active_otp(email: str) -> dict:
        """Fetches the latest unverified OTP record for a given email address."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM otp_verification
                    WHERE email = %s AND verified = FALSE
                    ORDER BY id DESC LIMIT 1
                """, (email,))
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def invalidate_all_active_otps(email: str):
        """Invalidates/deletes any previous unverified OTPs to ensure only 1 active OTP per email."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM otp_verification WHERE email = %s AND verified = FALSE",
                    (email,)
                )
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def create_otp(email: str, otp_hash: str, expires_at: datetime.datetime) -> int:
        """Stores hashed OTP with expiration timestamp."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO otp_verification (email, otp_hash, expires_at, attempts, verified)
                    VALUES (%s, %s, %s, 0, FALSE)
                """, (email, otp_hash, expires_at))
                conn.commit()
                return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def increment_attempts(otp_id: int):
        """Increments attempt count for OTP verification security tracking."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE otp_verification SET attempts = attempts + 1 WHERE id = %s",
                    (otp_id,)
                )
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def mark_verified(otp_id: int):
        """Marks OTP as verified upon successful match."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE otp_verification SET verified = TRUE WHERE id = %s",
                    (otp_id,)
                )
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def delete_otp(otp_id: int):
        """Deletes OTP record after verification."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM otp_verification WHERE id = %s", (otp_id,))
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def is_email_verified(email: str) -> bool:
        """Checks if email has a recent verified OTP record (valid for registration)."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id FROM otp_verification
                    WHERE email = %s AND verified = TRUE
                    ORDER BY id DESC LIMIT 1
                """, (email,))
                return cursor.fetchone() is not None
        finally:
            conn.close()
