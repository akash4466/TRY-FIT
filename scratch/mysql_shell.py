import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pymysql
import config

def get_conn():
    conn_params = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
        "database": config.DB_NAME,
        "connect_timeout": 10,
        "cursorclass": pymysql.cursors.DictCursor,
    }
    if config.DB_SSL:
        conn_params["ssl"] = {"ssl": {}}
    return pymysql.connect(**conn_params)

def execute_query(sql):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            if sql.strip().upper().startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")):
                rows = cursor.fetchall()
                if not rows:
                    print("(Empty set)")
                    return
                # Print table format
                headers = list(rows[0].keys())
                print(" | ".join(headers))
                print("-" * (sum(len(h) for h in headers) + 3 * (len(headers) - 1)))
                for row in rows[:50]:  # limit to 50 for display
                    print(" | ".join(str(row[h]) for h in headers))
                if len(rows) > 50:
                    print(f"... and {len(rows) - 50} more rows")
                print(f"({len(rows)} row(s) in set)\n")
            else:
                conn.commit()
                print(f"Query OK, {cursor.rowcount} row(s) affected.\n")
    except Exception as e:
        print(f"Error: {e}\n")
    finally:
        conn.close()

def interactive():
    print("=" * 60)
    print(f"Aiven MySQL Interactive Shell [MySQL 8.4.8]")
    print(f"Host: {config.DB_HOST}")
    print(f"Database: {config.DB_NAME} | User: {config.DB_USER}")
    print("Type your SQL query and press Enter (or 'exit' to quit):")
    print("=" * 60)
    while True:
        try:
            query = input("mysql> ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "\\q"):
                print("Bye!")
                break
            # Safety check against destructive accidental commands
            upper_q = query.upper()
            if "DROP DATABASE" in upper_q or "DROP TABLE" in upper_q or "TRUNCATE" in upper_q:
                confirm = input("CAUTION: Destructive command detected! Type 'CONFIRM' to proceed: ")
                if confirm.strip() != "CONFIRM":
                    print("Command aborted.")
                    continue
            execute_query(query)
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        execute_query(query)
    else:
        interactive()
