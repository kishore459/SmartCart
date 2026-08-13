# Deploy SmartCart on PythonAnywhere

This guide walkthroughs deploying your SmartCart Flask application on PythonAnywhere using SQLite for database persistence and setting up environment variables securely.

---

## Step 1: Upload Your Code
You can upload your code either via Git (recommended) or as a ZIP archive:

### Option A: Using Git (Recommended)
1. Push your local repository to a private GitHub repository.
2. Log in to PythonAnywhere, go to the **Consoles** tab, and open a new **Bash** console.
3. Clone your repository (replace `YOUR_GITHUB_USERNAME` and `YOUR_REPO_NAME`):
   ```bash
   git clone https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git ~/SMARTCART-2
   ```

### Option B: Using ZIP Upload
1. Zip your local project directory (excluding folders like `venv`, `__pycache__`, and `database/*.db`).
2. Go to the PythonAnywhere **Files** tab, upload the ZIP archive to your home directory (`/home/YOUR_USERNAME/`), and unzip it using a Bash console:
   ```bash
   unzip SMARTCART-2.zip -d ~/SMARTCART-2
   ```

---

## Step 2: Set Up Virtual Environment and Dependencies
In your PythonAnywhere Bash console, run:
```bash
cd ~/SMARTCART-2
mkvirtualenv --python=/usr/bin/python3.10 smartcart-env
pip install -r requirements.txt
```
> [!NOTE]
> If Python 3.10 is not available in your PythonAnywhere system image, select an available Python version (e.g. `python3.9` or `python3.11`) and match it when configuring the Web app in Step 3.

---

## Step 3: Create and Configure Web App
1. Go to the **Web** tab in PythonAnywhere and click **Add a new web app**.
2. Select **Manual Configuration** (do *not* select Flask, as manual configuration gives you full WSGI control).
3. Select your Python version (e.g., **Python 3.10**).
4. Under the **Virtualenv** section of the Web tab, enter the path:
   ```text
   /home/YOUR_USERNAME/.virtualenvs/smartcart-env
   ```
   *(Replace `YOUR_USERNAME` with your actual PythonAnywhere username).*

---

## Step 4: Configure WSGI and Environment Secrets
On PythonAnywhere, environment variables set in `.bashrc` or local files are not loaded by the WSGI server. The secure and standard way to supply credentials is to set them directly in PythonAnywhere's WSGI file.

1. Under the **Code** section of the Web tab, click the link next to **WSGI configuration file** (it will look like `/var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py`).
2. Replace its entire contents with the following script, replacing placeholders with your actual secrets:

```python
import os
import sys

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/SMARTCART-2'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Keep the SQLite database in the home directory so it survives updates and redeploys
os.environ['SMARTCART_DATABASE_PATH'] = '/home/YOUR_USERNAME/smartcart.db'

# Define your secrets here (these are private to your account and not in git)
os.environ['SECRET_KEY'] = 'your-super-secure-random-key'

# Email / SMTP Secrets
os.environ['MAIL_USERNAME'] = 'your-email@gmail.com'
os.environ['MAIL_PASSWORD'] = 'your-gmail-app-password'

# Razorpay Keys
os.environ['RAZORPAY_KEY_ID'] = 'rzp_live_yourkeyid'
os.environ['RAZORPAY_KEY_SECRET'] = 'yourrazorpaysecretkey'

# Import the app
from app import app as application
```

---

## Step 5: Configure Static Files (Crucial for Images and Styling)
For optimal performance, PythonAnywhere should serve your static CSS, JS, and product images directly instead of routing those requests through Flask.

Under the **Static files** section of the **Web** tab, add the following entry:
- **URL**: `/static/`
- **Directory**: `/home/YOUR_USERNAME/SMARTCART-2/static`

*(Replace `YOUR_USERNAME` with your actual PythonAnywhere username).*

---

## Step 6: Initialize and Run
1. Go back to the top of the **Web** tab and click **Reload**.
2. Visit your site at `http://YOUR_USERNAME.pythonanywhere.com`.
3. On the first load, the app automatically creates `/home/YOUR_USERNAME/smartcart.db` and runs the schema definitions.

If anything goes wrong, check the logs under the **Log files** section on the Web tab (especially the `error.log`).

---

## Troubleshooting & Account Limitations

> [!WARNING]
> **Email Notifications on Free Accounts:**
> PythonAnywhere restricts outgoing non-HTTP traffic on free accounts. This means SMTP connections (e.g., using `smtp.gmail.com` on port 587/465) will fail. If you require email verification/OTP features, you will need a **PythonAnywhere Paid Account** or you must rewrite the email service to use a whitelisted HTTP web API (such as SendGrid or Mailgun HTTP API).

> [!IMPORTANT]
> **Database File Permissions:**
> Ensure the directory where the SQLite database (`/home/YOUR_USERNAME/smartcart.db`) resides has correct write permissions. Since the WSGI file sets the path directly in your home directory, PythonAnywhere's web workers will have read/write access by default.

> [!TIP]
> **Uploading Product Images:**
> When you upload product images on the deployed site, they are written to `/home/YOUR_USERNAME/SMARTCART-2/static/uploads/product_images`. Since PythonAnywhere serves `/static/` statically (configured in Step 5), these uploaded images will render properly immediately without needing web app reloads.

