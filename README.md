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

Now, you can run the project.

```bash
uv run main.py
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
