# config.py
# ------------------------------------
import os

# Secret Keydir
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

# SQLite Database Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.environ.get(
    "SMARTCART_DATABASE_PATH",
    os.path.join(BASE_DIR, "database", "smartcart.db"),
)

# Email SMTP Settings
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USE_TLS = True

MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

# Razorpay Payment Gateway
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")


