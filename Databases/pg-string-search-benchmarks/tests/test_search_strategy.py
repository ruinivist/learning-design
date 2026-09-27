import unittest
from unittest.mock import Mock

from pg_string_search_benchmarks.search_strategy import SubstringMatch


class SubstringMatchTest(unittest.TestCase):
    def test_lowercases_and_wraps_query(self) -> None:
        db = Mock()
        db.execute.return_value.fetchall.return_value = []

        SubstringMatch().search(db, "FortNite")

        _, parameters = db.execute.call_args.args
        self.assertEqual(parameters, ("%fortnite%",))


if __name__ == "__main__":
    unittest.main()
