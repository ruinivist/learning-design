from abc import ABC, abstractmethod
from typing import Any

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
        return db.execute(
            """
            SELECT id, title
            FROM streams
            WHERE lower(title) LIKE %s
            """,
            (f"%{query.lower()}%",),
        ).fetchall()


class TrigramWordMatch(SearchStrategy):
    """
    This'll use pg_trgm and and word_similarity function to rank based on scores
    Uses default threshold of 0.6
    > SHOW pg_trgm.word_similarity_threshold`

    What are trigrams? You pad with two spaces at start and one at end
    then define a trigram set as window of 3 len substrings
    > select show_trgm('cat')

    similarity = | A intersect B | / | A union B |
    where A and B are the trigram sets we are working with

    word_similarity is the same exceptf or continuous extents ( ig )
    """

    def search(self, db: psycopg.Connection, query: str) -> list[tuple[str, str]]:
        # % is doubled here for escaping
        return db.execute(
            """
            SELECT id, title
            FROM streams
            WHERE %s <%% lower(title)
            ORDER BY word_similarity(%s, lower(title)) DESC
            """,
            (f"{query.lower()}", f"{query.lower()}"),
        ).fetchall()
