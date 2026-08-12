# SmartCart

SmartCart is a full-stack e-commerce web application built with **Python** and
**Flask**. It provides separate customer and administrator experiences for
browsing products, managing a cart, placing orders, and handling payments.

## Features

### Customer portal

- Register, sign in, sign out, and manage a profile image.
- Reset a forgotten password using an email OTP.
- Browse products, view product details, and add products to a session-based cart.
- Update cart quantities and remove cart items.
- Provide checkout and delivery details, place orders, and view order history.
- Pay online through Razorpay and download an invoice after ordering.

### Administrator portal

- Sign up with email OTP verification and sign in securely.
- View the administration dashboard.
- Create, view, update, and delete product listings.
- Upload product images and update the administrator profile image.

## Technology stack

- **Backend:** Python, Flask
- **Database:** SQLite (with MySQL-to-SQLite migration support)
- **Authentication:** Flask sessions and `bcrypt` password hashing
- **Email:** Flask-Mail with SMTP
- **Payments:** Razorpay
- **Frontend:** Jinja templates, HTML, CSS, and JavaScript

## Project structure

```text
SmartCart/
├── app.py                         # Flask routes, business logic, and application entry point
├── config.example.py              # Safe configuration template
├── requirements.txt               # Application dependencies
├── DEPLOY_PYTHONANYWHERE.md       # PythonAnywhere deployment guide
├── pythonanywhere_wsgi.py.example # WSGI configuration template
├── database/
│   ├── schema_sqlite.sql           # SQLite schema
│   ├── schema.sql                  # Original MySQL schema
│   ├── migrate_mysql_to_sqlite.py  # One-time migration utility
│   ├── migrations/                 # Incremental database changes
│   └── seeds/                      # Starter product catalog
├── static/
│   ├── css/style.css               # Application styling
│   ├── js/                         # Navigation and customer UI scripts
│   └── uploads/product_images/     # Starter product images
└── templates/
    ├── admin/                      # Administrator pages
    └── user/                       # Customer pages
```

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/kishore459/SmartCart.git
cd SmartCart
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

On Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure local secrets

Copy `config.example.py` to `config.py`, then set your own Flask secret key,
SMTP credentials, and Razorpay test keys.

```bash
copy config.example.py config.py
```

For macOS/Linux, use `cp config.example.py config.py`.

> `config.py` is intentionally ignored by Git. Never commit passwords, API keys,
> or production credentials.

### 5. Run the application

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser. The SQLite database and required
tables are created automatically when the application starts.

## Database notes

The current application uses SQLite. Its database file is local-only and not
committed to this repository. SQL schemas, migrations, and starter catalog data
are included in `database/`. If you have an existing MySQL database, use
`database/migrate_mysql_to_sqlite.py` to import its data; see
[DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md) for details.

## Deployment

Deployment instructions for PythonAnywhere are available in
[DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md).

## Security

- Keep `config.py`, `.env` files, and database files private.
- Use environment-specific credentials for email and Razorpay.
- Rotate any credential that was previously shared or committed.
