-- Starter catalog for SmartCart. The image files belong in static/uploads/product_images/.
UPDATE products SET name='Wireless Headphones', description='Comfortable over-ear headphones with immersive sound.', category='Electronics', price=8999.00, image='wireless-headphones.jpg' WHERE product_id=1;
UPDATE products SET name='Ultrabook Laptop', description='Lightweight laptop for work, learning, and entertainment.', category='Electronics', price=74999.00, image='ultrabook-laptop.jpg' WHERE product_id=2;
UPDATE products SET name='Running Shoes', description='Breathable everyday running shoes with a cushioned sole.', category='Fashion', price=4999.00, image='running-shoes.jpg' WHERE product_id=3;

INSERT INTO products (name, description, category, price, image)
SELECT 'Smart Watch', 'Modern smart watch for activity and notification tracking.', 'Accessories', 12999.00, 'smartwatch.jpg'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name='Smart Watch');

INSERT INTO products (name, description, category, price, image)
SELECT 'Mirrorless Camera', 'Compact high-quality camera for photos and videos.', 'Electronics', 54999.00, 'camera.jpg'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name='Mirrorless Camera');

INSERT INTO products (name, description, category, price, image)
SELECT 'Travel Backpack', 'Spacious daypack with organized compartments.', 'Bags', 3499.00, 'backpack.jpg'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name='Travel Backpack');

INSERT INTO products (name, description, category, price, image)
SELECT 'Skin Care Set', 'A simple daily skin-care essential set.', 'Beauty', 1299.00, 'skincare.jpg'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name='Skin Care Set');

INSERT INTO products (name, description, category, price, image)
SELECT 'Coffee Maker', 'Easy-to-use coffee maker for fresh brews at home.', 'Home & Kitchen', 8999.00, 'coffee-maker.jpg'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name='Coffee Maker');
