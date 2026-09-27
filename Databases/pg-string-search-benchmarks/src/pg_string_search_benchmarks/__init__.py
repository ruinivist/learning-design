from rich.console import Console
from rich.table import Table
from rich.text import Text

from .config import Env, connection
from .search_strategy import SubstringMatch


def main() -> None:
    env = Env.from_env()
    console = Console()

    queries = ["discord", "fortnite"]
    strategies = [SubstringMatch()]
    with connection(env) as db:
        for query in queries:
            for strat in strategies:
                results = strat.search(db, query)
                table = Table(title=f"{query} · {type(strat).__name__} ({len(results)} matches)")
                table.add_column("ID", justify="right")
                table.add_column("Title")
                for stream_id, title in results:
                    table.add_row(str(stream_id), Text(title))
                console.print(table)
