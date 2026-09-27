from dataclasses import dataclass, field
from os import environ

import psycopg
from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Env:
    user: str
    password: str = field(repr=False)
    host: str
    port: str
    database: str

    @classmethod
    def from_env(cls) -> "Env":
        load_dotenv()
        return cls(
            user=environ["PGUSER"],
            password=environ["PGPASSWORD"],
            host=environ["PGHOST"],
            port=environ["PGPORT"],
            database=environ["PGDATABASE"],
        )


def connection(env: Env) -> psycopg.Connection:
    return psycopg.connect(
        user=env.user,
        password=env.password,
        host=env.host,
        port=env.port,
        dbname=env.database,
        sslmode="disable",
    )
