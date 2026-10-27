# RetroZone 

A retro gaming e-commerce web application built with Flask.

---

## Description

RetroStore is a simple online shop for retro gaming consoles and games. 
Users can browse products, filter them, manage a shopping cart, and place 
orders. The app has no database. All persistent data (orders, contact messages) 
is stored in JSON files.

---

## Implementation

### Backend — `server.py`

Built with **Flask**. All routes are defined in a single file:

- **`/`** - renders the product listing, supports filtering by `type` and `genre`
- **`/cart`** - reads the cart from the session and calculates total, adding a shipping tax for orders that are less than $150
- **`/cart/add-item`, `/cart/remove-item`, `/cart/update-item`** - adds or removes item from the session shopping cart
- **`/checkout`** - on GET, renders the checkout form wit the cart summary. On POST, saves the orders in `orders.json` and empties the cart
- **`/contact`** - on POST, saves the message to `messages.json`
- **`/order-confirmed`** - confirmation page that appears after a succesful order

### Cart

The cart is stored in Flask's  session cookie as a dictionary of `{ product_id: quantity }`.

### Shipping

Computed on both the `/cart` and `/checkout` routes: free for orders $150 and over, $15 otherwise. 
The threshold is also displayed in the announcement bar at the top of every page so the user is aware of it before checkout.

### Templates — Jinja2

All pages extend `_base.html`, which contains the sticky navbar, the announcement bar, and the Bootstrap includes.

### Styling

Bootstrap 5 is used for layout and components (cards, tables, buttons, forms). 
A small `style.css` file adds custom colours,the sticky header and card image sizing.

---

## Design Choices

**Flat JSON files instead of a database** : A JSON fle is simpler to set up than a database, 
although it is slower it's fine for a small scale project like this one.

**Session-based cart** : the cart is stored in Flask's session, which keeps it in the user's browser as a signed cookie.

**Products as a Python list** : the product catalogue is just a list of dictionaries in `products.py`.

**Filter buttons instead of a dropdown** : the type and genre filters are just links styled as buttons, to avoid needing any JavaScript 

**Two-column checkout layout** : the checkout page shows the order summary on the right alongside the form, 
so the user can review their cart without navigating away.

---

## Third-Party Libraries


 **Flask** : Lightweight Python web framework; minimal boilerplate, built-in Jinja2 templating and session handling 
 **Bootstrap 5** : Responsive grid, ready-made components (cards, tables, buttons, navbar), saves writing a lot of CSS from scratch

No other third-party libraries are used. `json` and `os` are from the Python standard library.


