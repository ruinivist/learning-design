import sys
from statistics import mean, median
from time import perf_counter

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


def run_benchmarks(
    db: psycopg.Connection,
    console: Console,
    strategies: list[SearchStrategy],
    queries: list[str],
) -> None:
    timings = {strat: [] for strat in strategies}
    for query in queries:
        for strat in strategies:
            print_search_table(console, query, strat, strat.search(db, query))
            samples = []
            for _ in range(10):
                start = perf_counter()
                strat.search(db, query)
                samples.append((perf_counter() - start) * 1000)
            timings[strat].append((query, median(samples)))

    summary = Table(title="Warm search latency (10 runs/query; mean of medians)")
    summary.add_column("Strategy")
    summary.add_column("Avg (ms)", justify="right")
    summary.add_column("Slowest query")
    summary.add_column("Slowest (ms)", justify="right")
    for strat, query_timings in timings.items():
        slowest_query, slowest_ms = max(query_timings, key=lambda item: item[1])
        summary.add_row(
            type(strat).__name__,
            f"{mean(ms for _, ms in query_timings):.2f}",
            slowest_query,
            f"{slowest_ms:.2f}",
        )
    console.print(summary)


def main() -> None:
    console = Console()

    strategies = [
        TrigramLevHybrid(),
        VocabCorrectedFTS(),
    ]

    # connect can build connection from envs, this is how it autobuilds
    # the db url
    with psycopg.connect() as db:
        # defaul is 0.6 which is pretty high for a trigram match
        # word_similarity(fortntie, fortnite) is ~0.55
        # SELECT word_similarity('fortntie', 'fortnite');
        db.execute("SET pg_trgm.word_similarity_threshold = 0.5")
        db.execute("SET pg_trgm.strict_word_similarity_threshold = 0.5")

        run_benchmarks(db, console, strategies, sys.argv[1:] or eval_queries)
