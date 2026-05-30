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

Next, set the DATABASE_URL in `.env` that points to your database.

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/database_name
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

## Migrations

To create a migration, run:

```bash
alembic revision -m "<REVISION_NAME>"
```

After adding the migration content, apply the changes from it:

```bash
alembic upgrade head
```
