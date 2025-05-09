import sqlite3

# connect to database (creates one if not exists)
conn = sqlite3.connect("voting_system.db")
cursor = conn.cursor()

# create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id_hash TEXT PRIMARY KEY,
    last4 TEXT,
    token TEXT,
    token_expiry TEXT,
    voted INTEGER
)
''')

# create votes table
cursor.execute('''
CREATE TABLE IF NOT EXISTS votes (
    id_hash TEXT,
    vote TEXT,
    ip_address TEXT,
    time_cast TEXT,
    token TEXT
)
''')

conn.commit()
conn.close()
print("Database initialized.")
