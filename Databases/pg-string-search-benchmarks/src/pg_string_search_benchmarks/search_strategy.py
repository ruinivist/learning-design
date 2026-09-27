from abc import ABC, abstractmethod

import psycopg

type SearchResultT = list[tuple[str, str]]


class SearchStrategy(ABC):
    @abstractmethod
    def search(self, db: psycopg.Connection, query: str) -> SearchResultT:
        # stream ids so that same titles can be distinguished
        """Return matching stream IDs and titles."""


class SubstringMatch(SearchStrategy):
    """Return unordered, case-insensitive substring matches."""

    def search(self, db: psycopg.Connection, query: str) -> SearchResultT:
        if not query:
            return []
        return db.execute(
            """
            SELECT id, title
            FROM streams
            WHERE lower(title) LIKE %s
            """,
            (f"%{query.lower()}%",),
        ).fetchall()
