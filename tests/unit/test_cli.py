import pytest
from typer.testing import CliRunner

from petite import app

runner = CliRunner()


@pytest.fixture
def mock_db(mocker):
    return mocker.patch("petite.Database").return_value


@pytest.fixture
def mock_fs(mocker):
    return mocker.patch("petite.FileSystem").return_value


def test_apply_migrations_neg_num():
    result = runner.invoke(
        app,
        [
            "apply",
            "'-2'",
            "--migrations-folder",
            "migrations",
            "--postgres-uri",
            "postgres://user:password@localhost:5431/db",
        ],
    )

    assert result.exit_code != 0


@pytest.mark.parametrize("apply_num", [None, 1, 2, 3])
def test_apply_migrations_no_existing(mock_db, mock_fs, apply_num):
    mock_db.get_last_applied_migration.return_value = None
    mock_fs.get_migration_files.return_value = [
        "migration1.sql",
        "migration2.sql",
    ]
    mock_fs.get_migration.return_value = "SQL COMMAND"

    result = runner.invoke(
        app,
        (
            [
                "apply",
                str(apply_num),
                "--migrations-folder",
                "migrations",
                "--postgres-uri",
                "postgres://user:password@localhost:5432/db",
            ]
            if apply_num
            else [
                "apply",
                "--migrations-folder",
                "migrations",
                "--postgres-uri",
                "postgres://user:password@localhost:5432/db",
            ]
        ),
    )

    assert result.exit_code == 0

    mock_db.apply_migrations.assert_called_once_with(
        [("migration1.sql", "SQL COMMAND"), ("migration2.sql", "SQL COMMAND")][
            :apply_num
        ]
    )


@pytest.mark.parametrize("apply_num", [None, 1, 2, 3])
def test_apply_migrations_existing(mock_db, mock_fs, apply_num):
    mock_db.get_last_applied_migration.return_value = [0, "migration1.sql"]
    mock_fs.get_migration_files.return_value = [
        "migration1.sql",
        "migration2.sql",
        "migration3.sql",
    ]
    mock_fs.get_migration.return_value = "SQL COMMAND"

    result = runner.invoke(
        app,
        (
            # Need to add apply_num to the command if it's not None
            [
                "apply",
                str(apply_num),
                "--migrations-folder",
                "migrations",
                "--postgres-uri",
                "postgres://user:password@localhost:5432/db",
            ]
            if apply_num
            else [
                "apply",
                "--migrations-folder",
                "migrations",
                "--postgres-uri",
                "postgres://user:password@localhost:5432/db",
            ]
        ),
    )

    assert result.exit_code == 0

    mock_db.apply_migrations.assert_called_once_with(
        [
            ("migration2.sql", "SQL COMMAND"),
            ("migration3.sql", "SQL COMMAND"),
        ][:apply_num]
    )
