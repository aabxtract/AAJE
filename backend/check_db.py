import sqlite3

def check():
    conn = sqlite3.connect("aaje_ops.db")
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print("TABLES in aaje_dev.db:")
    for t in tables:
        print(f"\nTable: {t}")
        cursor.execute(f"PRAGMA table_info({t})")
        cols = cursor.fetchall()
        for col in cols:
            # col[1] is name, col[2] is type
            print(f" - {col[1]} ({col[2]})")
            
if __name__ == "__main__":
    check()
