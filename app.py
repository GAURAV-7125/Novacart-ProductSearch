from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB = Path(__file__).with_name("products.db")

# ---------------- Database ----------------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

SEED_PRODUCTS = [
    (101, "iPhone 15 Pro", "Electronics", 999.99, 4.8),
    (102, "MacBook Air M3", "Electronics", 1199.50, 4.9),
    (103, "iPad Air", "Electronics", 599.00, 4.6),
    (104, "Sony WH-1000XM5", "Electronics", 349.99, 4.7),
    (201, "Nike Air Max", "Footwear", 130.00, 4.4),
    (202, "Adidas UltraBoost", "Footwear", 180.00, 4.5),
    (301, "Coffee Maker", "Appliances", 89.99, 4.2),
]

# 100 additional products for a richer demo database.
PRODUCT_NAMES = {
    "Electronics": [
        "Samsung Galaxy S25", "Google Pixel 10", "OnePlus 13", "Dell Inspiron 15",
        "HP Pavilion 14", "Lenovo IdeaPad Slim", "ASUS Vivobook 16", "Acer Aspire 5",
        "JBL Flip Speaker", "Bose SoundLink Mini", "Anker Power Bank", "Logitech MX Master",
        "Apple Watch SE", "Garmin Venu 3", "Kindle Paperwhite", "GoPro Action Cam",
        "DJI Mini Drone", "Canon EOS Mirrorless", "Nikon Z50 Camera", "Samsung 4K Monitor",
        "LG UltraWide Monitor", "TP-Link WiFi Router", "Epson EcoTank Printer", "Roku Streaming Stick",
        "Nothing Phone", "Realme GT", "Xiaomi Pad", "Fire TV Stick", "Marshall Emberton",
        "Sennheiser Momentum 4"
    ],
    "Footwear": [
        "Puma RS-X", "Reebok Classic", "New Balance 574", "Asics Gel-Kayano",
        "Converse Chuck Taylor", "Vans Old Skool", "Skechers Go Walk", "Jordan 1 Low",
        "Adidas Superstar", "Nike Revolution", "Nike Pegasus", "Puma Suede Classic",
        "Fila Disruptor"
    ],
    "Appliances": [
        "Philips Air Fryer", "Bajaj Mixer Grinder", "Prestige Induction Cooktop", "Dyson Vacuum",
        "LG Microwave Oven", "Samsung Refrigerator", "Whirlpool Washing Machine", "Havells Room Heater",
        "Philips Hair Dryer", "Kent Water Purifier", "Morphy Richards Toaster", "Panasonic Rice Cooker",
        "Oven Toaster Grill", "Electric Kettle"
    ],
    "Home": [
        "IKEA Study Lamp", "Memory Foam Pillow", "Cotton Bedsheet Set", "Wooden Laptop Stand",
        "LED Floor Lamp", "Smart Table Lamp", "Wall Art Set", "Storage Organizer", "Office Chair",
        "Minimalist Desk", "Throw Blanket", "Digital Alarm Clock", "Ceramic Vase"
    ],
    "Sports": [
        "Yonex Badminton Racket", "Cosco Football", "SG Cricket Bat", "Wilson Tennis Racket",
        "Nivia Basketball", "Decathlon Yoga Mat", "Adjustable Dumbbells", "Resistance Bands",
        "Skipping Rope", "Trekking Backpack", "Cycling Helmet", "Table Tennis Set"
    ],
    "Beauty": [
        "Face Moisturizer", "Vitamin C Serum", "Sunscreen SPF 50", "Gentle Face Wash",
        "Hair Care Kit", "Beard Grooming Kit", "Lip Balm Set", "Body Lotion", "Perfume Mist",
        "Makeup Brush Set", "Aloe Vera Gel", "Shampoo & Conditioner"
    ],
    "Books": [
        "Python Programming Guide", "Data Structures Handbook", "Algorithms Made Easy", "Clean Code Guide",
        "AI Fundamentals", "Machine Learning Basics", "Web Development Starter", "C++ Programming Mastery",
        "Database Systems", "Digital Electronics Notes", "The Design of Everyday Things"
    ],
    "Accessories": [
        "Leather Wallet", "Canvas Backpack", "Polarized Sunglasses", "Stainless Steel Bottle",
        "Travel Organizer", "Minimal Card Holder", "Laptop Sleeve", "USB-C Hub", "Desk Mat",
        "Key Organizer", "Wireless Charging Pad", "Travel Adapter"
    ]
}

def make_extra_products():
    items = []
    base_prices = {
        "Electronics": 49, "Footwear": 55, "Appliances": 35, "Home": 20,
        "Sports": 18, "Beauty": 12, "Books": 10, "Accessories": 15
    }
    pid = 1001
    for category, names in PRODUCT_NAMES.items():
        for idx, name in enumerate(names):
            if len(items) >= 100:
                return items
            price = round(base_prices[category] + ((idx * 17 + len(name) * 3) % 260) + 0.99, 2)
            rating = round(4.0 + ((idx * 7 + len(name)) % 10) / 10, 1)
            items.append((pid, name, category, price, min(rating, 4.9)))
            pid += 1
    return items


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            rating REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            product_id INTEGER PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    """)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executemany(
        "INSERT OR IGNORE INTO products(id,name,category,price,rating) VALUES(?,?,?,?,?)",
        SEED_PRODUCTS + make_extra_products()
    )
    conn.commit()
    conn.close()

# ---------------- Trie ----------------
class TrieNode:
    def __init__(self):
        self.children = {}
        self.product_ids = []

class ProductTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, name, product_id):
        node = self.root
        for ch in name.lower():
            node = node.children.setdefault(ch, TrieNode())
            if product_id not in node.product_ids:
                node.product_ids.append(product_id)

    def search(self, prefix):
        node = self.root
        for ch in prefix.lower():
            if ch not in node.children:
                return []
            node = node.children[ch]
        return node.product_ids[:]


def build_trie(products):
    trie = ProductTrie()
    for p in products:
        trie.insert(p["name"], p["id"])
    return trie

# ---------------- Merge Sort ----------------
def merge_sort(products, ascending=True):
    if len(products) <= 1:
        return products
    mid = len(products) // 2
    left = merge_sort(products[:mid], ascending)
    right = merge_sort(products[mid:], ascending)
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        take_left = left[i]["price"] <= right[j]["price"] if ascending else left[i]["price"] >= right[j]["price"]
        if take_left:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def row_to_dict(row):
    return dict(row)


def all_products():
    conn = get_db()
    rows = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]

# ---------------- Routes ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.get("/api/products")
def products():
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "none")
    conn = get_db()
    if category:
        rows = conn.execute("SELECT * FROM products WHERE LOWER(category)=LOWER(?)", (category,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    data = [row_to_dict(r) for r in rows]
    if sort in ("asc", "desc"):
        data = merge_sort(data, sort == "asc")
    return jsonify(data)

@app.get("/api/search/id/<int:product_id>")
def search_id(product_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row) if row else None)

@app.get("/api/search/name")
def search_name():
    prefix = request.args.get("q", "").strip()
    data = all_products()
    trie = build_trie(data)
    ids = trie.search(prefix)
    by_id = {p["id"]: p for p in data}
    return jsonify([by_id[i] for i in ids if i in by_id])

@app.post("/api/products")
def add_product():
    data = request.get_json(force=True)
    required = ["id", "name", "category", "price", "rating"]
    if any(k not in data for k in required):
        return jsonify({"error": "All fields are required"}), 400
    try:
        conn = get_db()
        conn.execute("INSERT INTO products(id,name,category,price,rating) VALUES(?,?,?,?,?)",
                     (int(data["id"]), data["name"].strip(), data["category"].strip(),
                      float(data["price"]), float(data["rating"])))
        conn.commit(); conn.close()
        return jsonify({"message": "Product added successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Product ID already exists"}), 409

@app.put("/api/products/<int:product_id>")
def update_product(product_id):
    data = request.get_json(force=True)
    conn = get_db()
    cur = conn.execute("UPDATE products SET name=?,category=?,price=?,rating=? WHERE id=?",
                       (data["name"].strip(), data["category"].strip(), float(data["price"]),
                        float(data["rating"]), product_id))
    conn.commit(); conn.close()
    if cur.rowcount == 0:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"message": "Product updated successfully"})

@app.delete("/api/products/<int:product_id>")
def delete_product(product_id):
    conn = get_db()
    cur = conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit(); conn.close()
    if cur.rowcount == 0:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"message": "Product deleted successfully"})

@app.get("/api/categories")
def categories():
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    conn.close()
    return jsonify([r["category"] for r in rows])

# ---------------- Wishlist ----------------
@app.get("/api/wishlist")
def get_wishlist():
    conn = get_db()
    rows = conn.execute("""
        SELECT p.* FROM products p
        JOIN wishlist w ON w.product_id = p.id
        ORDER BY w.added_at DESC
    """).fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])

@app.post("/api/wishlist/<int:product_id>")
def add_wishlist(product_id):
    conn = get_db()
    exists = conn.execute("SELECT 1 FROM products WHERE id=?", (product_id,)).fetchone()
    if not exists:
        conn.close(); return jsonify({"error": "Product not found"}), 404
    conn.execute("INSERT OR IGNORE INTO wishlist(product_id) VALUES(?)", (product_id,))
    conn.commit(); conn.close()
    return jsonify({"message": "Added to wishlist"})

@app.delete("/api/wishlist/<int:product_id>")
def remove_wishlist(product_id):
    conn = get_db()
    conn.execute("DELETE FROM wishlist WHERE product_id=?", (product_id,))
    conn.commit(); conn.close()
    return jsonify({"message": "Removed from wishlist"})

# ---------------- Recommendations ----------------
@app.get("/api/recommendations")
def recommendations():
    conn = get_db()
    products = [row_to_dict(r) for r in conn.execute("SELECT * FROM products").fetchall()]
    wish = [row_to_dict(r) for r in conn.execute("""
        SELECT p.* FROM products p JOIN wishlist w ON p.id=w.product_id
    """).fetchall()]
    conn.close()

    wish_ids = {p["id"] for p in wish}
    category_counts = {}
    for p in wish:
        category_counts[p["category"]] = category_counts.get(p["category"], 0) + 1

    # Recommendation score: wishlist category affinity + rating + a small price-quality signal.
    scored = []
    for p in products:
        if p["id"] in wish_ids:
            continue
        affinity = category_counts.get(p["category"], 0) * 2.5
        score = affinity + p["rating"] * 1.5
        if not wish:
            score = p["rating"] * 2.0
        scored.append((score, p))

    scored.sort(key=lambda x: (x[0], x[1]["rating"]), reverse=True)
    return jsonify([p for _, p in scored[:12]])

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
