"""Utility functions for confirming dangerous operations"""

import typer
from rich import print

NO_TRANSACTION_MESSAGE = (
    "[bold red]Danger:[/] Running migrations without a transaction is risky. "
    "If a migration fails, the failing statement and all subsequent statements "
    "in the file will be skipped, and they will not be retried later. "
    "This can leave your database in an inconsistent state. "
    "Use this flag only if your migrations cannot run in a transaction.\n"
)


def confirm_no_transaction(value: bool):
    """Callback to confirm no-transaction option on apply command"""
    if value:
        print(NO_TRANSACTION_MESSAGE)

        continue_prompt = typer.confirm("Are you sure you want to continue?")
        print()

        if not continue_prompt:
            print("[bold red]Aborting[/]\n")
            raise typer.Exit(code=0)

    return value
