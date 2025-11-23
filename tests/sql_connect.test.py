import base

import psycopg2
from mylib import ConfigLoader

def get_all_tables():
    cfg = ConfigLoader(config_path="../mylib/sql/config/")
    conn = psycopg2.connect(
        host=cfg.Postgresql.host,
        port=cfg.Postgresql.port,
        dbname=cfg.Postgresql.dbname,
        user=cfg.Postgresql.user,
        password=cfg.Postgresql.password
    )
    
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname = 'public'
    ORDER BY tablename;
    """)
    
    tables = cursor.fetchall()
    
    print("\n\033[36m 数据库中的表: \033[0m")
    for table in tables:
        print(f"  - {table[0]}")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    get_all_tables()
