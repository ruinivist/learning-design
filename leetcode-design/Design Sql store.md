# Design sql store

Rem

- to use dataclasses and to key rows by a row id in a dict

```python
from dataclasses import dataclass, field


@dataclass
class Table:
    cols: int
    id: int = 1
    rows: dict[int, list[str]] = field(default_factory=dict)


class SQL:
    # this is an in memory sql like store
    # tables -> Table, within that rows are keyed by rowId ( the pk here )
    # cols too don't have a name

    def __init__(self, names: list[str], columns: list[int]):
        self.data: dict[str, Table] = {}

        for name, cols in zip(names, columns):
            self.data[name] = Table(cols)

    def ins(self, name: str, row: list[str]) -> bool:
        if name not in self.data:
            return False

        tbl = self.data[name]

        if tbl.cols != len(row):
            return False

        tbl.rows[tbl.id] = row
        tbl.id += 1

        return True

    def rmv(self, name: str, rowId: int) -> None:
        if name not in self.data:
            return

        tbl = self.data[name]
        tbl.rows.pop(rowId, None)

    def sel(self, name: str, rowId: int, columnId: int) -> str:
        if name not in self.data:
            return "<null>"

        tbl = self.data[name]

        if rowId not in tbl.rows or not 1 <= columnId <= tbl.cols:
            return "<null>"

        return tbl.rows[rowId][columnId - 1]

    def exp(self, name: str) -> list[str]:
        if name not in self.data:
            return []

        tbl = self.data[name]
        ret = []

        for rowId, row in tbl.rows.items():
            ret.append(",".join((str(rowId), *row)))

        return ret


# Your SQL object will be instantiated and called as such:
# obj = SQL(names, columns)
# param_1 = obj.ins(name,row)
# obj.rmv(name,rowId)
# param_3 = obj.sel(name,rowId,columnId)
# param_4 = obj.exp(name)
```
