from datetime import datetime
from typing import List, Optional, Tuple

import psycopg
import typer
from rich import print


class Database:
    """Class to handle database operations for migrations"""

    def __init__(self, uri: str):
        try:
            self.conn = psycopg.connect(uri)
            print("[bold green]Connected[/] to the database successfully!\n")
        except Exception as e:
            print(
                f"[bold red]Could not connect to the database![/]\nMake sure the database is running and URI is correct.\n\n[b]Error[/]: {e}."
            )
            raise typer.Exit(code=1)

    def create_migration_table(self) -> None:
        """Creates a migration table in the db if it doesn't exist"""

        table = """
        CREATE TABLE IF NOT EXISTS migration (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(255) UNIQUE NOT NULL,
            run_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """

        with self.conn.cursor() as cur:
            cur.execute(table)

        self.conn.commit()

        print("[bold green]Created or found[/] migration table in the database.\n")

    def get_last_applied_migration(self) -> Optional[Tuple[int, str, datetime]]:
        """Gets the last migration that was applied returning whole row"""

        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    "SELECT * FROM migration ORDER BY file_name DESC, run_on DESC, id DESC LIMIT 1"
                )
            except psycopg.errors.UndefinedTable:
                print(
                    f"[bold red]Migration table not found![/]\nRun the [b]setup[/] command to setup migrations table."
                )
                raise typer.Exit(code=1)

            value = cur.fetchone()

        if value is not None:
            print(f"[bold green]Found[/] last applied migration [b]{value[1]}[/].\n")

        return value

    def apply_migrations(self, migrations: List[Tuple[str, bytes]]):
        """Applies a single migration file to the database"""

        print(
            f"Attempting to apply {len(migrations)} migration{'s' if len(migrations) > 1 else ''}.\n"
        )

        with self.conn.cursor() as cur:
            for migration_name, migration_content in migrations:
                try:
                    cur.execute(
                        "INSERT INTO migration (file_name) VALUES (%s)",
                        (migration_name,),
                    )
                    cur.execute(migration_content)
                    print(f"[bold green]Applied[/] migration [b]{migration_name}[/].")

                except Exception as e:
                    print(
                        f"\n[bold red]Error[/] applying migration: [b]{migration_name}[/]!\nRolling back migrations applied so far.\n\n[b]Error[/]: {e}."
                    )
                    raise typer.Exit(code=1)

        self.conn.commit()

        print(
            f"\n[bold green]Successfully applied[/] {len(migrations)} migration{'s' if len(migrations) > 1 else ''}."
        )
