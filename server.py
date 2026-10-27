from flask import Flask, request, render_template, redirect, session
from products import products
import os
import json

app = Flask(__name__, static_folder="public")
app.secret_key = "REMOVED"


ORDERS_FILE = "./submitted-data/orders.json"
MESSAGES_FILE = "./submitted-data/messages.json"


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

def load_file(file):
    with open(file, 'r') as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)

def save_file(file, text):
    with open(file, 'w') as  f:
        json.dump(text, f, indent=2)

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
        order = {
            "full_name": request.form["full_name"],
            "email": request.form["email"],
            "phone": request.form["phone"],
            "address": request.form["address"],
            "payment_method": request.form["payment_method"],
            "cart": cart_products
        }
        print(json.dumps(order, indent=2))
        orders = load_file(ORDERS_FILE)
        orders.append(order)
        save_file(ORDERS_FILE, orders)
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

