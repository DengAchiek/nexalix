#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  echo "Missing .env file in $(pwd). Create it first based on .env.example"
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

set -a
source .env
set +a

python manage.py migrate
python manage.py collectstatic --noinput

echo "Done. Now configure PythonAnywhere Web tab (WSGI + static/media) and click Reload."
