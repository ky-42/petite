from pathlib import Path
from re import M
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich import print

from .utils import Database, FileSystem

load_dotenv()

app = typer.Typer(pretty_exceptions_show_locals=False)

POSTGRES_URI_HELP = "URI of the PostgreSQL database to connect to."


@app.command()
def setup(
    postgres_uri: Annotated[
        str,
        typer.Option(envvar="POSTGRES_URI", help=POSTGRES_URI_HELP),
    ],
    migrations_folder: Annotated[
        Path,
        typer.Option(
            envvar="MIGRATIONS_DIR",
            help="Path where the migration files will be stored. If the folder does not exist it will be created.",
        ),
    ],
):
    """Initializes the migration system by setting up the necessary folders and database table.

    Should be run once before running any other commands.
    """

    db = Database(postgres_uri)
    FileSystem.create_migration_folder(migrations_folder)
    db.create_migration_table()


@app.command(name="new")
def new_migration(
    migration_name: Annotated[
        str,
        typer.Argument(help="Name of the new migration file."),
    ],
    migrations_folder: Annotated[
        Path,
        typer.Option(
            envvar="MIGRATIONS_DIR",
            help="Folder where the new migration file will be created.",
        ),
    ],
):
    """Creates a new migration file in the migrations folder.

    When created the file name will follow the format: YYMMDDHHMMSS_<migration_name>.sql.
    This ensures that the migrations are applied in the correct order.
    For this reason this command should be used to create all migration files.
    """

    FileSystem(migrations_folder).create_migration_file(migration_name)


@app.command(name="apply")
def apply_migrations(
    migrations_folder: Annotated[
        Path,
        typer.Option(
            envvar="MIGRATIONS_DIR", help="Folder where the migration files are stored."
        ),
    ],
    postgres_uri: Annotated[
        str, typer.Option(envvar="POSTGRES_URI", help=POSTGRES_URI_HELP)
    ],
    count: Annotated[
        int,
        typer.Argument(
            help="Number of new migrations to apply. If not provided all outstanding migrations will be applied."
        ),
    ] = -1,
):
    """Runs outstanding migrations.

    If an error occurs while applying a migration, none of the migrations will be applied.
    """

    db = Database(postgres_uri)
    fs = FileSystem(migrations_folder)

    all_migration_files = fs.get_migration_files()
    most_recent_migration = db.get_last_applied_migration()

    if most_recent_migration is not None:
        try:
            most_recent_migration_index = all_migration_files.index(
                most_recent_migration[1]
            )
        except ValueError:
            print(
                f"\n[bold red]Error[/] migration [b]{most_recent_migration[1]}[/] not found in the migration folder."
            )
            raise typer.Exit(code=1)
    else:
        most_recent_migration_index = -1

    print(
        f"Found {len(all_migration_files)} migration files with {len(all_migration_files[most_recent_migration_index+1:])} outstanding.\n"
    )

    apply_till_index = (
        # Ensures we don't go out of bounds
        min(most_recent_migration_index + count + 1, len(all_migration_files))
        if count > -1
        # Run all migrations
        else len(all_migration_files)
    )

    files = all_migration_files[most_recent_migration_index + 1 : apply_till_index]

    to_apply = [(file, fs.get_migration(file)) for file in files]

    db.apply_migrations(to_apply)
