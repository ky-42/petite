# Petite

A dead simple PostgreSQL migrations manager. Perfect for small to medium size projects that just need a small and simple tool.

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

Petite has only 3 commands `setup`, `new`, and `apply`. You are intended to run `setup` first. Then `new` to create new migration files. Then `apply` to run those migration files against the database. Below is a quick outline of each command but more detailed information can be found in the help menu once installed:

## `setup`

This command is intended to be the first command ran when setting up a new project. This will create a migration table in your PostgreSQL database and create a directory to hold your migration files.

__Example__

```bash
  petite setup --postgres-uri postgresql://... --migrations-directory /.../migrations
```

## `new`

This command should be ran after `setup`. It creates a new file in the migrations directory where you can put your SQL code. It's ill advised that you create your own files as the file name is used as a means of ordering the migrations.

__Example__

```bash
  petite new migration_name --postgres-uri postgresql://... --migrations-directory /.../migrations
```

## `apply`

This command should be run after `setup` and once new migrations have been created with `new`. It will find new migrations then apply the specified number to the database in order of oldest unapplied to newest. If any fail all the migrations applied during the execution of the command will be rolled back.

__Example__

```bash
  petite apply 2 --postgres-uri postgresql://... --migrations-directory /.../migrations
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
