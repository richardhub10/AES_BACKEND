# Deploying the Backend to Render

Create a **Web Service** on Render from this repo.

Suggested settings:
- Environment: `Python 3`
- Build command: `pip install -r requirements.txt && python manage.py migrate`
- Start command: `gunicorn ua_clinic_backend.wsgi:application --chdir backend`

Environment variables (Render dashboard):
- `DJANGO_SECRET_KEY`: required
- `DJANGO_DEBUG`: set to `false` for production
- `DJANGO_ALLOWED_HOSTS`: e.g. `*` (or your Render domain)
- `CORS_ALLOW_ALL_ORIGINS`: `true` for quick testing (tighten later)
- `AES_MASTER_KEY_B64`: required (base64 32-byte key)

Default admin bootstrap (created automatically during `migrate`):
- `DEFAULT_ADMIN_USERNAME`: default `admin`
- `DEFAULT_ADMIN_PASSWORD`: required if you want the admin auto-created
- `DEFAULT_ADMIN_EMAIL`: default `admin@example.com`

Important:
- If you rotate `AES_MASTER_KEY_B64`, previously encrypted data cannot be decrypted.
