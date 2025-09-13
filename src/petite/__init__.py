from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich import print

from .utils import Database, FileSystem
from .utils.confirmations import NO_TRANSACTION_MESSAGE, confirm_no_transaction

POSTGRES_URI_HELP = "URI of the PostgreSQL database to connect to."

load_dotenv("./.env")

# Just to make the output prettier
print()

app = typer.Typer(
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich",
    help="""
        A simple PostgreSQL migrations manager.\n
        Note: If a .env file exists in the current directory
        it will be loaded automatically when a command is ran.
    """,
)


@app.command()
def setup(
    postgres_uri: Annotated[
        str,
        typer.Option(envvar="POSTGRES_URI", help=POSTGRES_URI_HELP),
    ],
    migrations_directory: Annotated[
        Path,
        typer.Option(
            envvar="MIGRATIONS_DIRECTORY",
            help="""
                Path to location where the migration files will be stored.
                If the destination directory does not exist it will be created
                assuming the parent directory exits.
            """,
        ),
    ],
):
    """Initializes the migration system by setting up the necessary directory and database table.

    Should be run once per project before running any other commands.
    """

    db = Database(postgres_uri)
    FileSystem.create_migration_directory(migrations_directory)
    db.create_migration_table()


@app.command(name="new")
def new_migration(
    migrations_directory: Annotated[
        Path,
        typer.Option(
            envvar="MIGRATIONS_DIRECTORY",
            help="Path to location where the new migration file will be created.",
        ),
    ],
    migration_name: Annotated[
        str,
        typer.Argument(help="Name of the new migration file."),
    ],
):
    """Creates a new migration file in the migrations directory.

    Should be ran after `setup`. When created the file name will follow the
    format: YYMMDDHHMMSS_migration_name.sql. This ensures that the migrations
    are applied in the correct order. For this reason this command should be
    used to create all migration files.
    """

    FileSystem(migrations_directory).create_migration_file(migration_name)


@app.command(name="apply")
def apply_migrations(
    postgres_uri: Annotated[
        str, typer.Option(envvar="POSTGRES_URI", help=POSTGRES_URI_HELP)
    ],
    migrations_directory: Annotated[
        Path,
        typer.Option(
            envvar="MIGRATIONS_DIRECTORY",
            help="Path to location where the migration files are stored.",
        ),
    ],
    count: Annotated[
        int,
        typer.Argument(
            help="Number of new migrations to apply.",
            show_default="All",
        ),
    ] = -1,
    no_transaction: Annotated[
        bool,
        typer.Option(
            "--no-transaction",
            help="Apply migrations without wrapping them in a transaction.\n\n"
            + NO_TRANSACTION_MESSAGE,
            callback=confirm_no_transaction,
        ),
    ] = False,
):
    """Runs outstanding migrations.

    Should be run after `setup` and once new migrations have been created
    with `new`. Will find new migrations then apply specified number to the
    database in order of oldest unapplied to newest. If an error occurs while
    applying a migration, none of the migrations will be applied.
    """

    db = Database(postgres_uri)
    fs = FileSystem(migrations_directory)

    all_migration_files = fs.get_migration_files()
    most_recent_migration = db.get_last_applied_migration()

    if most_recent_migration is not None:
        try:
            most_recent_migration_index = all_migration_files.index(
                most_recent_migration[1]
            )
        except ValueError:
            print(
                f"[bold red]Error[/] migration [b]{most_recent_migration[1]}[/] not found in the migration directory.\n"
            )
            raise typer.Exit(code=1)
    else:
        most_recent_migration_index = -1

    starting_migration_index = most_recent_migration_index + 1

    print(
        f"Found {len(all_migration_files)} migration files with {len(all_migration_files[starting_migration_index:])} outstanding.\n"
    )

    # No new migrations
    if starting_migration_index == len(all_migration_files):
        return

    ending_migration_index = (
        # Ensures we don't go out of bounds
        min(starting_migration_index + count, len(all_migration_files))
        if count > -1
        # Run all migrations
        else len(all_migration_files)
    )

    files = all_migration_files[starting_migration_index:ending_migration_index]

    to_apply = [(file, fs.get_migration(file)) for file in files]

    db.apply_migrations(to_apply, no_transaction)
