-- Run once for an existing SmartCart database.
ALTER TABLE orders
    ADD COLUMN customer_name VARCHAR(100) DEFAULT NULL,
    ADD COLUMN customer_phone VARCHAR(15) DEFAULT NULL,
    ADD COLUMN delivery_address TEXT DEFAULT NULL,
    ADD COLUMN pin_code VARCHAR(10) DEFAULT NULL,
    ADD COLUMN delivery_type VARCHAR(30) DEFAULT NULL,
    ADD COLUMN delivery_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    ADD COLUMN payment_method VARCHAR(30) DEFAULT NULL;
