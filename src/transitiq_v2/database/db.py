from os import getenv
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = getenv("DB_HOST")
DB_NAME = getenv("DB_NAME")
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_PORT = getenv("DB_PORT")


conn = psycopg2.connect(host=DB_HOST , dbname=DB_NAME , user=DB_USER, password=DB_PASSWORD , port=DB_PORT)

def create_issues_table():
    # shipment_id is the primary key of the live table (there is no separate id column).
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                shipment_id SERIAL PRIMARY KEY,
                origin VARCHAR(255) NOT NULL,
                destination VARCHAR(255) NOT NULL,
                carrier VARCHAR(255) NOT NULL,
                issue_description TEXT NOT NULL,
                status VARCHAR(255) NOT NULL DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # CREATE TABLE IF NOT EXISTS does not touch an already-existing table,
        # so the V3 lifecycle columns are added explicitly for older databases.
        cur.execute("ALTER TABLE issues ADD COLUMN IF NOT EXISTS status VARCHAR(255) NOT NULL DEFAULT 'new'")
        cur.execute("ALTER TABLE issues ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        cur.execute("ALTER TABLE issues ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

def create_analysis_runs_table():
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id SERIAL PRIMARY KEY,
                exception_id INTEGER NOT NULL REFERENCES issues(shipment_id),
                exception_type VARCHAR(255) NOT NULL,
                severity VARCHAR(255) NOT NULL,
                missing_information TEXT NOT NULL,
                recommended_actions TEXT NOT NULL,
                model_name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

