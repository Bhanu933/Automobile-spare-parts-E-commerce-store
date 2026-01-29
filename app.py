from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

DB_NAME = "database.db"

# -----------------------
# Helper: DB connection
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------
# Home page — display products
@app.route("/")
def home():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("home.html", products=products)

# -----------------------
# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                         (username, email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Username or email already exists!"
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")

# -----------------------
# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = user["is_admin"]
            return redirect(url_for("home"))
        else:
            return "Invalid email or password!"
    return render_template("login.html")

# -----------------------
# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -----------------------
# Add to Cart
@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM cart WHERE user_id=? AND product_id=?", (user_id, product_id)).fetchone()
    if item:
        conn.execute("UPDATE cart SET quantity = quantity + 1 WHERE id=?", (item["id"],))
    else:
        conn.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)", (user_id, product_id))
    conn.commit()
    conn.close()
    return redirect(url_for("home"))

# -----------------------
# Remove from Cart
@app.route("/remove_from_cart/<int:cart_id>")
def remove_from_cart(cart_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM cart WHERE id=?", (cart_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("cart"))

# -----------------------
# Cart page
@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    conn = get_db_connection()
    cart_items = conn.execute("""
        SELECT cart.id, products.id AS product_id, products.name, products.price, products.image, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = ?
    """, (user_id,)).fetchall()
    total = sum(item["price"] * item["quantity"] for item in cart_items)
    conn.close()
    return render_template("cart.html", cart_items=cart_items, total=total)

# -----------------------
# Checkout page
@app.route("/checkout")
def checkout():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    conn = get_db_connection()
    cart_items = conn.execute("""
        SELECT cart.id, products.id AS product_id, products.name, products.price, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = ?
    """, (user_id,)).fetchall()
    total = sum(item["price"] * item["quantity"] for item in cart_items)
    conn.close()
    return render_template("checkout.html", cart_items=cart_items, total=total)

# -----------------------
# Payment page (simulate)
@app.route("/payment", methods=["GET", "POST"])
def payment():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    conn = get_db_connection()
    cart_items = conn.execute("""
        SELECT cart.id, products.id AS product_id, products.name, products.price, cart.quantity
        FROM cart JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = ?
    """, (user_id,)).fetchall()
    total = sum(item["price"]*item["quantity"] for item in cart_items)

    if request.method == "POST":
        cur = conn.cursor()
        cur.execute("INSERT INTO orders (user_id, total, status) VALUES (?, ?, ?)", (user_id, total, "Paid"))
        order_id = cur.lastrowid
        for item in cart_items:
            cur.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                        (order_id, item["product_id"], item["quantity"], item["price"]))
        # Clear cart
        conn.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("orders"))

    conn.close()
    return render_template("payment.html", total=total)

# -----------------------
# Orders page
@app.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    conn = get_db_connection()
    orders = conn.execute("SELECT * FROM orders WHERE user_id=?", (user_id,)).fetchall()
    conn.close()
    return render_template("orders.html", orders=orders)

# -----------------------
# Admin panel
@app.route("/admin")
def admin():
    if "is_admin" not in session or session["is_admin"] == 0:
        return "Access denied!"
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    orders = conn.execute("SELECT * FROM orders").fetchall()
    conn.close()
    return render_template("admin.html", products=products, orders=orders)

# -----------------------
# Admin: Edit Product
@app.route("/admin/edit_product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if "is_admin" not in session or session["is_admin"] == 0:
        return "Access denied!"
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        conn.execute("UPDATE products SET name=?, price=? WHERE id=?", (name, price, product_id))
        conn.commit()
        conn.close()
        return redirect(url_for("admin"))

    conn.close()
    return render_template("edit_product.html", product=product)

# -----------------------
# Admin: Delete Product
@app.route("/admin/delete_product/<int:product_id>")
def delete_product(product_id):
    if "is_admin" not in session or session["is_admin"] == 0:
        return "Access denied!"
    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

# -----------------------
# Admin: Update Order Status
@app.route("/admin/update_order/<int:order_id>", methods=["POST"])
def update_order(order_id):
    if "is_admin" not in session or session["is_admin"] == 0:
        return "Access denied!"
    status = request.form["status"]
    conn = get_db_connection()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

# -----------------------
if __name__ == "__main__":
    app.run(debug=True)
