import random
import subprocess
from time import sleep

import psycopg
from psycopg import sql
from pytest import fixture

from petite.utils import Database


@fixture(scope="package", autouse=True)
def database():
    """Fixture to start and stop a PostgreSQL database in a Docker container.

    Yields a connection string to the database without a database name.

    Should only be used as a dependency for other fixtures.
    """

    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            "PetiteTestDb",
            "-e",
            "POSTGRES_PASSWORD=test",
            "-p",
            "5432:5432",
            "postgres:alpine",
        ]
    )

    conn_string = "postgresql://postgres:test@localhost:5432"

    # Ensure the database is up and running
    while True:
        try:
            psycopg.connect(conn_string)
            break
        except psycopg.OperationalError:
            sleep(1.5)

    yield conn_string

    subprocess.run(["docker", "stop", "PetiteTestDb"])
    subprocess.run(["docker", "rm", "PetiteTestDb"])


@fixture
def new_database(database):
    """Fixture to create a new database in the PostgreSQL container.

    Creates a new database with a random name and yields a connection string to it.

    Needed for isolation between tests.
    """

    conn = psycopg.connect(database + "/postgres", autocommit=True)

    database_name = "".join(random.sample("abcdefghijklmnopqrstuvwxyz", 10))

    with conn.cursor() as cur:
        try:
            cur.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
            )
        except psycopg.errors.UndefinedTable:
            pass

    conn.close()

    yield f"{database}/{database_name}"
