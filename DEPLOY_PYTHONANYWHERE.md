# Deploy Nexalix on PythonAnywhere (Free Tier)

## 1. Create account and open a Bash console
- Sign up at https://www.pythonanywhere.com/
- Open **Bash** from the dashboard.

## 2. Clone your repo
```bash
git clone https://github.com/DengAchiek/nexalix.git
cd nexalix/nexalix_site
```

## 3. Create and activate virtualenv
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Set production environment variables (recommended)
Create a `.env` in `nexalix_site/` and add:
```env
SECRET_KEY=replace-with-long-random-secret
DEBUG=False
ALLOWED_HOSTS=yourusername.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://yourusername.pythonanywhere.com
SITE_URL=https://yourusername.pythonanywhere.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=you@example.com
EMAIL_HOST_PASSWORD=app-password
DEFAULT_FROM_EMAIL=Nexalix Technologies <you@example.com>
ADMIN_EMAILS=you@example.com
CONTACT_NOTIFICATION_EMAIL=dachiek4@gmail.com
CONTACT_EMAIL=you@example.com
USE_CLOUDINARY_MEDIA=True
CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>
```

Load env vars in Bash session before migrations:
```bash
set -a
source .env
set +a
```

## 5. Migrate, collect static, and create admin user
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 6. Configure web app in PythonAnywhere
1. Go to **Web** tab -> **Add a new web app**.
2. Choose **Manual configuration** and your Python version.
3. Set **Source code** to:
   - `/home/yourusername/nexalix/nexalix_site`
4. Set **Working directory** to:
   - `/home/yourusername/nexalix/nexalix_site`
5. Set **Virtualenv** to:
   - `/home/yourusername/nexalix/nexalix_site/.venv`

## 7. Update WSGI config
Open the WSGI file in PythonAnywhere Web tab and use:
```python
import os
import sys

path = '/home/yourusername/nexalix/nexalix_site'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexalix_site.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

If using `.env`, add before `get_wsgi_application()`:
```python
from pathlib import Path

env_file = Path('/home/yourusername/nexalix/nexalix_site/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.strip().startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())
```

## 8. Static and media mappings in Web tab
Set:
- URL: `/static/` -> Directory: `/home/yourusername/nexalix/nexalix_site/staticfiles`
- URL: `/media/` -> Directory: `/home/yourusername/nexalix/nexalix_site/media`

## 9. Reload app
Click **Reload** in Web tab.

## 10. Update after code changes
```bash
cd ~/nexalix/nexalix_site
source .venv/bin/activate
git pull
set -a; source .env; set +a
python manage.py migrate
python manage.py collectstatic --noinput
```
Then click **Reload** in PythonAnywhere Web tab.
