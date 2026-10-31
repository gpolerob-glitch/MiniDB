"""Diagnóstico opcional de conexión: ejecutar tras docker compose up -d.

Usa configuraciones locales de demostración; no afecta las bases de datos.
"""
import os
from dotenv import load_dotenv
import psycopg
from pymongo import MongoClient

load_dotenv()

print("=== MiniDB Studio | diagnóstico ===")
try:
    with psycopg.connect(host=os.getenv('PG_HOST','localhost'),
                         port=int(os.getenv('PG_PORT','15432')),
                         dbname=os.getenv('PG_DB','miniide'),
                         user=os.getenv('PG_USER','ide_user'),
                         password=os.getenv('PG_PASSWORD','ide_demo_2026'),
                         connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute('SHOW server_version')
            print('PostgreSQL OK | versión:', cur.fetchone()[0])
except Exception as exc:
    print('PostgreSQL ERROR |', type(exc).__name__, str(exc)[:200])

client = None
try:
    client = MongoClient(os.getenv('MONGO_URI',
                         'mongodb://ide_admin:ide_demo_2026@localhost:27018/?authSource=admin'),
                         serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    info = client.admin.command('buildInfo')
    print('MongoDB OK | versión:', info.get('version','desconocida'))
except Exception as exc:
    print('MongoDB ERROR |', type(exc).__name__, str(exc)[:200])
finally:
    if client is not None:
        client.close()
