# app.py
# -----------------------------------------------------------------------------
# SmartCart E-Commerce Platform - Flask Core Application
# Combines Day-1 to Day-13: Admin Signup, OTP, Login, Dashboard, Profile,
# Product Management, User Portal, AJAX Cart, and Razorpay Verification.
# -----------------------------------------------------------------------------

from flask import Flask, render_template, request, redirect, session, flash, jsonify, url_for, Response
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import sqlite3
import bcrypt
import random
import os
import traceback
import uuid
from datetime import datetime, timedelta, timezone
import razorpay
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.after_request
def add_customer_shell(response):
    """Inject shared customer navigation and ensure every app page has a footer."""
    excluded_paths = {'/user-login', '/user-register', '/user/order/download-invoice'}
    is_customer_page = request.path.startswith('/user') and request.path not in excluded_paths
    is_download = 'attachment' in response.headers.get('Content-Disposition', '').lower()
    if response.mimetype == 'text/html' and not is_download:
        page = response.get_data(as_text=True)
        if is_customer_page:
            shell_script = '<script src="/static/js/customer_shell.js?v=3"></script>'
            if shell_script not in page:
                page = page.replace('</body>', shell_script + '</body>')
        elif '<footer' not in page.lower():
            footer = ('<footer class="site-footer"><div class="footer-brand"><strong>SmartCart</strong>'
                      '<p>Everything you love, delivered simply.</p></div>'
                      '<div class="footer-links"><a href="/">Home</a><a href="/user/products">Shop</a>'
                      '<a href="/user-login">My account</a></div>'
                      '<span>&copy; 2026 SmartCart. Shop smarter, live better.</span></footer>')
            page = page.replace('</body>', footer + '</body>')
        responsive_script = '<script src="/static/js/responsive_navigation.js?v=1"></script>'
        if responsive_script not in page:
            page = page.replace('</body>', responsive_script + '</body>')
        # Cache-bust shared CSS after responsive UI updates.
        page = page.replace('/static/css/style.css"', '/static/css/style.css?v=mobile-menu-3"')
        response.set_data(page)
    return response

# ---------------------------------------------------------
# 1. FILE UPLOAD CONFIGURATIONS
# ---------------------------------------------------------
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'product_images')
ADMIN_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'admin_profiles')
USER_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'user_profiles')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ADMIN_UPLOAD_FOLDER'] = ADMIN_UPLOAD_FOLDER
app.config['USER_UPLOAD_FOLDER'] = USER_UPLOAD_FOLDER

# Ensure target directories exist on server startup
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ADMIN_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['USER_UPLOAD_FOLDER'], exist_ok=True)


def allowed_image_file(filename):
    """Return True only for the image formats accepted by profile uploads."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_profile_image(image_file, folder):
    """Save an uploaded profile image with a unique, safe filename."""
    original_name = secure_filename(image_file.filename)
    extension = original_name.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"
    image_file.save(os.path.join(folder, filename))
    return filename

# ---------------------------------------------------------
# 2. EMAIL SMTP CONFIGURATION
# ---------------------------------------------------------
app.config['MAIL_SERVER'] = config.MAIL_SERVER
app.config['MAIL_PORT'] = config.MAIL_PORT
app.config['MAIL_USE_TLS'] = config.MAIL_USE_TLS
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD

mail = Mail(app)

# ---------------------------------------------------------
# 3. RAZORPAY CONFIGURATION
# ---------------------------------------------------------
razorpay_client = razorpay.Client(
    auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET)
)

# ---------------------------------------------------------
# 4. DATABASE CONNECTION HELPER
# ---------------------------------------------------------
class SQLiteCursor:
    """Compatibility wrapper for the MySQL-style queries already in this app."""

    def __init__(self, cursor, dictionary=False):
        self._cursor = cursor
        self._dictionary = dictionary

    def execute(self, query, params=None):
        # MySQL Connector uses %s placeholders; sqlite3 uses ? placeholders.
        query = query.replace('%s', '?')
        return self._cursor.execute(query, tuple(params or ()))

    def fetchone(self):
        row = self._cursor.fetchone()
        return dict(row) if row is not None and self._dictionary else row

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [dict(row) for row in rows] if self._dictionary else rows

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def close(self):
        self._cursor.close()


class SQLiteConnection:
    """Expose the small MySQL Connector API surface used by the routes."""

    def __init__(self, connection):
        self._connection = connection

    def cursor(self, dictionary=False):
        return SQLiteCursor(self._connection.cursor(), dictionary=dictionary)

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


def get_db_connection():
    """Create a SQLite connection for the SmartCart database."""
    connection = sqlite3.connect(config.DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys = ON')
    return SQLiteConnection(connection)


def initialize_database():
    """Create the SQLite database and tables on a first application start."""
    database_directory = os.path.dirname(config.DATABASE_PATH)
    if database_directory:
        os.makedirs(database_directory, exist_ok=True)
    schema_path = os.path.join(BASE_DIR, 'database', 'schema_sqlite.sql')
    with sqlite3.connect(config.DATABASE_PATH) as connection:
        connection.execute('PRAGMA foreign_keys = ON')
        with open(schema_path, encoding='utf-8') as schema_file:
            connection.executescript(schema_file.read())


initialize_database()


# =============================================================================
# ROUTE 1: CORE HOME / PORTAL SELECTION
# =============================================================================
@app.route('/')
def home():
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/contact')
def contact():
    return render_template("contact.html", support_email='support@smartcart.com')


# =============================================================================
# ADMIN PORTAL ROUTES (DAYS 2-8)
# =============================================================================

# ---------------------------------------------------------
# ADMIN ROUTE: SIGNUP (SEND OTP)
# ---------------------------------------------------------
@app.route('/admin-signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == "GET":
        return render_template("admin/admin_signup.html")

    name = request.form['name']
    email = request.form['email']

    # 1. Verify if email already exists
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT admin_id FROM admin WHERE email=%s", (email,))
    existing_admin = cursor.fetchone()
    cursor.close()
    conn.close()

    if existing_admin:
        flash("This email is already registered. Please login instead.", "danger")
        return redirect('/admin-signup')

    # 2. Temporarily save details in session
    session['signup_name'] = name
    session['signup_email'] = email

    # 3. Generate random 6-digit OTP
    otp = random.randint(100000, 999999)
    session['otp'] = otp

    # 4. Send OTP email using Flask-Mail
    try:
        message = Message(
            subject="SmartCart Admin OTP Verification",
            sender=config.MAIL_USERNAME,
            recipients=[email]
        )
        message.body = f"Hello {name},\n\nYour OTP for SmartCart Admin Registration is: {otp}\n\nThank you!"
        mail.send(message)
        flash("OTP sent to your email!", "success")
    except Exception as e:
        # Fallback Mechanism: Log verification details to console if SMTP is not set
        app.logger.warning("SMTP failed. Fallback details printed to console.")
        print("\n" + "="*60)
        print(f"[DEVELOPMENT FALLBACK] OTP for {email}: {otp}")
        print("="*60 + "\n")
        flash("OTP sent! (SMTP connection skipped: please check server terminal logs for OTP)", "warning")

    return redirect('/verify-otp')


# ---------------------------------------------------------
# ADMIN ROUTE: VERIFY OTP PAGE
# ---------------------------------------------------------
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == "GET":
        return render_template("admin/verify_otp.html")

    user_otp = request.form['otp']
    password = request.form['password']

    # Verify if OTP matches session
    if str(session.get('otp')) != str(user_otp):
        flash("Invalid OTP! Please try again.", "danger")
        return redirect('/verify-otp')

    # Hash the password using bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Save details into the database
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO admin (name, email, password) VALUES (%s, %s, %s)",
            (session['signup_name'], session['signup_email'], hashed_password)
        )
        conn.commit()
        flash("Admin Registered Successfully! Please Login.", "success")
    except Exception as e:
        conn.rollback()
        app.logger.error("Admin registration failed: %s", str(e))
        flash("Failed to register admin. Please try again.", "danger")
        return redirect('/admin-signup')
    finally:
        cursor.close()
        conn.close()

    # Clear signup session keys
    session.pop('otp', None)
    session.pop('signup_name', None)
    session.pop('signup_email', None)

    return redirect('/admin-login')


# ---------------------------------------------------------
# ADMIN ROUTE: LOGIN
# ---------------------------------------------------------
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return render_template("admin/admin_login.html")

    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admin WHERE email=%s", (email,))
    admin = cursor.fetchone()
    cursor.close()
    conn.close()

    if admin is None:
        flash("Email not found! Please register first.", "danger")
        return redirect('/admin-login')

    # Verify the stored hashed password using bcrypt
    stored_hash = admin['password'].encode('utf-8')
    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
        flash("Incorrect password! Try again.", "danger")
        return redirect('/admin-login')

    # Save credentials in session
    session['admin_id'] = admin['admin_id']
    session['admin_name'] = admin['name']
    session['admin_email'] = admin['email']
    session['admin_image'] = admin['profile_image']

    flash("Welcome back, Login Successful!", "success")
    return redirect('/admin-dashboard')


# ---------------------------------------------------------
# ADMIN ROUTE: PROTECTED DASHBOARD
# ---------------------------------------------------------
@app.route('/admin-dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash("Please login to access dashboard!", "danger")
        return redirect('/admin-login')

    return render_template("admin/dashboard.html", admin_name=session['admin_name'])


# ---------------------------------------------------------
# ADMIN ROUTE: LOGOUT
# ---------------------------------------------------------
@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    session.pop('admin_email', None)
    session.pop('admin_image', None)
    flash("Logged out successfully.", "success")
    return redirect('/admin-login')


# ---------------------------------------------------------
# ADMIN ROUTE: ADD PRODUCT
# ---------------------------------------------------------
@app.route('/admin/add-item', methods=['GET', 'POST'])
def add_item():
    if 'admin_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/admin-login')

    if request.method == 'GET':
        return render_template("admin/add_item.html")

    name = request.form['name']
    description = request.form['description']
    category = request.form['category']
    price = request.form['price']
    image_file = request.files['image']

    if image_file.filename == "":
        flash("Please upload a product image!", "danger")
        return redirect('/admin/add-item')

    # Save the product image securely
    filename = secure_filename(image_file.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image_file.save(image_path)

    # Save product record in MySQL
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO products (name, description, category, price, image) VALUES (%s, %s, %s, %s, %s)",
            (name, description, category, price, filename)
        )
        conn.commit()
        flash("Product added successfully!", "success")
    except Exception as e:
        conn.rollback()
        app.logger.error("DB error adding item: %s", str(e))
        flash("Database insertion failed. Try again.", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect('/admin/item-list')


# ---------------------------------------------------------
# ADMIN ROUTE: PRODUCT LIST (SEARCH + FILTER)
# ---------------------------------------------------------
@app.route('/admin/item-list')
def item_list():
    if 'admin_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/admin-login')

    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Fetch categories for filters select menu
    cursor.execute("SELECT DISTINCT category FROM products")
    categories = cursor.fetchall()

    # 2. Compile SQL queries based on active filters
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE %s"
        params.append("%" + search + "%")

    if category_filter:
        query += " AND category = %s"
        params.append(category_filter)

    cursor.execute(query, params)
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/item_list.html",
        products=products,
        categories=categories
    )


# ---------------------------------------------------------
# ADMIN ROUTE: VIEW SINGLE PRODUCT
# ---------------------------------------------------------
@app.route('/admin/view-item/<int:item_id>')
def view_item(item_id):
    if 'admin_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/admin-login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE product_id = %s", (item_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if not product:
        flash("Product not found!", "danger")
        return redirect('/admin/item-list')

    return render_template("admin/view_item.html", product=product)


# ---------------------------------------------------------
# ADMIN ROUTE: EDIT PRODUCT
# ---------------------------------------------------------
@app.route('/admin/update-item/<int:item_id>', methods=['GET', 'POST'])
def update_item(item_id):
    if 'admin_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/admin-login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE product_id = %s", (item_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        conn.close()
        flash("Product not found!", "danger")
        return redirect('/admin/item-list')

    if request.method == 'GET':
        cursor.close()
        conn.close()
        return render_template("admin/update_item.html", product=product)

    # POST Process updates
    name = request.form['name']
    description = request.form['description']
    category = request.form['category']
    price = request.form['price']
    new_image = request.files['image']

    old_image_name = product['image']

    if new_image and new_image.filename != "":
        new_filename = secure_filename(new_image.filename)
        new_image_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        new_image.save(new_image_path)

        # Delete the old image file if it exists to clean directory
        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image_name)
        if os.path.exists(old_image_path):
            try:
                os.remove(old_image_path)
            except Exception as e:
                app.logger.warning("Could not delete old product file: %s", str(e))

        final_image_name = new_filename
    else:
        final_image_name = old_image_name

    try:
        cursor.execute("""
            UPDATE products
            SET name=%s, description=%s, category=%s, price=%s, image=%s
            WHERE product_id=%s
        """, (name, description, category, price, final_image_name, item_id))
        conn.commit()
        flash("Product updated successfully!", "success")
    except Exception as e:
        conn.rollback()
        app.logger.error("Product edit failed: %s", str(e))
        flash("Product edit database update failed.", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect('/admin/item-list')


# ---------------------------------------------------------
# ADMIN ROUTE: DELETE PRODUCT
# ---------------------------------------------------------
@app.route('/admin/delete-item/<int:item_id>')
def delete_item(item_id):
    if 'admin_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/admin-login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT image FROM products WHERE product_id=%s", (item_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        conn.close()
        flash("Product not found!", "danger")
        return redirect('/admin/item-list')

    image_name = product['image']

    # Delete physical image file
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
    if os.path.exists(image_path):
        try:
            os.remove(image_path)
        except Exception as e:
            app.logger.warning("Could not remove image file: %s", str(e))

    # Delete DB row
    try:
        cursor.execute("DELETE FROM products WHERE product_id=%s", (item_id,))
        conn.commit()
        flash("Product deleted successfully!", "success")
    except Exception as e:
        conn.rollback()
        app.logger.error("Product deletion failed: %s", str(e))
        flash("Failed to delete product from database.", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect('/admin/item-list')


# ---------------------------------------------------------
# ADMIN ROUTE: PROFILE MANAGEMENT
# ---------------------------------------------------------
@app.route('/admin/profile', methods=['GET', 'POST'])
def admin_profile():
    if 'admin_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/admin-login')

    admin_id = session['admin_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admin WHERE admin_id = %s", (admin_id,))
    admin = cursor.fetchone()

    if request.method == 'GET':
        cursor.close()
        conn.close()
        return render_template("admin/admin_profile.html", admin=admin)

    # POST Profile edit details
    name = request.form['name']
    email = request.form['email']
    new_password = request.form['password']
    new_image = request.files['profile_image']

    old_image_name = admin['profile_image']

    # Determine password update status
    if new_password:
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    else:
        hashed_password = admin['password']

    # Determine image update status
    if new_image and new_image.filename != "":
        new_filename = secure_filename(new_image.filename)
        image_path = os.path.join(app.config['ADMIN_UPLOAD_FOLDER'], new_filename)
        new_image.save(image_path)

        # Remove the previous profile image
        if old_image_name:
            old_image_path = os.path.join(app.config['ADMIN_UPLOAD_FOLDER'], old_image_name)
            if os.path.exists(old_image_path):
                try:
                    os.remove(old_image_path)
                except Exception as e:
                    app.logger.warning("Could not delete old avatar: %s", str(e))

        final_image_name = new_filename
    else:
        final_image_name = old_image_name

    try:
        cursor.execute("""
            UPDATE admin
            SET name=%s, email=%s, password=%s, profile_image=%s
            WHERE admin_id=%s
        """, (name, email, hashed_password, final_image_name, admin_id))
        conn.commit()

        # Keep session keys fresh
        session['admin_name'] = name
        session['admin_email'] = email
        session['admin_image'] = final_image_name
        flash("Profile updated successfully!", "success")
    except Exception as e:
        conn.rollback()
        app.logger.error("Admin profile update failed: %s", str(e))
        flash("Failed to update profile values.", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect('/admin/profile')


# =============================================================================
# USER / CUSTOMER PORTAL ROUTES (DAYS 9-13)
# =============================================================================

# ---------------------------------------------------------
# USER ROUTE: REGISTRATION
# ---------------------------------------------------------
@app.route('/user-register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'GET':
        return render_template("user/user_register.html")

    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        conn.close()
        flash("Email already registered! Please login.", "danger")
        return redirect('/user-register')

    # Hash user password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        conn.commit()
        flash("Registration successful! Please login.", "success")
    except Exception as e:
        conn.rollback()
        app.logger.error("User registration failed: %s", str(e))
        flash("Failed to register customer.", "danger")
        return redirect('/user-register')
    finally:
        cursor.close()
        conn.close()

    return redirect('/user-login')


# ---------------------------------------------------------
# USER ROUTE: LOGIN
# ---------------------------------------------------------
@app.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'GET':
        return render_template("user/user_login.html")

    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        flash("Email not found! Please register.", "danger")
        return redirect('/user-login')

    # Verify password hash
    stored_hash = user['password'].encode('utf-8')
    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
        flash("Incorrect password!", "danger")
        return redirect('/user-login')

    # Establish user session
    session['user_id'] = user['user_id']
    session['user_name'] = user['name']
    session['user_email'] = user['email']
    session['user_image'] = user.get('profile_image')

    flash("Login successful! Welcome back.", "success")
    return redirect('/user-dashboard')


# ---------------------------------------------------------
# USER ROUTES: FORGOT PASSWORD
# ---------------------------------------------------------
@app.route('/user-forgot-password', methods=['GET', 'POST'])
def user_forgot_password():
    """Email a short-lived OTP that lets a customer choose a new password."""
    if request.method == 'GET':
        return render_template('user/forgot_password.html')

    email = request.form.get('email', '').strip().lower()
    if not email:
        flash('Please enter your email address.', 'danger')
        return redirect('/user-forgot-password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT user_id FROM users WHERE email=%s', (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    # Return the same message for known and unknown addresses.
    if user:
        otp = str(random.randint(100000, 999999))
        session['password_reset_email'] = email
        session['password_reset_otp'] = otp
        session['password_reset_expires_at'] = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        try:
            message = Message('SmartCart password reset code', sender=config.MAIL_USERNAME, recipients=[email])
            message.body = f'Your SmartCart password reset code is {otp}. It expires in 10 minutes.'
            mail.send(message)
        except Exception as error:
            app.logger.error('Password reset email failed: %s', error)
            app.logger.warning('[DEVELOPMENT FALLBACK] Password reset OTP for %s: %s', email, otp)

    flash('If an account exists for that email, a reset code has been sent.', 'success')
    return redirect('/user-reset-password')


@app.route('/user-reset-password', methods=['GET', 'POST'])
def user_reset_password():
    """Verify the emailed OTP and replace the customer's password hash."""
    reset_email = session.get('password_reset_email')
    reset_otp = session.get('password_reset_otp')
    expires_at = session.get('password_reset_expires_at')
    if not reset_email or not reset_otp or not expires_at:
        flash('Request a new password reset code first.', 'danger')
        return redirect('/user-forgot-password')
    try:
        is_expired = datetime.now(timezone.utc) > datetime.fromisoformat(expires_at)
    except ValueError:
        is_expired = True
    if is_expired:
        for key in ('password_reset_email', 'password_reset_otp', 'password_reset_expires_at'):
            session.pop(key, None)
        flash('That reset code has expired. Please request a new one.', 'danger')
        return redirect('/user-forgot-password')
    if request.method == 'GET':
        return render_template('user/reset_password.html', email=reset_email)

    otp = request.form.get('otp', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    if otp != reset_otp:
        flash('The reset code is incorrect.', 'danger')
        return redirect('/user-reset-password')
    if len(password) < 8:
        flash('Your new password must be at least 8 characters.', 'danger')
        return redirect('/user-reset-password')
    if password != confirm_password:
        flash('The new passwords do not match.', 'danger')
        return redirect('/user-reset-password')

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password=%s WHERE email=%s', (hashed_password, reset_email))
    conn.commit()
    cursor.close()
    conn.close()
    for key in ('password_reset_email', 'password_reset_otp', 'password_reset_expires_at'):
        session.pop(key, None)
    flash('Your password has been reset. Please log in.', 'success')
    return redirect('/user-login')


# ---------------------------------------------------------
# USER ROUTE: PROTECTED DASHBOARD (SHOPPING HOMEPAGE)
# ---------------------------------------------------------
@app.route('/user-dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-login')

    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch unique category list
    cursor.execute("SELECT DISTINCT category FROM products")
    categories = cursor.fetchall()

    # Dynamic SQL builder
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE %s"
        params.append("%" + search + "%")

    if category_filter:
        query += " AND category = %s"
        params.append(category_filter)

    cursor.execute(query, params)
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "user/user_home.html",
        user_name=session['user_name'],
        products=products,
        categories=categories
    )


# ---------------------------------------------------------
# USER ROUTE: PROFILE MANAGEMENT
# ---------------------------------------------------------
@app.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE user_id=%s", (session['user_id'],))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        session.clear()
        flash("Your account could not be found. Please login again.", "danger")
        return redirect('/user-login')

    if request.method == 'GET':
        cursor.close()
        conn.close()
        return render_template('user/user_profile.html', user=user)

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    new_password = request.form.get('password', '')
    new_image = request.files.get('profile_image')

    if not name or not email:
        cursor.close()
        conn.close()
        flash("Name and email are required.", "danger")
        return redirect('/user/profile')

    if new_image and new_image.filename and not allowed_image_file(new_image.filename):
        cursor.close()
        conn.close()
        flash("Please upload a PNG, JPG, JPEG, GIF, or WEBP image.", "danger")
        return redirect('/user/profile')

    hashed_password = (bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                       if new_password else user['password'])
    final_image_name = user.get('profile_image')

    if new_image and new_image.filename:
        final_image_name = save_profile_image(new_image, app.config['USER_UPLOAD_FOLDER'])

    try:
        cursor.execute(
            "UPDATE users SET name=%s, email=%s, password=%s, profile_image=%s WHERE user_id=%s",
            (name, email, hashed_password, final_image_name, session['user_id'])
        )
        conn.commit()

        old_image_name = user.get('profile_image')
        if new_image and new_image.filename and old_image_name:
            old_image_path = os.path.join(app.config['USER_UPLOAD_FOLDER'], old_image_name)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        session['user_name'] = name
        session['user_email'] = email
        session['user_image'] = final_image_name
        flash("Profile updated successfully!", "success")
    except Exception as e:
        conn.rollback()
        app.logger.error("User profile update failed: %s", str(e))
        flash("Failed to update your profile.", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect('/user/profile')


# ---------------------------------------------------------
# USER ROUTE: LOGOUT
# ---------------------------------------------------------
@app.route('/user-logout')
def user_logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('user_image', None)
    flash("Logged out successfully!", "success")
    return redirect('/user-login')


# ---------------------------------------------------------
# USER ROUTE: CATALOG SELECTION (REDIRECT TO DASHBOARD)
# ---------------------------------------------------------
@app.route('/user/products')
def user_products():
    return redirect(url_for('user_dashboard', **request.args))


# ---------------------------------------------------------
# USER ROUTE: PRODUCT DETAILS
# ---------------------------------------------------------
@app.route('/user/product/<int:product_id>')
def user_product_details(product_id):
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if not product:
        flash("Product not found!", "danger")
        return redirect('/user/products')

    return render_template("user/product_details.html", product=product)


# ---------------------------------------------------------
# USER ROUTE: CART ADD (AJAX ENDPOINT)
# ---------------------------------------------------------
@app.route('/user/add-to-cart-ajax/<int:product_id>')
def add_to_cart_ajax(product_id):
    if 'user_id' not in session:
        return jsonify({"error": "not_logged_in"}), 401

    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']

    # Retrieve product info from database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE product_id=%s", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if not product:
        return jsonify({"error": "Product not found"}), 404

    pid = str(product_id)

    # Add item or increment quantity
    if pid in cart:
        cart[pid]['quantity'] += 1
    else:
        cart[pid] = {
            'name': product['name'],
            'price': float(product['price']),
            'image': product['image'],
            'quantity': 1
        }

    session['cart'] = cart
    session.modified = True

    return jsonify({
        "message": f"'{product['name']}' added to cart successfully!",
        "cart_count": len(cart)
    })


# ---------------------------------------------------------
# USER ROUTE: CART ADD (SYNC FALLBACK)
# ---------------------------------------------------------
@app.route('/user/add-to-cart/<int:product_id>')
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-login')

    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE product_id=%s", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if not product:
        flash("Product not found.", "danger")
        return redirect(request.referrer or '/user/products')

    pid = str(product_id)

    if pid in cart:
        cart[pid]['quantity'] += 1
    else:
        cart[pid] = {
            'name': product['name'],
            'price': float(product['price']),
            'image': product['image'],
            'quantity': 1
        }

    session['cart'] = cart
    session.modified = True

    flash("Item added to cart!", "success")
    return redirect(request.referrer or '/user/cart')


# ---------------------------------------------------------
# USER ROUTE: VIEW SHOPPING CART
# ---------------------------------------------------------
@app.route('/user/cart')
def view_cart():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-login')

    cart = session.get('cart', {})
    
    # Calculate grand total amount
    grand_total = sum(item['price'] * item['quantity'] for item in cart.values())

    return render_template("user/cart.html", cart=cart, grand_total=grand_total)


# ---------------------------------------------------------
# USER ROUTE: CART QUANTITY CONTROLS
# ---------------------------------------------------------
@app.route('/user/cart/increase/<pid>')
def increase_quantity(pid):
    cart = session.get('cart', {})

    if pid in cart:
        cart[pid]['quantity'] += 1

    session['cart'] = cart
    session.modified = True
    return redirect('/user/cart')


@app.route('/user/cart/decrease/<pid>')
def decrease_quantity(pid):
    cart = session.get('cart', {})

    if pid in cart:
        cart[pid]['quantity'] -= 1
        if cart[pid]['quantity'] <= 0:
            cart.pop(pid)

    session['cart'] = cart
    session.modified = True
    return redirect('/user/cart')


@app.route('/user/cart/remove/<pid>')
def remove_from_cart(pid):
    cart = session.get('cart', {})

    if pid in cart:
        cart.pop(pid)

    session['cart'] = cart
    session.modified = True

    flash("Item removed from your cart.", "success")
    return redirect('/user/cart')


# =============================================================================
# PAYMENTS & TRANSACTIONS MANAGEMENT (DAYS 12-13)
# =============================================================================

DELIVERY_OPTIONS = {
    'standard': {'label': 'Standard delivery (3–5 business days)', 'fee': 0},
    'express': {'label': 'Express delivery (1–2 business days)', 'fee': 149},
}


def create_order_record(user_id, cart, checkout_details, payment_method, payment_status,
                        razorpay_order_id, razorpay_payment_id):
    """Store the confirmed cart, payment, and delivery details as one transaction."""
    delivery_fee = DELIVERY_OPTIONS[checkout_details['delivery_type']]['fee']
    item_total = sum(item['price'] * item['quantity'] for item in cart.values())
    total_amount = item_total + delivery_fee
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO orders (user_id, razorpay_order_id, razorpay_payment_id, amount, payment_status,
                customer_name, customer_phone, delivery_address, pin_code, delivery_type, delivery_fee, payment_method)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, razorpay_order_id, razorpay_payment_id, total_amount, payment_status,
              checkout_details['customer_name'], checkout_details['customer_phone'], checkout_details['delivery_address'],
              checkout_details['pin_code'], checkout_details['delivery_type'], delivery_fee, payment_method))
        order_db_id = cursor.lastrowid
        for pid_str, item in cart.items():
            cursor.execute("""INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                              VALUES (%s, %s, %s, %s, %s)""",
                           (order_db_id, int(pid_str), item['name'], item['quantity'], item['price']))
        conn.commit()
        return order_db_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


@app.route('/user/checkout', methods=['GET', 'POST'])
def user_checkout():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-login')
    cart = session.get('cart', {})
    if not cart:
        flash("Your cart is empty! Add products first.", "danger")
        return redirect('/user/products')

    item_total = sum(item['price'] * item['quantity'] for item in cart.values())
    if request.method == 'GET':
        return render_template('user/checkout.html', item_total=item_total,
                               saved_details=session.get('checkout_details', {}),
                               delivery_options=DELIVERY_OPTIONS)

    details = {
        'customer_name': request.form.get('customer_name', '').strip(),
        'customer_phone': request.form.get('customer_phone', '').strip(),
        'delivery_address': request.form.get('delivery_address', '').strip(),
        'pin_code': request.form.get('pin_code', '').strip(),
        'delivery_type': request.form.get('delivery_type', 'standard'),
    }
    payment_method = request.form.get('payment_method', '')
    if (not details['customer_name'] or not details['customer_phone'].isdigit() or len(details['customer_phone']) != 10 or
            len(details['delivery_address']) < 10 or not details['pin_code'].isdigit() or len(details['pin_code']) != 6 or
            details['delivery_type'] not in DELIVERY_OPTIONS or payment_method not in {'online', 'cash_on_delivery'}):
        flash("Enter a valid name, 10-digit phone number, complete address, and 6-digit PIN code.", "danger")
        return redirect('/user/checkout')

    session['checkout_details'] = details
    session.modified = True
    if payment_method == 'cash_on_delivery':
        try:
            order_db_id = create_order_record(session['user_id'], cart, details, 'cash_on_delivery',
                'cash_on_delivery', f"COD-{uuid.uuid4().hex[:12].upper()}", 'Not applicable')
            session.pop('cart', None)
            session.pop('checkout_details', None)
            flash("Order placed successfully. Please pay cash when it is delivered.", "success")
            return redirect(url_for('order_success', order_db_id=order_db_id))
        except Exception as e:
            app.logger.error("Cash-on-delivery order failed: %s", str(e))
            flash("We could not place your order. Please try again.", "danger")
            return redirect('/user/checkout')
    return redirect('/user/pay')

# ---------------------------------------------------------
# USER ROUTE: INIT RAZORPAY PAYMENT
# ---------------------------------------------------------
@app.route('/user/pay')
def user_pay():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-login')

    cart = session.get('cart', {})
    if not cart:
        flash("Your cart is empty! Add products first.", "danger")
        return redirect('/user/products')

    checkout_details = session.get('checkout_details')
    if not checkout_details:
        flash("Please enter delivery details before payment.", "danger")
        return redirect('/user/checkout')

    # Calculate payment totals
    item_total = sum(item['price'] * item['quantity'] for item in cart.values())
    delivery_fee = DELIVERY_OPTIONS[checkout_details['delivery_type']]['fee']
    total_amount = item_total + delivery_fee
    
    # Razorpay requires amount in Paise (1 INR = 100 Paise)
    razorpay_amount = int(total_amount * 100)

    try:
        # Create Razorpay Order
        razorpay_order = razorpay_client.order.create({
            "amount": razorpay_amount,
            "currency": "INR",
            "payment_capture": "1"
        })
    except Exception as e:
        app.logger.error("Razorpay order creation failed: %s", str(e))
        flash("Failed to generate payment gateway order. Try again.", "danger")
        return redirect('/user/cart')

    # Store order reference key in session
    session['razorpay_order_id'] = razorpay_order['id']

    return render_template(
        "user/payment.html",
        amount=total_amount,
        item_total=item_total,
        delivery_fee=delivery_fee,
        checkout_details=checkout_details,
        amount_paise=razorpay_amount,
        key_id=config.RAZORPAY_KEY_ID,
        order_id=razorpay_order['id']
    )


# ---------------------------------------------------------
# USER ROUTE: SIGNATURE VERIFY & DB WRITER
# ---------------------------------------------------------
@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    if 'user_id' not in session:
        flash("Please login to complete the payment.", "danger")
        return redirect('/user-login')

    # Retrieve checkout POST verification values
    razorpay_payment_id = request.form.get('razorpay_payment_id')
    razorpay_order_id = request.form.get('razorpay_order_id')
    razorpay_signature = request.form.get('razorpay_signature')

    if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
        flash("Payment verification failed (Missing parameters).", "danger")
        return redirect('/user/cart')

    # Setup verification payload
    payload = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }

    try:
        # Verifies signature authenticity. Raises error if signature invalid.
        razorpay_client.utility.verify_payment_signature(payload)
    except Exception as e:
        app.logger.error("Razorpay signature mismatch: %s", str(e))
        flash("Payment gateway signature verification failed. Untrusted request.", "danger")
        return redirect('/user/cart')

    # Signature is authenticated! Let's insert into database.
    user_id = session['user_id']
    cart = session.get('cart', {})
    checkout_details = session.get('checkout_details')

    if not cart or not checkout_details:
        flash("Session cart is empty. Cannot generate transaction.", "danger")
        return redirect('/user/checkout')

    try:
        order_db_id = create_order_record(user_id, cart, checkout_details, 'online', 'paid',
                                          razorpay_order_id, razorpay_payment_id)

        # Pop session cart contents
        session.pop('cart', None)
        session.pop('razorpay_order_id', None)
        session.pop('checkout_details', None)

        flash("Order placed and payment successfully completed!", "success")
        return redirect(url_for('order_success', order_db_id=order_db_id))

    except Exception as e:
        app.logger.error("Order transaction record insertion failed: %s\n%s", str(e), traceback.format_exc())
        flash("Error recording checkout status in database. Contact help support.", "danger")
        return redirect('/user/cart')


# ---------------------------------------------------------
# USER ROUTE: TEMP SUCCESS LANDING (GET FALLBACK)
# ---------------------------------------------------------
@app.route('/payment-success')
def payment_success():
    payment_id = request.args.get('payment_id')
    order_id = request.args.get('order_id')
    
    if not payment_id:
        flash("Payment reference missing.", "danger")
        return redirect('/user/cart')

    return render_template(
        "user/payment_success.html",
        payment_id=payment_id,
        order_id=order_id
    )


# ---------------------------------------------------------
# USER ROUTE: FINAL CONFIRMATION & INVOICE
# ---------------------------------------------------------
@app.route('/user/order-success/<int:order_db_id>')
def order_success(order_db_id):
    if 'user_id' not in session:
        flash("Please login to view invoice details.", "danger")
        return redirect('/user-login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Verify if order exists and matches logged-in user for security
    cursor.execute("SELECT * FROM orders WHERE order_id=%s AND user_id=%s", (order_db_id, session['user_id']))
    order = cursor.fetchone()

    if not order:
        cursor.close()
        conn.close()
        flash("Invoice order reference not found.", "danger")
        return redirect('/user/products')

    # Fetch corresponding cart items
    cursor.execute("SELECT * FROM order_items WHERE order_id=%s", (order_db_id,))
    items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("user/order_success.html", order=order, items=items)


# ---------------------------------------------------------
# USER ROUTE: DOWNLOAD INVOICE (DAY 14)
# ---------------------------------------------------------
@app.route('/user/order/download-invoice/<int:order_db_id>')
def download_invoice(order_db_id):
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch order details
    cursor.execute("SELECT * FROM orders WHERE order_id=%s AND user_id=%s", (order_db_id, session['user_id']))
    order = cursor.fetchone()

    if not order:
        cursor.close()
        conn.close()
        flash("Order not found.", "danger")
        return redirect('/user/my-orders')

    # Fetch items
    cursor.execute("SELECT * FROM order_items WHERE order_id=%s", (order_db_id,))
    items = cursor.fetchall()

    cursor.close()
    conn.close()

    item_count = sum(item['quantity'] for item in items)
    product_names = [item['product_name'] for item in items]
    product_summary = ', '.join(product_names[:2])
    if len(product_names) > 2:
        product_summary += f" and {len(product_names) - 2} more item(s)"

    if order['amount'] >= 50000:
        motivation = f"Your investment in {product_summary} is a strong step toward doing more with confidence."
    elif order['amount'] >= 10000:
        motivation = f"Great choice! Enjoy every moment with {product_summary}; quality choices add value to everyday life."
    else:
        motivation = f"Every smart choice counts. We hope {product_summary} makes your day a little better."

    invoice_html = render_template(
        'user/invoice.html',
        order=order,
        items=items,
        customer_name=order.get('customer_name') or session.get('user_name', 'Customer'),
        customer_email=session.get('user_email', ''),
        item_count=item_count,
        items_total=sum(item['price'] * item['quantity'] for item in items),
        delivery_fee=order.get('delivery_fee') or 0,
        motivation=motivation
    )
    return Response(
        invoice_html,
        mimetype='text/html; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename=invoice_order_{order_db_id}.html'}
    )

    # Generate a beautiful HTML content for the downloaded file
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Invoice - SmartCart Order #{order['order_id']}</title>
    <style>
        body {{ font-family: 'Outfit', sans-serif; padding: 30px; color: #333; line-height: 1.6; background-color: #f8fafc; }}
        .invoice-box {{ max-width: 800px; margin: auto; border: 1px solid #eee; padding: 40px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); background-color: white; }}
        .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #ddd; padding-bottom: 20px; margin-bottom: 30px; }}
        .company-details {{ text-align: right; }}
        .details-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; margin-bottom: 30px; }}
        th {{ background-color: #f8f9fa; padding: 12px; border-bottom: 2px solid #ddd; }}
        td {{ padding: 12px; border-bottom: 1px solid #eee; }}
        .total-row {{ text-align: right; font-size: 18px; font-weight: bold; color: #6366f1; }}
        .print-btn {{ display: block; width: fit-content; margin: 20px auto 0 auto; background-color: #6366f1; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; font-weight: bold; }}
        @media print {{
            .print-btn {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="invoice-box">
        <div class="header">
            <div>
                <h1 style="margin: 0; color: #6366f1;">🛒 SmartCart Invoice</h1>
                <p style="color: #777; margin: 5px 0 0 0;">Dynamic Purchase Receipt</p>
            </div>
            <div class="company-details">
                <strong>SmartCart Inc.</strong><br>
                Tech Support: billing@smartcart.com<br>
                Date: {order['created_at']}
            </div>
        </div>

        <div class="details-grid">
            <div>
                <h3>Billed To</h3>
                <strong>Customer Name:</strong> {session['user_name']}<br>
                <strong>Email Address:</strong> {session['user_email']}<br>
            </div>
            <div>
                <h3>Payment Info</h3>
                <strong>Order ID:</strong> #{order['order_id']}<br>
                <strong>Razorpay Payment ID:</strong> {order['razorpay_payment_id']}<br>
                <strong>Razorpay Order ID:</strong> {order['razorpay_order_id']}<br>
                <strong>Status:</strong> Paid
            </div>
        </div>

        <h3>Order Items Breakdown</h3>
        <table>
            <thead>
                <tr>
                    <th>Item Name</th>
                    <th style="text-align: center;">Quantity</th>
                    <th style="text-align: right;">Unit Price</th>
                    <th style="text-align: right;">Subtotal</th>
                </tr>
            </thead>
            <tbody>"""

    for item in items:
        subtotal = item['price'] * item['quantity']
        html_content += f"""
                <tr>
                    <td>{item['product_name']}</td>
                    <td style="text-align: center;">{item['quantity']}</td>
                    <td style="text-align: right;">₹{item['price']:.2f}</td>
                    <td style="text-align: right;">₹{subtotal:.2f}</td>
                </tr>"""

    html_content += f"""
            </tbody>
        </table>

        <div class="total-row">
            Grand Total Paid: ₹{order['amount']:.2f}
        </div>

        <button onclick="window.print()" class="print-btn">Print / Save as PDF</button>
    </div>
</body>
</html>"""

    return Response(
        html_content,
        mimetype="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_order_{order_db_id}.html"
        }
    )


# ---------------------------------------------------------
# USER ROUTE: TRANSACTIONS LIST
# ---------------------------------------------------------
@app.route('/user/my-orders')
def my_orders():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/user-login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM orders WHERE user_id=%s ORDER BY created_at DESC",
        (session['user_id'],)
    )
    orders = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("user/my_orders.html", orders=orders)


# ---------------------------------------------------------
# APPLICATION ENTRYPOINT TRIGGER
# ---------------------------------------------------------
if __name__ == '__main__':
    # Start internal web server
    app.run(debug=True)
