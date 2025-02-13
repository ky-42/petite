import pytest
import typer
from pytest_mock import MockerFixture

from . import Database


def test_apply_migrations(mocker: MockerFixture):
    mock_conn = mocker.patch("petite.utils.database.psycopg.connect").return_value
    mock_cursor = mocker.MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    db = Database("fake_uri")

    db.apply_migrations([("1.sql", b"A"), ("2.sql", b"B")])

    mock_cursor.execute.assert_has_calls(
        [
            mocker.call(mocker.ANY, ("1.sql",)),
            mocker.call(b"A"),
            mocker.call(mocker.ANY, ("2.sql",)),
            mocker.call(b"B"),
        ]
    )


def test_apply_migrations_fail(mocker: MockerFixture):
    mock_conn = mocker.patch("petite.utils.database.psycopg.connect").return_value
    mock_cursor = mocker.MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Mock the execute method of the cursor
    mock_cursor.execute = [mocker.MagicMock(), Exception]

    db = Database("fake_uri")

    with pytest.raises(typer.Exit):
        db.apply_migrations([("1.sql", b"A"), ("2.sql", b"B")])
