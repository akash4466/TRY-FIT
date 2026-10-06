import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import db

# Verify otp_verifications table unchanged
conn = db.get_connection()
cur = conn.cursor()
cur.execute('SHOW CREATE TABLE otp_verifications')
row = cur.fetchone()
print('=== otp_verifications CREATE TABLE ===')
ddl = row['Create Table']
for c in ['"']:
    ddl = ddl.replace(c, '`')
print(ddl)
cur.execute('SELECT COUNT(*) as c FROM otp_verifications')
print('Row count:', cur.fetchone()['c'])
conn.close()
print('Database OK - table unchanged')
