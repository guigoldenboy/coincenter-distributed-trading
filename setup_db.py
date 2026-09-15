import sqlite3

conn = sqlite3.connect("coincenter.db")
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

cursor.executescript("""
CREATE TABLE IF NOT EXISTS Clients (
    id INTEGER PRIMARY KEY,
    is_manager INTEGER NOT NULL,
    balance REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Assets (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    supply INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ClientAssets (
    client_id INTEGER,
    asset_symbol TEXT,
    quantity REAL,
    PRIMARY KEY (client_id, asset_symbol),
    FOREIGN KEY (client_id) REFERENCES Clients(id) ON DELETE CASCADE,
    FOREIGN KEY (asset_symbol) REFERENCES Assets(symbol) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    symbol TEXT,
    type TEXT,
    quantity REAL,
    price REAL,
    datetime TEXT
);
""")

# meter users default
cursor.execute("INSERT OR IGNORE INTO Clients (id, is_manager, balance) VALUES (0, 1, 0)")
cursor.execute("INSERT OR IGNORE INTO Clients (id, is_manager, balance) VALUES (1, 0, 1000)")

# meter ativos default
cursor.execute("INSERT OR IGNORE INTO Assets (symbol, name, price, supply) VALUES ('BTC', 'Bitcoin', 25000, 100)")
cursor.execute("INSERT OR IGNORE INTO Assets (symbol, name, price, supply) VALUES ('ETH', 'Ethereum', 1700, 200)")

conn.commit()
conn.close()
print("Base de dados criada com sucesso.")
