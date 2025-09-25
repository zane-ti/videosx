-- Sellers
CREATE TABLE IF NOT EXISTS sellers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    slug TEXT UNIQUE,
    bio TEXT
);

-- Products
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER,
    title TEXT,
    slug TEXT UNIQUE,
    short_desc TEXT,
    long_desc TEXT,
    filename TEXT,
    price REAL,
    category TEXT,
    published INTEGER DEFAULT 1,
    FOREIGN KEY (seller_id) REFERENCES sellers(id)
);

/* Seed data */
INSERT INTO sellers (name, slug, bio) VALUES ('Test Seller One', 'seller-one', 'Vendedor teste número um');
INSERT INTO sellers (name, slug, bio) VALUES ('Test Seller Two', 'seller-two', 'Vendedor teste número dois');

INSERT INTO products (seller_id, title, slug, short_desc, long_desc, filename, price, category, published)
VALUES
(1, 'Sample Video 1', 'sample-video-1', 'Preview curto do vídeo 1', 'Descrição longa do vídeo 1', 'sample1.mp4', 4.99, 'Category A', 1),
(1, 'Sample Video 2', 'sample-video-2', 'Preview curto do vídeo 2', 'Descrição longa do vídeo 2', 'sample2.mp4', 6.99, 'Category B', 1),
(2, 'Sample Video 3', 'sample-video-3', 'Preview curto do vídeo 3', 'Descrição longa do vídeo 3', 'sample3.mp4', 3.99, 'Category A', 1);
