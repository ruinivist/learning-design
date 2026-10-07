# Browser history

Trivial if you make "at" as 1 based ( otherwise too but this model is nicer )

```python
class BrowserHistory:

    def __init__(self, homepage: str):
        self.hist = [homepage]
        # at is the 1 based index
        self.at = 1

    def visit(self, url: str) -> None:
        self.hist = self.hist[: self.at]
        self.hist.append(url)
        self.at = len(self.hist)

    def back(self, steps: int) -> str:
        self.at = max(1, self.at - steps)
        return self.hist[self.at - 1]

    def forward(self, steps: int) -> str:
        self.at = min(len(self.hist), self.at + steps)
        return self.hist[self.at - 1]
```
