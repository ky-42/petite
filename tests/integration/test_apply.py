import random
from pathlib import Path

import psycopg
import pytest
from typer.testing import CliRunner

from petite import app

from . import Database, database, new_database

runner = CliRunner()


def test_apply_migrations_success(new_database: str, tmp_path: Path):
    mig_path = tmp_path / "migrations"
    mig_path.mkdir()

    (mig_path / "1_test.sql").write_text("CREATE TABLE test();")
    (mig_path / "2_test.sql").write_text(
        "ALTER TABLE test ADD COLUMN test_column_one INT;"
    )
    (mig_path / "3_test.sql").write_text(
        "ALTER TABLE test ADD COLUMN test_column_two INT;\nALTER TABLE test ADD COLUMN test_column_three INT;"
    )

    # Tested elsewhere
    db = Database(new_database)
    db.create_migration_table()

    result = runner.invoke(
        app,
        [
            "apply",
            "1",
            "--migrations-directory",
            str(mig_path),
            "--postgres-uri",
            new_database,
        ],
    )

    assert result.exit_code == 0
    assert f"Found 3 migration files with 3 outstanding" in result.stdout
    assert "Attempting to apply 1 migration" in result.stdout
    assert "Applied migration 1_test.sql" in result.stdout
    assert "Successfully applied 1 migration" in result.stdout

    db_conn = psycopg.connect(new_database)
    with db_conn.cursor() as cur:
        cur.execute("SELECT * FROM test")
        cur.fetchone()

        cur.execute("SELECT * FROM migration")
        migration = cur.fetchall()

        assert len(migration) == 1
        assert migration[0][1] == "1_test.sql"  # type: ignore
    db_conn.close()

    # Apply the rest of the migrations to ensure it picks up from the last

    result = runner.invoke(
        app,
        [
            "apply",
            "--migrations-directory",
            str(mig_path),
            "--postgres-uri",
            new_database,
        ],
    )

    assert result.exit_code == 0
    assert "Found 3 migration files with 2 outstanding" in result.stdout
    assert "Attempting to apply 2 migration" in result.stdout
    assert "Applied migration 2_test.sql" in result.stdout
    assert "Applied migration 3_test.sql" in result.stdout
    assert "Successfully applied 2 migrations" in result.stdout

    db_conn = psycopg.connect(new_database)
    with db_conn.cursor() as cur:
        # Error would be thrown if column doesn't exist
        # Meaning the migrations were not applied
        cur.execute(
            "INSERT INTO test (test_column_one, test_column_two, test_column_three) VALUES (1, 2, 3);"
        )
        db_conn.commit()

        cur.execute("SELECT * FROM migration")
        migration = cur.fetchall()

        assert [x[1] for x in migration] == ["1_test.sql", "2_test.sql", "3_test.sql"]  # type: ignore
    db_conn.close()


def test_apply_migrations_fail(new_database: str, tmp_path: Path):
    mig_path = tmp_path / "migrations"
    mig_path.mkdir()

    (mig_path / "1_test.sql").write_text("CREATE TABLE test();")
    # Bad sql will throw an error if run
    (mig_path / "2_test.sql").write_text(
        "42 TABLE test ADD COLUMN test_column_one INT;"
    )

    # Tested elsewhere
    db = Database(new_database)
    db.create_migration_table()

    result = runner.invoke(
        app,
        [
            "apply",
            "2",
            "--migrations-directory",
            str(mig_path),
            "--postgres-uri",
            new_database,
        ],
    )

    assert result.exit_code == 1
    assert "Found 2 migration files with 2 outstanding" in result.stdout
    assert "Attempting to apply 2 migrations" in result.stdout
    assert "Applied migration 1_test.sql" in result.stdout
    assert "Error applying migration: 2_test.sql" in result.stdout
    assert "Rolling back migrations applied so far" in result.stdout

    # Ensure the migration table is empty meaning the first
    # migration was rolled back
    db_conn = psycopg.connect(new_database)
    with db_conn.cursor() as cur:
        with pytest.raises(psycopg.errors.UndefinedTable):
            cur.execute("SELECT * FROM test")
    db_conn.close()


def test_apply_no_transaction_success(new_database: str, tmp_path: Path):
    mig_path = tmp_path / "migrations"
    mig_path.mkdir()

    random_name = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))

    (mig_path / "1_test.sql").write_text(
        f"CREATE USER {random_name} WITH PASSWORD '';\nCREATE DATABASE {random_name} OWNER {random_name};\nGRANT ALL PRIVILEGES ON DATABASE {random_name} TO {random_name};"
    )

    db = Database(new_database)
    db.create_migration_table()

    result = runner.invoke(
        app,
        [
            "apply",
            "--migrations-directory",
            str(mig_path),
            "--postgres-uri",
            new_database,
            "--no-transaction",
        ],
        input="y",
    )

    assert result.exit_code == 0
    assert "Found 1 migration files with 1 outstanding" in result.stdout
    assert "Attempting to apply 1 migration" in result.stdout
    assert "Applied migration 1_test.sql" in result.stdout

    conn = psycopg.connect(new_database)

    # Check if user and database were created
    with conn.cursor() as cur:
        # Check user existence
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s;", (random_name,))
        assert cur.fetchone() is not None

        # Check database existence
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (random_name,))
        assert cur.fetchone() is not None
    conn.close()


def test_apply_no_transaction_fail(new_database: str, tmp_path: Path):
    mig_path = tmp_path / "migrations"
    mig_path.mkdir()

    random_db_name = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))

    (mig_path / "1_test.sql").write_text(
        f"CREATE USER {random_db_name} WITH PASSWORD '';\nCREATE DATABASE {random_db_name} OWNER {random_db_name};\nGRANT ALL PRIVILEGES ON DATABASE {random_db_name} TO {random_db_name};"
    )
    (mig_path / "2_test.sql").write_text(
        f"CREATE USER {random_db_name+'1'} WITH PASSWORD '';\nCREATE ERROR DATABASE {random_db_name+'1'} OWNER {random_db_name+'1'};\nGRANT ALL PRIVILEGES ON DATABASE {random_db_name+'1'} TO {random_db_name+'1'};"
    )

    db = Database(new_database)
    db.create_migration_table()

    result = runner.invoke(
        app,
        [
            "apply",
            "--migrations-directory",
            str(mig_path),
            "--postgres-uri",
            new_database,
            "--no-transaction",
        ],
        input="y",
    )

    assert result.exit_code == 1
    assert "Found 2 migration files with 2 outstanding" in result.stdout
    assert "Attempting to apply 2 migrations" in result.stdout
    assert "Applied migration 1_test.sql" in result.stdout
    assert "Error applying migration: 2_test.sql" in result.stdout
    assert (
        f"CREATE ERROR DATABASE {random_db_name+'1'} OWNER {random_db_name+'1'}"
        in result.stdout
    )

    conn = psycopg.connect(new_database)

    # Check if user and database were created
    with conn.cursor() as cur:
        # Check user existence
        cur.execute(
            "SELECT 1 FROM pg_roles WHERE rolname IN (%s,%s);",
            (random_db_name, random_db_name + "1"),
        )
        assert len(cur.fetchall()) == 2

        # Check database existence
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname IN (%s,%s);",
            (random_db_name, random_db_name + "1"),
        )
        assert len(cur.fetchall()) == 1
    conn.close()
