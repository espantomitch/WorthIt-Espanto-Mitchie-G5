# WorthIt: Regret Less

**Student:** Espanto, Mitchie T.
**Section:** G5
**Increment:** IM2 Project Development 2

WorthIt helps shoppers compare prices and specifications before making a purchase. It uses Django templates and PostgreSQL, including PostgreSQL hosted on Supabase.

## Product comparison and saved comparisons

1. Register or log in as a regular User. Open **My products** on the User dashboard.
2. Add products with a name, category, type, PHP price, and specifications. Enter one specification per line, such as `RAM: 16 GB`. Open a product to edit or delete it.
3. Choose **Compare products** and select 2–4 of your products of the same type. WorthIt lines up matching specifications and marks missing values with a dash.
4. Name and save the comparison. Open **Saved comparisons** to revisit, rename, or delete it. The saved version preserves the prices and specifications you compared, including after editing or deleting a source product.

Registration, login, logout, dashboard routing, and personal profile editing remain available. Public registration creates regular Users. Staff accounts see the Admin dashboard and account overview. Product and comparison pages are private to their regular User owner.

## Local setup in VS Code

Open the repository folder containing `manage.py` in VS Code. Use Python 3.12–3.14 and run these commands in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Skip the copy if `.env` already exists. Add the generated secret to `DJANGO_SECRET_KEY` in your private `.env`. Set `DJANGO_DEBUG=True` only for local HTTP development. Keep `DJANGO_DEBUG=False` when serving over HTTPS or verifying the custom 404 and 500 pages.

- **Supabase PostgreSQL** — copy the database name, username, host, port, and database password from **Connect → Session pooler**. Set `DB_SSLMODE=require`. The password is the PostgreSQL database password. Django handles application authentication.
- **Local PostgreSQL** — create a development database such as `worthit`. Set `DB_NAME=worthit`, `DB_HOST=localhost`, `DB_PORT=5432`, your local username and password, and `DB_SSLMODE=disable`.

Quote values containing spaces or `#`. Keep `.env` private.

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Run `createsuperuser` only if you need a new administrator. In VS Code, **Python: Select Interpreter** accepts `.venv\Scripts\python.exe`, and **Run and Debug → WorthIt Django** also starts the server.

## Local test accounts

Use a disposable local development database if you need the exact accounts shown in the completion report. Register `pd2_buyer` with `pd2_buyer@example.test` and `LocalPD2-Buyer-47!` on the registration page. Create the limited staff account from the local Django shell:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "from accounts.models import User; User.objects.create_user('pd2_staff', 'pd2_staff@example.test', 'LocalPD2-Staff-47!', is_staff=True)"
```

These demo credentials are public and intended for a disposable local copy. The staff account can use the Admin dashboard. A separately created superuser can manage accounts in Django administration.

## Verification

Run the integration suite with disposable PostgreSQL and a database role that can create a test database:

```powershell
.\.venv\Scripts\python.exe manage.py test accounts products
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

The suite covers Account Feature regressions, role gates, product CRUD and ownership, comparison validation, and the saved comparison lifecycle. Hosted PostgreSQL roles may restrict test-database creation.

For a manual check, add two laptops, preview them side by side, save the comparison, and reopen it from the dashboard. Reopen it again after editing or deleting one source product. Verify another User cannot open the saved comparison by URL and staff accounts receive HTTP 403 on the private feature pages.

## Project structure

| Path | Purpose |
| --- | --- |
| `accounts/` | Registration, login, profiles, role dashboards, and custom User model |
| `products/` | Product CRUD, comparison builder, saved comparisons, and PostgreSQL migrations |
| `templates/` | Server-rendered account, product, and comparison pages |
| `static/css/style.css` | Shared responsive styling |
| `docs/` | Project Development 2 completion report |

Work on `feature/*` branches from `develop`. Merge features into `develop` through pull requests, then open a release pull request from `develop` into `main`. Keep merged feature branches.
