import sqlite3


class DBManager:
    def __init__(self, path):
        self.path = path

    def init_db(self):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        # Create houses table if missing
        cur.execute('''
            CREATE TABLE IF NOT EXISTS houses (
                id INTEGER PRIMARY KEY,
                address TEXT UNIQUE
            );''')
        # Create expenses table if missing
        cur.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                house_id INTEGER,
                date TEXT,
                type TEXT CHECK(type IN ('income', 'expense')),
                category TEXT,
                expense TEXT,
                recipient TEXT,
                amount REAL,
                payment TEXT,
                FOREIGN KEY(house_id) REFERENCES houses(id)
            );''')
        # Migrate existing DB: add missing columns
        cur.execute("PRAGMA table_info(expenses);")
        existing = [row[1] for row in cur.fetchall()]
        if 'type' not in existing:
            cur.execute('ALTER TABLE expenses ADD COLUMN type TEXT DEFAULT "expense"')
        if 'category' not in existing:
            cur.execute('ALTER TABLE expenses ADD COLUMN category TEXT')
        if 'expense' not in existing:
            cur.execute('ALTER TABLE expenses ADD COLUMN expense TEXT')
        if 'recipient' not in existing:
            cur.execute('ALTER TABLE expenses ADD COLUMN recipient TEXT')
        if 'payment' not in existing:
            cur.execute('ALTER TABLE expenses ADD COLUMN payment TEXT')
        conn.commit()
        conn.close()

    def connect(self):
        return sqlite3.connect(self.path)
