from pathlib import Path

import psycopg
from typer.testing import CliRunner

from petite import app

from . import database, new_database

runner = CliRunner()


def test_setup(new_database: str, tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "setup",
            "--migrations-folder",
            str(tmp_path / "migrations"),
            "--postgres-uri",
            new_database,
        ],
    )

    assert result.exit_code == 0
    assert "Connected to the database" in result.stdout
    assert "Created migrations folder" in result.stdout
    assert "Created or found migration table" in result.stdout

    # Will raise an exception if the table doesn't exist
    db_conn = psycopg.connect(new_database)
    with db_conn.cursor() as cur:
        cur.execute("SELECT * FROM migration")
        cur.fetchone()
    db_conn.close()

    assert (tmp_path / "migrations").exists()

    # Running the setup command again should not create a new folder
    # or table

    (tmp_path / "migrations" / "test.sql").write_text("")

    result = runner.invoke(
        app,
        [
            "setup",
            "--migrations-folder",
            str(tmp_path / "migrations"),
            "--postgres-uri",
            new_database,
        ],
    )

    assert result.exit_code == 0
    assert "Connected to the database" in result.stdout
    assert "Created or found migration table" in result.stdout
    assert "Found migrations folder" in result.stdout

    # Will raise an exception if the table doesn't exist
    db_conn = psycopg.connect(new_database)
    with db_conn.cursor() as cur:
        cur.execute("SELECT * FROM migration")
        cur.fetchone()
    db_conn.close()

    assert (tmp_path / "migrations" / "test.sql").exists()
