import sqlite3
from datetime import datetime

def get_db():
    conn = sqlite3.connect("coincenter.db")
    conn.row_factory = sqlite3.Row
    return conn

def add_asset(symbol, name, price, supply):
    conn = get_db()
    conn.execute("INSERT INTO Assets (symbol, name, price, supply) VALUES (?, ?, ?, ?)",
                 (symbol, name, price, supply))
    conn.commit()
    conn.close()

def list_assets():
    conn = get_db()
    assets = conn.execute("SELECT symbol, name, price, supply FROM Assets").fetchall()
    conn.close()
    return [dict(a) for a in assets]

def get_asset(symbol):
    conn = get_db()
    asset = conn.execute("SELECT * FROM Assets WHERE symbol = ?", (symbol,)).fetchone()
    conn.close()
    return dict(asset) if asset else None

def login(user_id, is_manager=0):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO Clients (id, is_manager, balance) VALUES (?, ?, 0)",
                 (user_id, is_manager))
    conn.commit()
    conn.close()

def get_user_balance(user_id):
    conn = get_db()
    user = conn.execute("SELECT balance FROM Clients WHERE id = ?", (user_id,)).fetchone()
    assets = conn.execute("SELECT asset_symbol, quantity FROM ClientAssets WHERE client_id = ?", (user_id,)).fetchall()
    conn.close()
    return {
        "balance": user["balance"] if user else 0,
        "assets": [dict(a) for a in assets]
    }

def deposit(user_id, amount):
    if amount <= 0:
        return False
    conn = get_db()
    conn.execute("UPDATE Clients SET balance = balance + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()
    return True

def withdraw(user_id, amount):
    conn = get_db()
    user = conn.execute("SELECT balance FROM Clients WHERE id = ?", (user_id,)).fetchone()
    if not user or user["balance"] < amount:
        conn.close()
        return False
    conn.execute("UPDATE Clients SET balance = balance - ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()
    return True

def buy_asset(user_id, symbol, quantity):
    conn = get_db()
    cursor = conn.cursor()
    asset = cursor.execute("SELECT price, supply FROM Assets WHERE symbol = ?", (symbol,)).fetchone()
    if not asset or asset["supply"] < quantity:
        conn.close()
        return False
    total_price = asset["price"] * quantity
    user = cursor.execute("SELECT balance FROM Clients WHERE id = ?", (user_id,)).fetchone()
    if not user or user["balance"] < total_price:
        conn.close()
        return False
    cursor.execute("UPDATE Clients SET balance = balance - ? WHERE id = ?", (total_price, user_id))
    existing = cursor.execute("SELECT quantity FROM ClientAssets WHERE client_id = ? AND asset_symbol = ?",
                              (user_id, symbol)).fetchone()
    if existing:
        cursor.execute("UPDATE ClientAssets SET quantity = quantity + ? WHERE client_id = ? AND asset_symbol = ?",
                       (quantity, user_id, symbol))
    else:
        cursor.execute("INSERT INTO ClientAssets (client_id, asset_symbol, quantity) VALUES (?, ?, ?)",
                       (user_id, symbol, quantity))
    cursor.execute("UPDATE Assets SET supply = supply - ? WHERE symbol = ?", (quantity, symbol))
    cursor.execute("""
        INSERT INTO Transactions (client_id, symbol, type, quantity, price, datetime)
        VALUES (?, ?, 'buy', ?, ?, ?)
    """, (user_id, symbol, quantity, asset["price"], datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def sell_asset(user_id, symbol, quantity):
    conn = get_db()
    cursor = conn.cursor()
    user_asset = cursor.execute("SELECT quantity FROM ClientAssets WHERE client_id = ? AND asset_symbol = ?",
                                (user_id, symbol)).fetchone()
    if not user_asset or user_asset["quantity"] < quantity:
        conn.close()
        return False
    asset = cursor.execute("SELECT price FROM Assets WHERE symbol = ?", (symbol,)).fetchone()
    if not asset:
        conn.close()
        return False
    cursor.execute("UPDATE Clients SET balance = balance + ? WHERE id = ?",
                   (asset["price"] * quantity, user_id))
    new_qty = user_asset["quantity"] - quantity
    if new_qty > 0:
        cursor.execute("UPDATE ClientAssets SET quantity = ? WHERE client_id = ? AND asset_symbol = ?",
                       (new_qty, user_id, symbol))
    else:
        cursor.execute("DELETE FROM ClientAssets WHERE client_id = ? AND asset_symbol = ?",
                       (user_id, symbol))
    cursor.execute("UPDATE Assets SET supply = supply + ? WHERE symbol = ?", (quantity, symbol))
    cursor.execute("""
        INSERT INTO Transactions (client_id, symbol, type, quantity, price, datetime)
        VALUES (?, ?, 'sell', ?, ?, ?)
    """, (user_id, symbol, quantity, asset["price"], datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def get_transactions(start, end):
    conn = get_db()
    txs = conn.execute("""
        SELECT * FROM Transactions
        WHERE datetime BETWEEN ? AND ?
        ORDER BY datetime
    """, (start, end)).fetchall()
    conn.close()
    return [dict(t) for t in txs]


