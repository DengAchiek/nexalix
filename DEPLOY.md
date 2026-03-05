# Deploy Nexalix (Django)

This project is now prepared for production deployment with environment-based settings.

## 1. Deploy on Render (recommended)

Create a **Web Service** from your Git repository and set:

- Build Command:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

- Start Command:

```bash
gunicorn nexalix_site.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
```

## 2. Required environment variables

Set these in Render dashboard:

- `SECRET_KEY` = long random string
- `DEBUG` = `False`
- `ALLOWED_HOSTS` = `yourdomain.com,www.yourdomain.com`
- `CSRF_TRUSTED_ORIGINS` = `https://yourdomain.com,https://www.yourdomain.com`
- `DATABASE_URL` = your PostgreSQL connection URL
- `SITE_URL` = `https://yourdomain.com`

If you use contact email notifications:

- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`
- `ADMIN_EMAILS`
- `CONTACT_NOTIFICATION_EMAIL` (set this to `dachiek4@gmail.com`)
- `CONTACT_EMAIL`

For persistent media uploads (partner logos, project images, etc.), enable Cloudinary:

- `USE_CLOUDINARY_MEDIA=True`
- `CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>`

Use `.env.example` as reference.

## 3. Database

Use managed PostgreSQL in production and set `DATABASE_URL`.

`settings.py` auto-switches from SQLite to `DATABASE_URL` when provided.

## 4. First-time admin user

After deployment, run once in shell:

```bash
python manage.py createsuperuser
```

## 5. Domain setup

After assigning a custom domain:

1. Update `ALLOWED_HOSTS`
2. Update `CSRF_TRUSTED_ORIGINS`
3. Update `SITE_URL`

## 6. Local development

Local default remains safe:

- `DEBUG=True` (unless overridden)
- SQLite database

For local env vars, copy `.env.example` values into your platform/environment.
