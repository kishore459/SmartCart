"""Copy this file to config.py and replace the placeholder values."""

import os

SECRET_KEY = "replace-with-a-long-random-secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.environ.get(
    "SMARTCART_DATABASE_PATH",
    os.path.join(BASE_DIR, "database", "smartcart.db"),
)

MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = "your-email@example.com"
MAIL_PASSWORD = "your-email-app-password"

RAZORPAY_KEY_ID = "your-razorpay-key-id"
RAZORPAY_KEY_SECRET = "your-razorpay-key-secret"
