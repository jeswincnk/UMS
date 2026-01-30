# University Management System (UMS) — Django scaffold

This repository contains a starter scaffold for the University Management System (UMS) described in the abstract. It provides the Django project, apps, and core models to get started.

Windows (PowerShell) quick start

1. Create a virtual environment and activate it

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

2. Configure environment variables

Copy `.env.example` to `.env` and set values (DATABASE_URL or DB_* values).

3. Run migrations (by default the settings fall back to SQLite for quick starts)

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Notes
- The default `AUTH_USER_MODEL` is `accounts.User`.
- For production, configure MySQL in environment variables; see `ums_project/settings.py`.
