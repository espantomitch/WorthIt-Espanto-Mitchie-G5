# WorthIt: Regret Less

**Author:** Espanto, Mitchie T.  
**Section:** G5
**Phase:** IM2 Account Feature

A full-stack Django web application. Django renders all pages through templates; the database is PostgreSQL, either installed locally or hosted by Supabase. No React or SQLite is used.

## What works in this phase

- Registration with required first/last name, username, valid unique email, matching passwords, and Django password validation/hashing.
- Case-insensitive unique usernames and emails, enforced in forms and database constraints.
- Username/password login, helpful errors, POST logout, and protected pages.
- Separate User and Admin dashboards, automatic role routing, and HTTP 403 for the other role's URL.
- View/edit your own name, email, and optional contact number.
- Admin account counts and access to Django administration according to assigned permissions.

Product parsing, comparisons, scoring, bookmarks, and exports are later phases. Their controls are not presented as working features. Public registration always creates a regular User. There is no public role selector.

## 1. Open in VS Code on Windows

1. Extract the ZIP. Open the **worthit** folder that contains `manage.py` using **File → Open Folder**.
2. Install the **Python** extension by Microsoft when VS Code prompts you.
3. Select **Terminal → New Terminal**. Run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Use Python 3.12, 3.13, or 3.14. The tested dependency versions are in `requirements.txt`. The commands use the environment's Python directly, so PowerShell activation restrictions do not block setup.

Press **Ctrl+Shift+P → Python: Select Interpreter**, then select `.venv\Scripts\python.exe`.

## 2. Configure your private .env file

Generate a secret key:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Open `.env` in VS Code. Paste the generated value in quotes:

```dotenv
DJANGO_SECRET_KEY='paste-your-generated-value-here'
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

Do not paste database passwords into chat or commit `.env`. `.env.example` contains placeholders only and is safe to commit. Use quotes around passwords containing `#` or spaces.

### Option A: Supabase PostgreSQL

1. Create/open your own Supabase project.
2. Open **Connect → Session pooler** and view its connection parameters. Use session mode, not transaction mode, for this setup.
3. Copy the actual host, port, database, username, and database password into `.env`:

```dotenv
DB_NAME=postgres
DB_USER=postgres.YOUR_PROJECT_REFERENCE
DB_PASSWORD='your-database-password'
DB_HOST=YOUR_SESSION_POOLER_HOST
DB_PORT=5432
DB_SSLMODE=require
```

Copy the exact values shown by your project; the example username/port may differ from another connection option. The database password is not the anon/publishable key or service-role key. This project uses Django authentication and connects directly to PostgreSQL, so Supabase API keys and Supabase Auth are not needed. Never expose Django account tables through a public Data API; use a dedicated project and disable the Data API if it is not needed.

### Option B: local PostgreSQL

Install PostgreSQL and create a database named `worthit` using pgAdmin. In `.env`, set your actual PostgreSQL username/password and:

```dotenv
DB_NAME=worthit
DB_USER=postgres
DB_PASSWORD='your-local-postgres-password'
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=disable
```

`disable` is only for a local development database. There is no SQLite fallback.

## 3. Create tables and your administrator

Run these from the folder containing `manage.py`:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

The first migration is included. `createsuperuser` asks for a username, email, and password; the password does not appear as you type. Keep your chosen credentials private.

Visit **http://127.0.0.1:8000/**. Keep the terminal running. Use a second terminal for other commands or press **Ctrl+C** to stop the server. VS Code's **Run and Debug → WorthIt Django** also starts the server after configuration.

## 4. Roles and how to demonstrate them

| Role | How it is created | Dashboard |
|---|---|---|
| User | Public registration form | `/accounts/dashboard/user/` |
| Admin | `createsuperuser`, or staff status assigned by a trusted superuser | `/accounts/dashboard/admin/` |

Django's `is_staff` field is the single source of truth for the Admin role. `is_superuser` grants all Django administration permissions. A staff-only account can use the Admin dashboard but needs explicit permissions before it can manage accounts in `/admin/`. Only give account-edit permissions to trusted administrators.

1. Register a regular User. Try an invalid email, duplicate username/email, and mismatched password.
2. Log in as that User. Open `/accounts/dashboard/admin/` directly: it must return **403**.
3. View/edit your profile, save, refresh, and confirm the values persisted.
4. Log out. Open `/accounts/profile/`: it must redirect to login.
5. Log in using the superuser. Confirm the Admin dashboard, account totals, and `/admin/` work.
6. While logged in as Admin, open the User dashboard URL: it must return **403**.
7. Profiles have no public user-ID route. Attempts to supply another user's ID or submit staff fields do not change the account being edited or its role.

## 5. Automated checks

With a disposable local PostgreSQL database configured and a database role allowed to create test databases:

```powershell
.\.venv\Scripts\python.exe manage.py test accounts
```

Django creates and removes a separate test database. Hosted Supabase roles may not allow test database creation; use local PostgreSQL for the full suite. Do not point tests at production data or use `--keepdb` to reuse a live database.

Checks that do not require a database connection:

```powershell
.\.venv\Scripts\python.exe manage.py test accounts.tests.AccessWithoutDatabaseTests
```

See `VALIDATION.md` for checks actually executed when this package was prepared.

## 6. Public GitHub repository

Use the required name **WorthIt-Espanto-Mitchie-YOUR_SECTION**. Replace `YOUR_SECTION` with your actual class section in both the repository name and this README.

Create an empty **Public** repository on GitHub. Do not add a remote README or `.gitignore` when creating it if you are using these local files. Then run in VS Code:

```powershell
git init
git branch -M main
git status
git check-ignore .env .venv/
git add .
git diff --cached --name-only
git commit -m "espanto.mitchie: implement WorthIt account feature"
git remote add origin https://github.com/YOUR_USERNAME/WorthIt-Espanto-Mitchie-YOUR_SECTION.git
git push -u origin main
```

Before committing, confirm `.env`, `.venv`, `venv`, and `__pycache__` do not appear in the staged file list. Authenticate through GitHub's normal sign-in flow; do not put tokens in a remote URL.

**Commit history:** this package does not include fabricated development history. A single upload of completed code does not satisfy the instruction to show progress over time. Commit and push your genuine setup changes, completed work, tests, and corrections regularly as you work and learn. Do not backdate commits or claim supplied code as a history of your own development. Follow your instructor's policy on assisted code.

Example messages for real later work:

- `espanto.mitchie: configure PostgreSQL and verify migrations`
- `espanto.mitchie: improve account form messages`
- `espanto.mitchie: verify dashboard access and profile isolation`

The repository has not been created or pushed from this package.

## Project map

```text
worthit/
  manage.py
  config/                 Django settings and root URLs
  accounts/
    models.py             Custom Django User with unique email/contact number
    forms.py              Registration, login, profile validation
    views.py              Account flows and dashboards
    decorators.py         Role checks
    migrations/           PostgreSQL schema changes
    tests.py              Access and database integration tests
  templates/              Server-rendered HTML pages
  static/css/style.css    Responsive WorthIt styling
  .vscode/                Interpreter and debugger settings
  .env.example            Configuration placeholders
  .gitignore
  requirements.txt
```

## Common setup problems

- **Set ... in your .env file:** edit `.env` beside `manage.py`, not `.env.example`. Replace all placeholders.
- **Connection refused:** verify PostgreSQL is running or that the Supabase host/port is correct.
- **Password authentication failed:** use the PostgreSQL database password, not an API key.
- **Relation users does not exist:** run `manage.py migrate` against the same database you configured for the server.
- **Admin dashboard returns 403:** log in with the `createsuperuser` account. A public registration is deliberately a regular User.
- **Cannot type another terminal command:** the server is running. Open another terminal or stop it with Ctrl+C.

## Deployment boundary

This is the requested account-feature phase, configured for local development. Before public hosting, use a production server, configure static-file serving and HTTPS, set a strong secret, set `DJANGO_DEBUG=False`, and supply exact allowed hosts/trusted origins. Add login throttling before exposing authentication to unrestricted public traffic. Do not use Django's development server for production.

## References

- Django authentication: https://docs.djangoproject.com/en/5.2/topics/auth/default/
- Custom Django users: https://docs.djangoproject.com/en/5.2/topics/auth/customizing/
- Supabase PostgreSQL connection parameters: https://supabase.com/docs/guides/database/connecting-to-postgres
