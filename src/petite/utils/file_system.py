import os
from datetime import datetime
from pathlib import Path
from typing import List

import typer
from rich import print


class FileSystem:
    """Class to handle file system operations for migrations"""

    def __init__(self, migrations_directory: Path):
        if not migrations_directory.exists():
            print(
                f"[bold red]Migration directory not found![/]\nRun the [b]setup[/] command to setup the migrations directory.\n"
            )
            raise typer.Exit(code=1)

        self.migrations_directory = migrations_directory

    def create_migration_file(self, migration_name: str) -> None:
        """Creates a new migration file in the migrations directory"""

        file_name = datetime.now().strftime("%y%m%d%H%M%S") + f"_{migration_name}.sql"

        with open(self.migrations_directory / file_name, "w") as f:
            f.write("-- Write migration code below\n")

        print(
            f"[bold green]Created[/] migration file at: [b]{self.migrations_directory}/{file_name}[/].\n"
        )

    def get_migration_files(self) -> List[str]:
        """Returns sorted list of all migration files in the migrations directory"""

        # Creates list of all files in the migrations directory ending with .sql
        all_migrations = [
            file_path.name
            for file_path in self.migrations_directory.glob("*.sql")
            if file_path.is_file()
        ]
        all_migrations.sort()

        return all_migrations

    def get_migration(self, migration_name: str) -> bytes:
        """Gets a migration file from the migration directory"""

        migration_file = self.migrations_directory / migration_name

        if not migration_file.exists():
            print(
                f"\n[bold red]Error[/] migration [b]{migration_name}[/] not found in the migration directory.\n"
            )
            raise typer.Exit(code=1)

        return migration_file.read_bytes()

    @staticmethod
    def create_migration_directory(migrations_directory: Path) -> None:
        """Creates the migration directory if it doesn't exist"""

        if not migrations_directory.exists():
            os.mkdir(migrations_directory)
            print(
                f"[bold green]Created[/] migrations directory at: [b]{migrations_directory}[/].\n"
            )
        else:
            print(
                f"[bold green]Found[/] migrations directory at: [b]{migrations_directory}[/].\n"
            )
