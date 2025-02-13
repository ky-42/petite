from pathlib import Path

from typer.testing import CliRunner

from petite import app

runner = CliRunner()


def test_new_migration_no_folder(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "new",
            "test",
            "--migrations-folder",
            str(tmp_path / "migrations"),
        ],
    )

    assert result.exit_code == 1
    assert "Migration folder not found!" in result.stdout


def test_new_migration(tmp_path: Path):
    mig_path = tmp_path / "migrations"
    mig_path.mkdir()

    result = runner.invoke(
        app,
        [
            "new",
            "test",
            "--migrations-folder",
            str(mig_path),
        ],
    )

    assert result.exit_code == 0
    assert "Created migration file" in result.stdout

    files = list(mig_path.glob("*_test.sql"))
    assert len(files) == 1
    assert "_test.sql" in files[0].name
