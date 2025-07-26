import os
import pg8000
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return pg8000.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME")
    )

def initialize_tables():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            timestamp TIMESTAMPTZ,
            action TEXT,
            amount FLOAT,
            price FLOAT,
            confidence FLOAT,
            symbol TEXT,
            tx_sig TEXT,
            pnl FLOAT,
            Return_pct FLOAT,
            sentiment FLOAT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_votes (
            timestamp TIMESTAMPTZ,
            agent TEXT,
            action TEXT,
            amount FLOAT,
            confidence FLOAT,
            symbol TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            timestamp TIMESTAMPTZ,
            symbol TEXT,
            price FLOAT,
            volume FLOAT
        );
        """)

        conn.commit()

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

