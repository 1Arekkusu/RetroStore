import sqlite3
from products import products

conn = sqlite3.connect("database.db")
conn.executemany(
    """INSERT OR REPLACE INTO products
    (id, name, description, price, image, type, genre)
    VALUES (?, ?, ?, ?, ?, ?, ?)""",
    [(p["id"], p["name"], p.get("description"), p["price"], 
      p.get("image"), p.get("type"), p.get("genre")) for p in products]
)
conn.commit()
conn.close()