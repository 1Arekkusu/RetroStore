from flask import Flask, request, render_template, redirect, session, g
from products import products
import secrets
import os
import sqlite3

app = Flask(__name__, static_folder="public")

DATABASE = "database.db"
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

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

@app.route("/")
def index():

    type_filter = request.args.get("type")
    genre_filter = request.args.get("genre")

    filtered = products
    if type_filter:
        filtered = [p for p in filtered if p.get('type') == type_filter]
    if genre_filter:
        filtered = [p for p in filtered if p.get('genre') == genre_filter]

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
    cart = session.get('cart', {})
    cart_products = []
    total = 0
    for product in products:
        product_id = str(product['id'])
        if product_id in cart:
            quantity = cart[product_id]
            subtotal = round(product['price'] * quantity, 2)
            total += subtotal
            cart_products.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
    shipping = 0 if total >= 150 else 15
    total += shipping
    total = round(total, 2)
    return render_template("cart.html", cart_products=cart_products, total=total, shipping = shipping)

@app.route("/checkout", methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    cart_products = []
    total = 0
    for product in products:
        product_id = str(product['id'])
        if product_id in cart:
            quantity = cart[product_id]
            subtotal = round(product['price'] * quantity, 2)
            total += subtotal
            cart_products.append({
                'product_id': product_id,
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity,
                'subtotal': product['price'] * quantity
            })
    shipping = 0 if total >= 150 else 15
    total += shipping
    total = round(total, 2)
    if request.method == 'POST':
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
            """INSERT INTO order_items(order_id, product_id, name, price, quantity)
               VALUES (?, ?, ?, ?, ?)""",
            [(order_id, int(i["product_id"]), i["name"], i["price"], i["quantity"])
            for i in cart_products]
        )
        db.commit()

        session['cart'] = {}
        return redirect('/order-confirmed')
    return render_template("checkout.html", cart_products=cart_products, total=total, shipping = shipping)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        message = {
            "name": request.form["name"],
            "email": request.form["email"],
            "message": request.form["message"]
        }

        messages = load_file(MESSAGES_FILE)
        messages.append(message)
        save_file(MESSAGES_FILE, messages)

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

