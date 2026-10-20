# Repository Guidelines

## Project Structure & Module Organization

This repository collects design notes and small Python implementations, rather than one deployable application.

- `Projects/` contains standalone exercises such as Logger, Rate Limiter, LRU Cache, and Parking Lot. Supporting explanations and diagrams live beside their code.
- `leetcode-design/` contains Markdown solutions to data-structure design problems.
- `Systems/`, `Low/`, `Languages/`, and `Databases/` organize technical notes. System diagrams include PNG assets and SVGs under `Systems/uml/`.
- `Databases/pg-string-search-benchmarks/` is a separate Python package with a `src/` layout, `pyproject.toml`, and `uv.lock`.

## Build, Test, and Development Commands

There is no repository-wide build or test command. For the PostgreSQL benchmark, use Python 3.13+ and run these commands from `Databases/pg-string-search-benchmarks/`:

- `uv sync`: install the locked dependencies.
- `uv run pg-string-search-benchmarks`: run the default search queries.
- `uv run pg-string-search-benchmarks fortnite chatting`: benchmark specific queries.
- `uv build`: build the Python package.

Benchmark execution requires a populated PostgreSQL database and the tables, extensions, and search configuration used by the strategies. Consult `Databases/Smarter string search in PostgreSQL.md` and `search_strategy.py` before running.

## Coding Style & Naming Conventions

Use four-space indentation in Python, `snake_case` for functions and variables, and `PascalCase` for classes. Follow neighboring code and retain useful type annotations. Keep exercises self-contained and explanations close to their implementations. Use descriptive Markdown filenames and relative links for diagrams. No formatter or linter is currently configured.

## Writing notes

Use both the `prose` and `humanizer` skills whenever writing or revising notes in this repository. Apply `prose` while drafting, then use `humanizer` to edit the result. Preserve technical meaning, code examples, identifiers, commands, and links.

## Testing Guidelines

No automated test suite, testing framework, or coverage threshold is configured. For behavioral changes, add focused assertions or standard-library `unittest` tests alongside the affected exercise; name test files `test_*.py`. Run them with `python -m unittest discover -s "Projects/<exercise>"`. Check edge cases and document any database-dependent validation separately from latency measurements.

## Commit & Pull Request Guidelines

History uses conventional prefixes such as `feat:`, `fix:`, and `chore:`. Keep commit messages lowercase and at most eight words, for example `fix: correct cache eviction`. Keep each change focused. Pull requests should explain the affected exercise or note, the behavior changed, and validation performed. Link relevant issues and include rendered screenshots when changing diagrams.

## Configuration

Use the benchmark's `.env.example` as a template and export the PostgreSQL variables into your shell; the program does not load `.env` automatically. Keep credentials in ignored local files and never commit real passwords.
