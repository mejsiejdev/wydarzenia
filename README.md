# Wydarzenia

## Setting up the project locally

First, install [python](https://www.python.org/downloads/)
and [uv](https://docs.astral.sh/uv/getting-started/installation/)

Check if the `uv` is available:

```bash
$ uv
An extremely fast Python package manager.

Usage: uv [OPTIONS] <COMMAND>

...
```

After ensuring it's available, install required packages.

```bash
uv sync
```

Next, set the DATABASE_URL in `.env` that points to your database,
and a JWT_SECRET_KEY used to sign access tokens (any long random string,
e.g. generated with `openssl rand -hex 32`).

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/database_name
JWT_SECRET_KEY=<long random string>
```

Before running, apply the database migrations (see [Migrations](#migrations)):

```bash
uv run alembic upgrade head
```

Now you can run the project with uvicorn. For local development, use
`--reload` for live reloading:

```bash
uv run uvicorn main:app --reload
```

The API is served at `http://127.0.0.1:8000`, with interactive docs at
`http://127.0.0.1:8000/docs`.

For a production-like server, drop `--reload`:

```bash
uv run uvicorn main:app
```

If you want to add a package, run:

```bash
uv add <PACKAGE>
```

For example:

```bash
uv add ruff
```

## Authentication

Log in via `POST /auth/login` (OAuth2 password form, `username` carries the
email) to get a JWT bearer token, then send it as `Authorization: Bearer <token>`.
In the interactive docs, use the **Authorize** button.

New accounts start with the `nieaktywowany` status: they can log in and browse,
but cannot create events. Only a moderator can change a user's `status` or
`blacklisted` flag (via `PATCH /users/{id}`) — so the first moderator has to be
bootstrapped by hand:

### Setting up the first moderator

1. Register a user through the API — either in the interactive docs
   (`POST /users` at `http://127.0.0.1:8000/docs`) or with curl:

   ```bash
   curl -X POST http://127.0.0.1:8000/users \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@example.com", "password": "password123", "first_name": "Admin", "last_name": "User"}'
   ```

2. Promote that account directly in the database, using the same connection
   string as `DATABASE_URL` in your `.env`:

   ```bash
   psql "postgresql://user:password@localhost:5432/database_name" \
     -c "UPDATE users SET status = 'moderator' WHERE email = 'admin@example.com';"
   ```

3. Log in as that user — in the interactive docs click **Authorize** and enter
   the email as `username` plus your password. If the user was already logged
   in before the promotion, no re-login is needed: the status is read fresh
   from the database on every request.

The moderator can now list all users (`GET /users`) and manage other accounts
via `PATCH /users/{id}` — e.g. activate one with `{"status": "zwykły"}` or
block one with `{"blacklisted": true}`.

## Migrations

To create a migration, run:

```bash
alembic revision -m "<REVISION_NAME>"
```

After adding the migration content, apply the changes from it:

```bash
alembic upgrade head
```
