# SmartCart 🛒

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-brightgreen?style=for-the-badge&logo=render)](https://smartcart-lp8d.onrender.com)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-blue?style=for-the-badge&logo=github)](https://github.com/kishore459/SmartCart)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Razorpay](https://img.shields.io/badge/Razorpay-Payments-02042B?style=for-the-badge&logo=razorpay&logoColor=3395FF)](https://razorpay.com/)

> **A full-stack e-commerce web application built with Python Flask and MySQL / SQLite, featuring user authentication, admin management, product management, image uploads, shopping cart, and secure online payments.**

---

## 🌐 Live Demo

- **Application URL:** [https://smartcart-lp8d.onrender.com](https://smartcart-lp8d.onrender.com)
- **Source Code:** [https://github.com/kishore459/SmartCart](https://github.com/kishore459/SmartCart)

---

## ✨ Features

### 🛍️ Customer Portal
- **User Authentication:** Sign up, sign in, and sign out with `bcrypt` encrypted passwords.
- **Password Recovery:** Reset forgotten passwords securely using an email OTP verification flow.
- **Product Catalog:** Browse products with categories, search, view high-resolution images, pricing, and stock details.
- **Session-based Cart:** Add items to cart, adjust quantities dynamically, and remove items with instant total calculations.
- **Checkout & Orders:** Enter shipping/delivery address, place orders, and review past order history with tracking status.
- **Online Payment:** Integrated **Razorpay** payment gateway for secure online transactions.
- **Invoices:** Instant order invoice generation and download after payment confirmation.

### 🛡️ Administrator Portal
- **Secure Admin Access:** Administrator sign up and login with email OTP verification.
- **Analytics Dashboard:** Overview of products, orders, and customer activity.
- **Product Management (CRUD):** Add new items, update product details/pricing, upload product images, and delete listings.
- **Profile & Image Management:** Upload and manage admin profile images.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3, Flask, Jinja2 Templates, Gunicorn |
| **Database** | SQLite (default / production-ready), MySQL (supported via schema & migration scripts) |
| **Authentication & Security** | Flask Sessions, `bcrypt` password hashing, OTP email verification |
| **Email Services** | `Flask-Mail` via SMTP (Gmail / Custom SMTP) |
| **Payment Gateway** | Razorpay Python SDK & Checkout JS |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Deployment** | Render, PythonAnywhere |

---

## 📁 Project Structure

```text
SmartCart/
├── app.py                         # Application entry point, routes, and business logic
├── config.py                      # Application configuration and environment variables
├── config.example.py              # Configuration template with placeholder credentials
├── requirements.txt               # Python package dependencies (Flask, bcrypt, razorpay, etc.)
├── DEPLOY_PYTHONANYWHERE.md       # PythonAnywhere deployment guide
├── pythonanywhere_wsgi.py.example # WSGI configuration template
├── database/
│   ├── schema_sqlite.sql          # SQLite schema
│   ├── schema.sql                 # MySQL schema
│   ├── migrate_mysql_to_sqlite.py # MySQL to SQLite data migration script
│   ├── migrations/                # Database migration scripts
│   ├── seeds/                     # Starter catalog seeds
│   └── smartcart.db               # SQLite database file
├── static/
│   ├── css/
│   │   └── style.css              # Custom styling & responsive layouts
│   ├── js/                        # Client-side scripts & interactivity
│   └── uploads/
│       └── product_images/        # Uploaded product images
└── templates/
    ├── admin/                     # Admin portal templates
    └── user/                      # Customer-facing storefront templates
```

---

## 🚀 Getting Started

Follow these instructions to run the application locally on your machine.

### Prerequisites
- Python 3.8+ installed ([python.org](https://www.python.org/))
- Git installed ([git-scm.com](https://git-scm.com/))

---

### 1. Clone the Repository

```bash
git clone https://github.com/kishore459/SmartCart.git
cd SmartCart
```

### 2. Create and Activate Virtual Environment

**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Application Secrets

Copy `config.example.py` to create your local `config.py`:

**On Windows:**
```powershell
copy config.example.py config.py
```

**On macOS / Linux:**
```bash
cp config.example.py config.py
```

Edit `config.py` with your credentials:
```python
SECRET_KEY = "your-random-secret-key"

# Email Configuration (for OTP verification)
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = "your-email@gmail.com"
MAIL_PASSWORD = "your-app-password"

# Razorpay Test Credentials
RAZORPAY_KEY_ID = "rzp_test_xxxxxx"
RAZORPAY_KEY_SECRET = "your-razorpay-secret"
```

> ⚠️ **Note:** `config.py` is included in `.gitignore` to prevent leaking private credentials.

### 5. Run the Application

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser. The database and starter tables are initialized automatically on startup.

---

## ☁️ Deployment

### Deploying on Render (Live)

1. Create a new **Web Service** on [Render](https://render.com/).
2. Connect your GitHub repository: `https://github.com/kishore459/SmartCart`.
3. Set the following build and start parameters:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. In the **Environment Variables** section, configure:
   - `SECRET_KEY`
   - `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`
   - `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`
5. Deploy the service. Your live application will be available at your Render URL (e.g., `https://smartcart-lp8d.onrender.com`).

### Deploying on PythonAnywhere

Detailed step-by-step instructions for deploying to PythonAnywhere are available in [DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md).

---

## 🗄️ Database Management

- The project defaults to **SQLite** for ease of development and single-server deployments.
- To use an existing **MySQL** database or migrate existing data into SQLite, run the helper utility:
  ```bash
  python database/migrate_mysql_to_sqlite.py
  ```

---

## 🔒 Security Best Practices

- Always keep sensitive credentials out of version control.
- Passwords are encrypted with `bcrypt` before storage.
- Admin routes and checkout endpoints are protected with session validations.
- For production, configure HTTPS and set appropriate CORS/cookie flags.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
