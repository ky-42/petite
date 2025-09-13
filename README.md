# Petite

A simple PostgreSQL migrations manager. Perfect for small to medium size projects that just need a small and simple tool.

## Installation

There are two main options when installing petite. You could install it as a system wide tool or you could install on a per project basis. If installing as a system wide tool I recommend using [pipx](https://pipx.pypa.io/stable/). If installing on a per project basis I recommend installing within a virtual environment.

__pipx__

```bash
  pipx install petite-cli
```

__pip__
```bash
  pip install petite-cli
```
    
## Usage

**Commands**:

* `setup`: Initializes the migration system by setting up the necessary directory and database table.
* `new`: Creates a new migration file in the migrations directory.
* `apply`: Runs outstanding migrations.

**Note**: If a .env file exists in the current directory when a command is run it will be loaded automatically when a command is ran.

## `setup`

Initializes the migration system by setting up the necessary directories and database table.

Should be run once per project before running any other commands.

**Options**:

* `--postgres-uri TEXT`: URI of the PostgreSQL database to connect to.  [env var: POSTGRES_URI; required]
* `--migrations-directory PATH`: Path to location where the migration files will be stored. If the destination directory does not exist it will be created assuming the parent directory exits.  [env var: MIGRATIONS_DIRECTORY; required]

**Example**

```bash
  petite setup --postgres-uri postgresql://... --migrations-directory /.../migrations
```

## `new`

Creates a new migration file in the migrations directory.

Should be ran after `setup`. When created the file name will follow the format: YYMMDDHHMMSS_migration_name.sql. This ensures that the migrations are applied in the correct order. For this reason this command should be used to create all migration files.

**Arguments**:

* `MIGRATION_NAME`: Name of the new migration file.  [required]

**Options**:

* `--migrations-directory PATH`: Path to location where the new migration file will be created.  [env var: MIGRATIONS_DIRECTORY; required]

**Example**

```bash
  petite new --migrations-directory /.../migrations new_migration 
```

## `apply`

Runs outstanding migrations.

Should be run after `setup` and once new migrations have been created with `new`. Will find new migrations then apply specified number to the database in order of oldest unapplied to newest. If an error occurs while applying a migration, none of the migrations will be applied.

**Arguments**:

* `COUNT`: Number of new migrations to apply.  [default: (All)]

**Options**:

* `--postgres-uri TEXT`: URI of the PostgreSQL database to connect to.  [env var: POSTGRES_URI; required]
* `--migrations-directory PATH`: Path to location where the migration files are stored.  [env var: MIGRATIONS_DIRECTORY; required]
* `--no-transaction`: Apply migrations without wrapping them in a transaction. <span style="color: #800000; text-decoration-color: #800000; font-weight: bold">Danger:</span> Running migrations without a transaction is risky. If a migration fails, the failing statement and all subsequent statements in the file will be skipped, and they will not be retried later. This can leave your database in an inconsistent state. Use this flag only if your migrations cannot run in a transaction.
* `--help`: Show this message and exit.

**Example**

```bash
  petite apply --postgres-uri postgresql://... --migrations-directory /.../migrations 2
```

## Contributing

Contributions are always welcome! Just make a pull request before you start working on anything so I can let you know if its something I want to add.

## Running Tests

To run unit tests, run the following command:

```bash
  poetry run pytest
```

To run integration tests first ensure you have docker installed as its used to bring up a PostgreSQL instance. You might also need to add your current user to the docker group see [here](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user) for more information. Once this is complete run the following command:

```bash
  poetry run pytest tests/integration
```

## Build Locally

This project uses [poetry](https://python-poetry.org/) so I would recommend you use it as well. It would make building the project much easier and all the examples below will be making use of it.

Clone the project

```bash
  git clone https://github.com/ky-42/petite
```

Go to the project directory

```bash
  cd petite
```

Install dependencies

```bash
  poetry install
```

Build the sdist and wheel files

```bash
  poetry build
```
