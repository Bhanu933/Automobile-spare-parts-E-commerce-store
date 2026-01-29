import sqlite3

# Database connection
DB_NAME = "database.db"
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# ----------------------------
# 1. Users table
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0
)
''')

# ----------------------------
# 2. Products table
c.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    image TEXT
)
''')

# ----------------------------
# 3. Cart table
c.execute('''
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
)
''')

# ----------------------------
# 4. Orders table
c.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total REAL NOT NULL,
    status TEXT DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# ----------------------------
# 5. Order items table
c.execute('''
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    price REAL NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
)
''')

# ----------------------------
# Optional: Insert initial products
products = [
    ('Brake Pads', 1200, 'brake.jpg'),
    ('Engine Oil', 900, 'oil.jpg'),
    ('Car Tyre', 4500, 'tyre.jpg'),
    ('Spark Plug', 350, 'sparkplug.jpg'),
    ('Battery', 5200, 'battery.jpg'),
    ('Clutch Plate', 2200, 'clutch.jpg'),
    ('Bike Chain', 800, 'chain.jpg'),
    ('Air Filter', 600, 'airfilter.jpg'),
    ('Mirror', 500, 'mirror.jpg'),
    ('Horn', 300, 'horn.jpg'),
    ('Indicator', 250, 'indicator.jpg'),
    ('Shock', 2000, 'shock.jpg'),
    ('Disc', 1800, 'disc.jpg'),
    ('Cable', 150, 'cable.jpg'),
    ('Piston', 1200, 'piston.jpg'),
    ('Gasket', 300, 'gasket.jpg'),
    ('Carburetor', 2200, 'carburetor.jpg'),
    ('Silencer', 3500, 'silencer.jpg'),
    ('Radiator', 4000, 'radiator.jpg'),
    ('Fuel Pump', 3200, 'fuelpump.jpg')
]

c.executemany('INSERT INTO products (name, price, image) VALUES (?, ?, ?)', products)

# Commit and close
conn.commit()
conn.close()

print("Database and tables created successfully with initial products!")
