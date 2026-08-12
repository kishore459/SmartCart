# Deploy SmartCart on PythonAnywhere

This project now uses SQLite, a lightweight database stored in one file. It is
appropriate for a small project with low-to-moderate write traffic. PythonAnywhere
also offers MySQL if the application later needs many simultaneous writes.

1. Create a PythonAnywhere account, open a **Bash console**, and upload or clone this project into `/home/YOUR_USERNAME/SMARTCART-2`.
2. Create a virtual environment and install the dependencies:

   ```bash
   cd ~/SMARTCART-2
   mkvirtualenv --python=/usr/bin/python3.10 smartcart-env
   pip install -r requirements.txt
   ```

   Select an available Python version if `python3.10` is not offered by your account.
3. On the **Web** tab, add a new Flask web app. Choose **Manual configuration**, set its virtualenv to `/home/YOUR_USERNAME/.virtualenvs/smartcart-env`, and open its WSGI configuration file.
4. Replace the WSGI file contents with [pythonanywhere_wsgi.py.example](pythonanywhere_wsgi.py.example), changing every `YOUR_USERNAME` value.
5. Click **Reload** on the Web tab. The first load creates `/home/YOUR_USERNAME/smartcart.db` and its tables automatically.

Before publishing, replace every secret in `config.py` (Flask secret, SMTP app password, and Razorpay keys). The values currently in that file should be treated as exposed and rotated in their provider dashboards. Do not commit replacement production credentials to a public repository.

## Moving existing MySQL data

Use the included one-time migration script before uploading the finished SQLite file to PythonAnywhere. First make a backup of your MySQL database and the SQLite file, then run this from the project root:

```bash
pip install -r database/requirements-migration.txt
python database/migrate_mysql_to_sqlite.py --host localhost --user YOUR_MYSQL_USER --database smartcart_db
```

Enter the MySQL password when asked. It copies `admin`, `users`, `products`, `orders`, and `order_items`, preserving their IDs. The command refuses to overwrite a SQLite database containing data. If you intentionally want to replace it after backing it up, add `--replace`.

Upload the resulting `database/smartcart.db` to `/home/YOUR_USERNAME/smartcart.db`, or keep it in the project and update `SMARTCART_DATABASE_PATH` in the WSGI file to match its final location.
