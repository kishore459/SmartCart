-- Run this once only if your smartcart_db database already exists.
ALTER TABLE users ADD COLUMN profile_image VARCHAR(255) DEFAULT NULL;
