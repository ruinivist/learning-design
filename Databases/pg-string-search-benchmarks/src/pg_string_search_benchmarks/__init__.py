import psycopg
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .search_strategy import SubstringMatch


def main() -> None:
    console = Console()

    queries = ["discord", "fortnite"]
    strategies = [SubstringMatch()]
    with psycopg.connect() as db:
        for query in queries:
            for strat in strategies:
                results = strat.search(db, query)
                shown = results[:10]
                table = Table(
                    title=(
                        f"{query} · {type(strat).__name__} "
                        f"({len(results)} matches, showing {len(shown)} unordered)"
                    )
                )
                table.add_column("ID", justify="right")
                table.add_column("Title")
                for stream_id, title in shown:
                    table.add_row(str(stream_id), Text(title))
                console.print(table)
