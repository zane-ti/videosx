from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import sqlite3, os
from decimal import Decimal

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "store.db")
VIDEO_FOLDER = os.path.join(BASE_DIR, "videos")

# --- Database helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript(open(os.path.join(BASE_DIR, "schema.sql")).read())
    conn.commit()
    conn.close()

# initialize DB if missing
if not os.path.exists(DB_PATH):
    init_db()

# --- Routes ---
@app.route("/")
def index():
    conn = get_db()
    products = conn.execute("SELECT p.*, s.name as seller_name, s.slug as seller_slug FROM products p LEFT JOIN sellers s ON p.seller_id = s.id WHERE p.published=1").fetchall()
    categories = conn.execute("SELECT DISTINCT category FROM products").fetchall()
    conn.close()
    return render_template("index.html", products=products, categories=categories)

@app.route("/category/<cat>")
def category(cat):
    conn = get_db()
    products = conn.execute("SELECT p.*, s.name as seller_name, s.slug as seller_slug FROM products p LEFT JOIN sellers s ON p.seller_id = s.id WHERE p.category = ? AND p.published=1", (cat,)).fetchall()
    conn.close()
    return render_template("category.html", products=products, category=cat)

@app.route("/product/<int:pid>")
def product(pid):
    conn = get_db()
    p = conn.execute("SELECT p.*, s.name as seller_name, s.slug as seller_slug FROM products p LEFT JOIN sellers s ON p.seller_id = s.id WHERE p.id = ?", (pid,)).fetchone()
    conn.close()
    if not p:
        return "Produto não encontrado", 404
    return render_template("product.html", p=p)

@app.route("/seller/<slug>")
def seller(slug):
    conn = get_db()
    s = conn.execute("SELECT * FROM sellers WHERE slug = ?", (slug,)).fetchone()
    if not s:
        conn.close()
        return "Vendedor não encontrado", 404
    products = conn.execute("SELECT * FROM products WHERE seller_id = ? AND published=1", (s["id"],)).fetchall()
    conn.close()
    return render_template("seller.html", seller=s, products=products)

# Simple cart stored in session
def _cart():
    return session.setdefault("cart", {})

@app.route("/cart")
def cart():
    conn = get_db()
    cart = _cart()
    items = []
    total = Decimal("0.00")
    for pid, qty in cart.items():
        row = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if row:
            price = Decimal(str(row["price"]))
            subtotal = price * int(qty)
            total += subtotal
            items.append({"product": row, "qty": int(qty), "subtotal": subtotal})
    conn.close()
    return render_template("cart.html", items=items, total=total)

@app.route("/cart/add/<int:pid>", methods=["POST"])
def cart_add(pid):
    cart = _cart()
    cart[str(pid)] = int(cart.get(str(pid), 0)) + 1
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:pid>", methods=["POST"])
def cart_remove(pid):
    cart = _cart()
    cart.pop(str(pid), None)
    session["cart"] = cart
    return redirect(url_for("cart"))

# Checkout (Stripe Checkout session creation)
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    # This endpoint creates a Stripe Checkout session.
    # Replace with your Stripe secret key in environment variables and uncomment Stripe calls.
    # For security, do NOT commit secret keys to GitHub. Use Render/GitHub secrets.
    try:
        import stripe
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_...replace_me")
    except Exception as e:
        return "Stripe library not configured on the server. Install stripe in requirements.txt and set STRIPE_SECRET_KEY.", 500

    conn = get_db()
    cart = _cart()
    line_items = []
    for pid, qty in cart.items():
        prod = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if prod:
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": prod["title"], "description": prod["short_desc"]},
                    "unit_amount": int(float(prod["price"]) * 100)
                },
                "quantity": int(qty)
            })
    conn.close()
    if not line_items:
        return "Carrinho vazio", 400

    # Create session
    host = request.host_url.rstrip("/")
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=host + url_for("checkout_success"),
            cancel_url=host + url_for("cart")
        )
    except Exception as e:
        return str(e), 500

    return redirect(checkout_session.url, code=303)

@app.route("/checkout-success")
def checkout_success():
    # In production you'd verify webhook and mark orders as paid.
    session.pop("cart", None)
    return render_template("checkout_success.html")

# Serve sample videos from /videos folder (use nginx/static in production)
@app.route("/videos/<path:filename>")
def videos(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
