# Deployment guide

This app is written to run on any host that can run a Python WSGI
application: a self-managed VPS, a platform-as-a-service, or a container
platform. Nothing here assumes a particular provider. Where a setting
depends on your host, that's called out below.

## 1. Environment variables

Copy `.env.example` to `.env` on the server (never commit `.env`) and set:

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`. Must be at least 32 characters in production — the app refuses to start otherwise. Use a different key than your local `.env`. |
| `FLASK_ENV` | Yes | Set to `production`. This makes session cookies require HTTPS (see step 3) and enables the `SECRET_KEY` length check. |
| `TRUST_PROXY` | Only if behind a proxy | `0` if the app receives traffic directly (rare). `1` if there is exactly one reverse proxy or load balancer in front of it (the common case: nginx, or most PaaS platforms). If unsure, ask your host how many proxy hops sit in front of your app. Getting this wrong either breaks rate limiting (`0` when you need `1`) or lets a client spoof its IP by sending a fake `X-Forwarded-For` header (a number too high). |
| `PORT` | Depends on host | Some platforms set this automatically and expect the app to read it; others want a fixed port with the platform routing to it. Check your host's docs. |

## 2. Running the app

Do not use the Flask development server (`flask run`) in production — it is
single-threaded and not built for production traffic. Use Gunicorn instead:

```bash
pip install -r requirements.txt --break-system-packages
gunicorn wsgi:app --bind 0.0.0.0:${PORT:-8000} --workers 3 --access-logfile -
```

`wsgi.py` is the entry point Gunicorn loads; it calls the same
`create_app()` used everywhere else, so behaviour is identical to what
you tested locally.

Adjust `--workers` to roughly `(2 × CPU cores) + 1`. For a small single-core
VPS, 3 is a reasonable starting point.

If your host wants a `Procfile` (common on some PaaS platforms), it would
contain one line:

If instead your host wants you to point it at a WSGI callable directly
(common on container platforms), that callable is `wsgi:app`.

## 3. HTTPS

Once `FLASK_ENV=production` is set, the admin session cookie is marked
`Secure`, meaning the browser will only send it over HTTPS. If the site is
served over plain HTTP, admin sign-in will appear to silently fail (the
cookie gets set but the browser won't send it back). Make sure your host
or reverse proxy terminates HTTPS before switching this on:

- Many PaaS platforms provide HTTPS automatically for their default domain.
- On a self-managed VPS, a reverse proxy such as nginx with a free
  certificate (e.g. via Let's Encrypt / certbot) is the usual approach.

## 4. Database and files

- `instance/leads.db` and `instance/audit.log` are created automatically on
  first run and are **not** committed to Git (see `.gitignore`).
- These files must live on persistent storage. Some platforms use an
  ephemeral filesystem that resets on every deploy or restart — check
  whether your host offers a persistent disk or volume, and point
  `instance/` at it if so.
- Back them up regularly:
```bash
  python3 scripts/backup.py
```
  This writes a timestamped copy to `backups/` and keeps the 14 most
  recent by default (`--keep N` to change that). Schedule it with cron or
  your host's scheduled-task feature. Store copies somewhere other than
  the same server when you can.

## 5. Before going live: checklist

- [ ] `SECRET_KEY` in production is different from the one used locally,
     and is at least 32 characters.
- [ ] `FLASK_ENV=production` is set, and the site is reachable over HTTPS.
- [ ] `TRUST_PROXY` is set correctly for your host (see the table above).
- [ ] `flask --app wsgi create-admin` has been run **once** on the server
     to create your real admin account, with a fresh strong password —
     don't reuse a local test password.
- [ ] `instance/` and `.env` are excluded from Git (check `.gitignore`;
     confirm with `git status` that neither shows up as tracked).
- [ ] A backup has been taken and you've confirmed you can read it back.
- [ ] The contact form, admin sign-in and a status update have all been
     tested against the live URL, not just locally.
- [ ] `robots.txt` and `sitemap.xml` resolve at the live domain (they build
     their URLs from the incoming request, so this should work automatically,
     but check `Sitemap:` in the live `/robots.txt` points at the right host).
