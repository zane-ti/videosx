-- users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    is_seller INTEGER DEFAULT 0
);

-- sellers can be users with is_seller=1

-- products
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER,
    title TEXT,
    slug TEXT,
    short_desc TEXT,
    long_desc TEXT,
    filename TEXT,
    price REAL,
    category TEXT,
    published INTEGER DEFAULT 1,
    FOREIGN KEY (seller_id) REFERENCES users(id)
);

-- orders
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stripe_session_id TEXT,
    paid INTEGER DEFAULT 0,
    created_at TEXT
);

-- download tokens
CREATE TABLE IF NOT EXISTS download_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    user_id INTEGER,
    token TEXT,
    created_at TEXT
);

-- seed: create two users and some products
INSERT INTO users (username,password_hash,is_seller) VALUES ('buyer1', 'REPLACE_WITH_HASH', 0);
INSERT INTO users (username,password_hash,is_seller) VALUES ('seller1', 'REPLACE_WITH_HASH', 1);

INSERT INTO products (seller_id,title,slug,short_desc,long_desc,filename,price,category,published)
VALUES (2, 'Sample Video 1', 'sample-video-1', 'Preview curto do vídeo 1', 'Descrição longa do vídeo 1', 'sample1.mp4', 4.99, 'Category A', 1);

