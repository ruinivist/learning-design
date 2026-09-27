from abc import ABC, abstractmethod

import psycopg

type SearchResultT = list[tuple[int, str]]


class SearchStrategy(ABC):
    @abstractmethod
    def search(self, db: psycopg.Connection, query: str) -> SearchResultT:
        # stream ids so that same titles can be distinguished
        """Return matching stream IDs and titles."""


class SubstringMatch(SearchStrategy):
    """no order is defined, simply does a like %...% based search"""

    def search(self, db: psycopg.Connection, query: str) -> SearchResultT:
        if not query:
            return []
        return db.execute(
            """
            SELECT id, title FROM streams WHERE strpos(lower(title), lower(%s)) > 0
            LIMIT 10
            """,
            (query,),
        ).fetchall()
