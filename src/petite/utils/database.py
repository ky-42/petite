from datetime import datetime
from typing import List, Optional, Tuple

import psycopg
import sqlglot
import typer
from rich import print


class Database:
    """Class to handle database operations for migrations"""

    def __init__(self, uri: str) -> None:
        try:
            self.conn = psycopg.connect(uri)
            print("[bold green]Connected[/] to the database successfully!\n")
        except Exception as e:
            print(
                f"[bold red]Could not connect to the database![/]\nMake sure the database is running and URI is correct.\n\n[b]Error[/]: {e}\n"
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

        print("[bold green]Created[/] migration table in the database.\n")

    def get_last_applied_migration(self) -> Optional[Tuple[int, str, datetime]]:
        """Gets the last migration that was applied returning whole row"""

        with self.conn.cursor() as cur:
            try:
                cur.execute(
                    "SELECT * FROM migration ORDER BY file_name DESC, run_on DESC, id DESC LIMIT 1"
                )
            except psycopg.errors.UndefinedTable:
                print(
                    f"[bold red]Migration table not found![/]\nRun the [b]setup[/] command to setup migrations table.\n"
                )
                raise typer.Exit(code=1)

            value = cur.fetchone()

        if value is not None:
            print(f"Found last applied migration [b]{value[1]}[/].\n")

        return value

    def apply_migrations(
        self, migrations: List[Tuple[str, bytes]], no_transaction: bool = False
    ) -> None:
        """Applies a single migration file to the database"""

        print(
            f"Attempting to apply {len(migrations)} migration{'s' if len(migrations) > 1 else ''}.\n"
        )

        no_transaction_fail_index = -1
        if no_transaction:
            # Need to commit any open transaction before setting autocommit
            self.conn.commit()
            self.conn.autocommit = no_transaction

        with self.conn.cursor() as cur:
            for migration_name, migration_content in migrations:
                try:
                    cur.execute(
                        "INSERT INTO migration (file_name) VALUES (%s)",
                        (migration_name,),
                    )

                    if not no_transaction:
                        cur.execute(migration_content)
                    else:
                        # Run each statement in the migration file separately so no
                        # transaction is opened by psycopg because if multiple
                        # statements are run in one execute call psycopg will open a
                        # transaction even if autocommit is True
                        for index, statement in enumerate(
                            self.__split_migration(migration_content)
                        ):
                            # Track the current statement so we know what was not
                            # applied for error message later
                            no_transaction_fail_index = index
                            cur.execute(statement)

                    print(f"[bold green]Applied[/] migration [b]{migration_name}[/].")

                except Exception as e:
                    print(
                        f"[bold red]Error[/] applying migration: [b]{migration_name}[/]!\n\n"
                        + f"[bold red]Error[/]: {e}\n"
                        + (
                            "Rolling back migrations applied so far."
                            if not no_transaction
                            else (
                                "[bold red]Danger:[/] Statements before the error in the "
                                f"migration file [b]{migration_name}[/] have already been applied. "
                                "The statements not applied include:\n\n"
                                + "\n".join(
                                    [
                                        stmt.decode("utf-8") + ";"
                                        for stmt in self.__split_migration(
                                            migration_content
                                        )[no_transaction_fail_index:]
                                    ]
                                )
                                + "\n\nIt is recommended you personally check which statements succeeded "
                                "and remove any that did not from the migration file. "
                                "Unapplied statements should be moved to a new migration file."
                            )
                        )
                    )
                    raise typer.Exit(code=1)

        self.conn.commit()

        print(
            f"\n[bold green]Successfully applied[/] {len(migrations)} migration{'s' if len(migrations) > 1 else ''}.\n"
        )

    def __split_migration(self, migration_content: bytes) -> List[bytes]:
        """Splits a migrations content into individual SQL statements"""

        parsed_migration = sqlglot.parse(
            migration_content.decode("utf-8"), read="postgres"
        )

        return [
            statement.sql(dialect="postgres").encode("utf-8")
            for statement in parsed_migration
            if statement
        ]
