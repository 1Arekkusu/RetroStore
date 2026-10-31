from flask import Flask, request, render_template, redirect, session, g
from products import products
import secrets
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__, static_folder="public")

DATABASE = "database.db"
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def build_cart(cart):
    if not cart:
        return [], 0, 0

    ids = [int(i) for i in cart]
    placeholders = ",".join("?" * len(ids))
    rows = get_db().execute(
        f"SELECT * FROM products WHERE id IN ({placeholders})", ids
    ).fetchall()

    items = []
    total = 0
    for row in rows:
        quantity = cart[str(row["id"])]     
        subtotal = round(row["price"] * quantity, 2)
        total += subtotal
        items.append({"product": row, "quantity": quantity, "subtotal": subtotal})

    shipping = 0 if total >= 150 else 15
    total = round(total + shipping, 2)
    return items, shipping, total

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.cli.command("init-db")
def init_db_command():
    with open("schema.sql") as f:
        get_db().executescript(f.read())
    print("Database initialized.")

@app.route("/register", methods = ["GET", "POST"])
def register():
    errors = {};
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        db = get_db()

        if not username:
            erorrs["username"] = "Please eneter a username."
        elif db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            erorrs["username"] = "That username is already taken."

        if "@" not in email:
            erorrs["email"] = "Please enter a valid email"
        elif db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            errors["email"] = "An account with that email already exists."

        if len(password) < 8:
            errors["password"] = "Password must be at least 8 characters."

        if not errors:
            try:
                db.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username,  email, generate_password_hash(password))
                )       
                db.commit()
                return redirect("/login")
            except sqlite3.IntegrityError as e:
                if "users.username" in str(e):
                    errors["username"] = "That username is already taken."
                else:
                    errors["email"] = "An account with that email already exists."


    return render_template("register.html", errors = errors) 

@app.route("/")
def index():

    type_filter = request.args.get("type")
    genre_filter = request.args.get("genre")

    db = get_db()
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    if type_filter:
        query += " AND type = ?"
        params.append(type_filter)
    if genre_filter:
        query += " AND genre = ?"
        params.append(genre_filter)
    filtered = db.execute(query, params).fetchall()

    return render_template('index.html', products=filtered, active_type=type_filter, active_genre=genre_filter)

@app.route("/cart/add-item", strict_slashes=False)
def add_to_cart():
    product_id = request.args.get('id')
    if 'cart' not in session:
        session['cart'] = {}
    cart = session['cart']  
    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1
    session['cart'] = cart
    return redirect('/')

@app.route("/cart/remove-item", strict_slashes=False)
def remove_from_cart():
    product_id = request.args.get('id')
    cart = session.get('cart', {})
    if product_id in cart:
        del cart[product_id]
    session['cart'] = cart
    return redirect('/cart')

@app.route("/cart/update-item")
def update_cart():
    product_id = request.args.get('id')
    action = request.args.get('action')
    cart = session.get('cart', {})

    if product_id in cart:
        if action == 'inc':
            cart[product_id] += 1
        elif action == 'dec':
            cart[product_id] -= 1
            if(cart[product_id] <= 0):
                del cart[product_id]

    session['cart'] = cart
    return redirect('/cart')

@app.route("/cart")
def cart():
    items, shipping, total = build_cart(session.get("cart", {}))
    return render_template("cart.html", cart_products=items, total=total, shipping=shipping)

@app.route("/checkout", methods=['GET', 'POST'])
def checkout():
    items, shipping, total = build_cart(session.get("cart", {}))

    if request.method == "POST":

        if not items:
            return redirect("/cart")

        db = get_db()
        cur = db.execute(
            """INSERT INTO orders
               (full_name, email, phone, address, payment_method, shipping, total)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (request.form["full_name"], request.form["email"], request.form["phone"],
             request.form["address"], request.form["payment_method"], shipping, total)
        )
        order_id = cur.lastrowid

        db.executemany(
            """INSERT INTO order_items (order_id, product_id, name, price, quantity)
               VALUES (?, ?, ?, ?, ?)""",
            [(order_id, i["product"]["id"], i["product"]["name"],
              i["product"]["price"], i["quantity"]) for i in items]
        )
        db.commit()

        session["cart"] = {}
        return redirect("/order-confirmed")

    return render_template("checkout.html", cart_products=items, total=total, shipping=shipping)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        db = get_db()
        db.execute(
            "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
            (request.form["name"], request.form["email"], request.form["message"])
        )
        db.commit()

    return render_template("contact.html")


@app.route("/order-confirmed")
def order_confirmed():
    return render_template("confirmed.html")


@app.errorhandler(404)
def error404(code):
    return "HTTP Error 404 - Page Not Found"


# Run the webserver (port 5000 - the default Flask port)
if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")

