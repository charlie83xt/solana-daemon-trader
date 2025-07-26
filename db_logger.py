import sqlite3
from datetime import datetime
from db import get_connection

DB_PATH = "trading.db"

def fetch_all_trades():
    # conn = sqlite3.connect(DB_PATH)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM trades ORDER BY timestamp ASC")
    rows = c.fetchall()
    # conn.close()
    return rows


# def init_db():
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()

#     c.execute("""CREATE TABLE IF NOT EXISTS agent_votes (
#         id SERIAL PRIMARY KEY,
#         timestamp TIMESTAMP NOT NULL,
#         agent TEXT NOT FULL,
#         action TEXT NOT FULL,
#         amount FLOAT,
#         confidence FLOAT,
#         symbol TEXT
#     )""")

#     c.execute("""CREATE TABLE IF NOT EXISTS trades (
#         id SERIAL PRIMARY KEY,
#         timestamp TIMESTAMP NOT FULL,
#         action TEXT NOT FULL,
#         amount FLOAT NOT FULL,
#         price FLOAT NOT FULL,
#         confidence FLOAT,
#         symbol TEXT,
#         tx_sig TEXT,
#         pnl FLOAT,
#         return_pct FLOAT,
#         sentiment FLOAT
#     )""")

#     c.execute("""CREATE TABLE IF NOT EXISTS price_history (
#         id SERIAL PRIMARY KEY,
#         timestamp TIMESTAMP NOT FULL,
#         symbol TEXT,
#         price FLOAT,
#         volume FLOAT
#     )""")

#     conn.commit()
#     conn.close()


def log_trade(**kwargs):
    # conn = sqlite3.connect(DB_PATH)
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO trades VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        kwargs.get("timestamp"),
        kwargs.get("action"),
        kwargs.get("amount"),
        kwargs.get("price"),
        kwargs.get("confidence"),
        kwargs.get("symbol"),
        kwargs.get("tx_sig"),
        kwargs.get("pnl"),
        kwargs.get("return_pct"),
        kwargs.get("sentiment")
    ))
    conn.commit()
    conn.close()

def log_agent_votes(**kwargs):
    # conn = sqlite3.connect(DB_PATH)
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO agent_votes VALUES (%s, %s, %s, %s, %s)
    """, (
        kwargs.get("timestamp"),
        kwargs.get("agent"),
        kwargs.get("action"),
        kwargs.get("amount"),
        kwargs.get("confidence"),
        kwargs.get("symbol")
    ))
    conn.commit()
    conn.close()

def log_price_history(**kwargs):
    # conn = sqlite3.connect(DB_PATH)
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO price_history VALUES (%s, %s, %s, %s)
    """, (
        kwargs.get("timestamp"),
        kwargs.get("symbol"),
        kwargs.get("price"),
        kwargs.get("volume")
        
    ))
    conn.commit()
    conn.close()
  