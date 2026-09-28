import sys

import psycopg
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .search_strategy import *

eval_queries = [
    "discord",
    "fortnite",
    "dota",
    "dawnwalker",
    "zombies",
    "wow",
    "rp",
    "r6",
    "enderal",
    "hotzone",
    "serotonin",
    "chatting",
    "zzqvxx",
    "fortite",
    "fortnnite",
    "fortnire",
    "fortntie",
    "chetting",
]


def print_search_table(
    console: Console, query: str, strategy: SearchStrategy, results: SearchResultT
) -> None:
    shown = results[:4]
    table = Table(
        title=(
            f"{query} · {type(strategy).__name__} "
            f"({len(results)} matches, showing {len(shown)})"
        )
    )
    table.add_column("ID", justify="right")
    table.add_column("Title")
    for stream_id, title in shown:
        table.add_row(str(stream_id), Text(title))
    console.print(table)


def main() -> None:
    console = Console()

    strategies = [SubstringMatch(), TrigramWordMatch(), TrigramStrictWordMatch()]

    # connect can build connection from envs, this is how it autobuilds
    # the db url
    with psycopg.connect() as db:
        # defaul is 0.6 which is pretty high for a trigram match
        # word_similarity(fortntie, fortnite) is ~0.55
        # SELECT word_similarity('fortntie', 'fortnite');
        db.execute("SET pg_trgm.word_similarity_threshold = 0.5")
        db.execute("SET pg_trgm.strict_word_similarity_threshold = 0.5")

        for query in (sys.argv[1:] or eval_queries):
            for strat in strategies:
                print_search_table(console, query, strat, strat.search(db, query))
