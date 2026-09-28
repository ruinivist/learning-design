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
    Uses the connection's pg_trgm.word_similarity_threshold
    > SHOW pg_trgm.word_similarity_threshold`

    What are trigrams? You pad with two spaces at start and one at end
    then define a trigram set as window of 3 len substrings
    > select show_trgm('cat')

    similarity = | A intersect B | / | A union B |
    where A and B are the trigram sets we are working with

    word_similarity is the same exceptf or continuous extents ( ig )
    """

    def search(self, db: psycopg.Connection, query: str) -> list[tuple[str, str]]:
        query = query.lower()
        # % is doubled here for escaping
        return db.execute(
            """
            SELECT id, title
            FROM streams
            WHERE %s <%% lower(title)
            ORDER BY word_similarity(%s, lower(title)) DESC, id
            """,
            (query, query),
        ).fetchall()


class TrigramStrictWordMatch(SearchStrategy):
    """Rank trigram matches whose matched extent follows word boundaries."""

    def search(self, db: psycopg.Connection, query: str) -> SearchResultT:
        query = query.lower()
        return db.execute(
            """
            SELECT id, title
            FROM streams
            WHERE %s <<%% lower(title)
            ORDER BY strict_word_similarity(%s, lower(title)) DESC, id
            """,
            (query, query),
        ).fetchall()


class TrigramLevHybrid(SearchStrategy):
    """Rank trigram candidates by distance to their closest word."""

    def search(self, db: psycopg.Connection, query: str) -> SearchResultT:
        query = query.lower()
        # 1. that subquery regexp_split_to_table(lower(title), '[^[:alnum:]]+')
        # is to split title into words and then it takes a min over all comparisons
        # 2. that as words(word) is as {table name}({column name}), I could've written
        # simple "as word" too since just one col and words isn't referenced
        return db.execute(
            """
            SELECT id, title
            FROM streams
            WHERE %s <%% lower(title)
            ORDER BY (
                SELECT min(levenshtein(%s, word))
                FROM regexp_split_to_table(
                    lower(title), '[^[:alnum:]]+'
                ) AS words(word)
                WHERE word <> ''
            ), word_similarity(%s, lower(title)) DESC, id
            """,
            (query, query, query),
        ).fetchall()


class FullTextMatch(SearchStrategy):
    """Rank word matches using PostgreSQL full-text search."""

    def search(self, db: psycopg.Connection, query: str) -> SearchResultT:
        return db.execute(
            """
            SELECT id, title
            FROM streams
            WHERE to_tsvector('simple', title)
                  @@ plainto_tsquery('simple', %s)
            ORDER BY ts_rank(
                to_tsvector('simple', title),
                plainto_tsquery('simple', %s)
            ) DESC, id
            """,
            (query, query),
        ).fetchall()
