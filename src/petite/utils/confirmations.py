"""Utility functions for confirming dangerous operations"""

import typer
from rich import print

NO_TRANSACTION_MESSAGE = (
    "[bold red]Danger:[/] Running migrations without a transaction is dangerous. "
    "If a migration fails when this is set, "
    "part of a migration may be applied but not recorded. "
    "This means part of the migration may rerun next time migrations are applied, "
    "leaving the database in an inconsistent state. "
    "It is recommended to only use this flag if the migrations being applied "
    "do not support being run in a transaction.\n"
)


def confirm_no_transaction(value: bool):
    if value:
        print(NO_TRANSACTION_MESSAGE)

        continue_prompt = typer.confirm("Are you sure you want to continue?")
        print()

        if not continue_prompt:
            print("[bold red]Aborting[/]\n")
            raise typer.Exit(code=0)

    return value
