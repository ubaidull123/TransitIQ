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

cur = conn.cursor()

def create_issues_table():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            shipment_id SERIAL PRIMARY KEY,
            origin VARCHAR(255) NOT NULL,
            destination VARCHAR(255) NOT NULL,
            carrier VARCHAR(255) NOT NULL,
            issue_description TEXT NOT NULL
        )
    """)
    conn.commit()

