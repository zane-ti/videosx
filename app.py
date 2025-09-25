from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, abort
import sqlite3, os, json, datetime
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import stripe

app = Flask(__name__, static_folder='frontend/build', static_url_path='/')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "store.db")
VIDEO_FOLDER = os.path.join(BASE_DIR, "videos")

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
stripe.api_key = STRIPE_SECRET_KEY

# token serializer for temporary download links
ts = URLSafeTimedSerializer(app.secret_key)

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript(open(os.path.join(BASE_DIR, "schema_full.sql")).read())
    conn.commit()
    conn.close()

if not os.path.exists(DB_PATH):
    init_db()
if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)

# Simple auth helpers
def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    conn = get_db()
    u = conn.execute("SELECT id,username,is_seller FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return u

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    is_seller = 1 if data.get("is_seller") else 0
    if not username or not password:
        return jsonify({"error":"missing"}), 400
    pw = generate_password_hash(password)
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username,password_hash,is_seller) VALUES (?,?,?)", (username,pw,is_seller))
        conn.commit()
        uid = cur.lastrowid
    except Exception as e:
        conn.close()
        return jsonify({"error":"username_taken"}), 400
    conn.close()
    session["user_id"] = uid
    return jsonify({"ok":True,"user_id":uid})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if not u or not check_password_hash(u["password_hash"], password):
        return jsonify({"error":"invalid"}), 400
    session["user_id"] = u["id"]
    return jsonify({"ok":True,"user_id":u["id"], "is_seller": bool(u["is_seller"])})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("user_id", None)
    return jsonify({"ok":True})

# Products API
@app.route("/api/products")
def api_products():
    conn = get_db()
    rows = conn.execute("SELECT p.*, u.username as seller_name FROM products p LEFT JOIN users u ON p.seller_id = u.id WHERE p.published=1").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/product/<int:pid>")
def api_product(pid):
    conn = get_db()
    p = conn.execute("SELECT p.*, u.username as seller_name FROM products p LEFT JOIN users u ON p.seller_id = u.id WHERE p.id = ?", (pid,)).fetchone()
    conn.close()
    if not p:
        return jsonify({"error":"notfound"}), 404
    return jsonify(dict(p))

# Seller upload (basic)
@app.route("/api/seller/upload", methods=["POST"])
def api_seller_upload():
    u = current_user()
    if not u or not u["is_seller"]:
        return jsonify({"error":"unauthorized"}), 403
    if "file" not in request.files:
        return jsonify({"error":"nofile"}), 400
    f = request.files["file"]
    title = request.form.get("title","Untitled")
    price = float(request.form.get("price", "0.0"))
    filename = f.filename
    save_path = os.path.join(VIDEO_FOLDER, filename)
    f.save(save_path)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO products (seller_id,title,slug,short_desc,long_desc,filename,price,category,published) VALUES (?,?,?,?,?,?,?,?,1)",
                (u["id"], title, filename, "upload", "uploaded", filename, price, "Uncategorized"))
    conn.commit()
    conn.close()
    return jsonify({"ok":True})

# Checkout creation for current cart (simple)
@app.route("/api/create-checkout-session", methods=["POST"])
def api_create_checkout_session():
    data = request.json or {}
    items = data.get("items", [])
    if not items:
        return jsonify({"error":"empty"}), 400
    line_items = []
    conn = get_db()
    for it in items:
        pid = int(it.get("product_id"))
        qty = int(it.get("quantity",1))
        prod = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if not prod:
            continue
        line_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {"name": prod["title"], "description": prod["short_desc"]},
                "unit_amount": int(float(prod["price"])*100)
            },
            "quantity": qty
        })
    conn.close()
    if not line_items:
        return jsonify({"error":"no_valid_items"}), 400
    host = request.host_url.rstrip("/")
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=host + "/?checkout=success",
            cancel_url=host + "/"
        )
    except Exception as e:
        return jsonify({"error":str(e)}), 500
    return jsonify({"url": checkout_session.url})

# Stripe webhook to mark orders and create download tokens
@app.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")
    event = None
    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except ValueError as e:
            return "Invalid payload", 400
        except stripe.error.SignatureVerificationError as e:
            return "Invalid signature", 400
    else:
        # No webhook secret provided — attempt to parse event for local testing
        try:
            event = json.loads(payload)
        except:
            return "Invalid payload", 400

    # Handle checkout.session.completed
    if event and event.get("type") == "checkout.session.completed":
        session_obj = event["data"]["object"]
        # In a real integration you'd lookup line items and products; here we'll create a simple order record
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO orders (stripe_session_id,paid,created_at) VALUES (?,?,datetime('now'))", (session_obj.get("id"),1))
        order_id = cur.lastrowid
        # For demo: generate download tokens for products - this example skips mapping line items to product IDs.
        # A proper implementation requires attaching metadata to Stripe line items or using the API to fetch them.
        conn.commit()
        conn.close()
        return "", 200

    return "", 200

# Generate temporary download link token (signed)
@app.route("/api/download-token/<int:pid>", methods=["POST"])
def api_download_token(pid):
    # Only after verifying order or if you're admin - for simplicity allow if user is logged in
    u = current_user()
    if not u:
        return jsonify({"error":"login_required"}), 403
    token = ts.dumps({"pid": pid, "user": u["id"]})
    # store token in DB
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO download_tokens (product_id,user_id,token,created_at) VALUES (?,?,?,datetime('now'))", (pid,u["id"],token))
    conn.commit()
    conn.close()
    return jsonify({"token":token, "url": url_for("download_file", token=token, _external=True)})

@app.route("/download/<token>")
def download_file(token):
    try:
        data = ts.loads(token, max_age=60*60*24)  # 24h validity
    except SignatureExpired:
        return "Link expirado", 400
    except BadSignature:
        return "Link inválido", 400
    pid = data.get("pid")
    conn = get_db()
    p = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    conn.close()
    if not p:
        return "Produto não encontrado", 404
    # send file
    return send_from_directory(VIDEO_FOLDER, p["filename"], as_attachment=True)

# Serve React frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=True)
