import psycopg
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .search_strategy import *


def print_search_table(
    console: Console, query: str, strategy: SearchStrategy, results: SearchResultT
) -> None:
    shown = results[:10]
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

    queries = ["fortnite"]
    strategies = [SubstringMatch(), TrigramWordMatch()]

    # connect can build connection from envs, this is how it autobuilds
    # the db url
    with psycopg.connect() as db:
        for query in queries:
            for strat in strategies:
                print_search_table(console, query, strat, strat.search(db, query))
