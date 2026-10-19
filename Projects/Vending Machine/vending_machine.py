"""Vending machine, GoF State: one class per state, base state rejects every event."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, auto

DENOMS = frozenset(map(Decimal, ["0.05", "0.10", "0.20", "0.50", "1", "2"]))


@dataclass
class Item:
    name: str
    price: Decimal
    count: int


# === errors ===


class Reason(Enum):
    UNKNOWN_ITEM = auto()
    SOLD_OUT = auto()
    SHORT = auto()
    NO_CHANGE = auto()


class IllegalActionError(Exception):
    def __init__(self, state: "State", event: str) -> None:
        super().__init__(f"{event} not allowed in {type(state).__name__}")
        self.state = state
        self.event = event


class SaleRefused(Exception):
    def __init__(self, item_name: str, reason: Reason) -> None:
        super().__init__(f"can't sell {item_name}: {reason.name}")
        self.item_name = item_name
        self.reason = reason


# === states ===


class State:
    def insert(self, m: "Machine", coin: Decimal) -> None:
        raise IllegalActionError(self, "insert")

    def select(self, m: "Machine", name: str) -> Counter[Decimal]:
        raise IllegalActionError(self, "select")

    def cancel(self, m: "Machine") -> Counter[Decimal]:
        raise IllegalActionError(self, "cancel")

    def dispensed(self, m: "Machine") -> None:
        raise IllegalActionError(self, "dispensed")

    def restock(self, m: "Machine", name: str, n: int) -> None:
        raise IllegalActionError(self, "restock")


class Idle(State):
    def insert(self, m, coin):
        m._accept(coin)
        m.state = HasMoney()

    def restock(self, m, name, n):
        m._add_stock(name, n)


class HasMoney(State):
    def insert(self, m, coin):
        m._accept(coin)

    def select(self, m, name):
        item: Item | None = m.items.get(name)

        if item is None: raise SaleRefused(name, Reason.UNKNOWN_ITEM)
        if item.count == 0: raise SaleRefused(name, Reason.SOLD_OUT)
        if m.balance < item.price: raise SaleRefused(name, Reason.SHORT)

        change = m._change_for(m.balance - item.price)
        if change is None:
            raise SaleRefused(name, Reason.NO_CHANGE)

        m._commit_sale(name, change)
        m.state = Dispensing()
        return change

    def cancel(self, m):
        refund = m._refund_all()
        m.state = Idle()
        return refund


class Dispensing(State):
    def dispensed(self, m):
        m.state = Idle() if m._has_stock() else OutOfService()


class OutOfService(State):
    def restock(self, m, name, n):
        m._add_stock(name, n)
        m.state = Idle()


# === machine ===


class Machine:
    def __init__(self, items: Iterable[Item], coins: dict[Decimal, int]) -> None:
        items = tuple(items)
        self.items = {item.name: item for item in items}
        if len(self.items) != len(items):
            raise ValueError("duplicate item names")
        self.coins = Counter(coins)
        self.inserted: Counter[Decimal] = Counter()
        self.state: State = Idle() if self._has_stock() else OutOfService()

    @property
    def balance(self) -> Decimal:
        return sum((d * n for d, n in self.inserted.items()), Decimal(0))

    def insert(self, coin: Decimal):
        return self.state.insert(self, coin)

    def select(self, name: str):
        return self.state.select(self, name)

    def cancel(self):
        return self.state.cancel(self)

    def dispensed(self):
        return self.state.dispensed(self)

    def restock(self, name: str, n: int):
        return self.state.restock(self, name, n)

    def _accept(self, coin: Decimal) -> None:
        if coin not in DENOMS:
            raise ValueError(f"unknown coin {coin}")
        self.coins[coin] += 1
        self.inserted[coin] += 1

    def _change_for(self, amount: Decimal) -> Counter[Decimal] | None:
        # ponytail: 0/1 knapsack over every physical coin, O(coins x cents); fine for one tube
        target = int(amount * 100)
        best: list[Counter[Decimal] | None] = [Counter()] + [None] * target
        for coin in self.coins.elements():
            c = int(coin * 100)
            for a in range(target, c - 1, -1):
                prev, cur = best[a - c], best[a]
                if prev is not None and (cur is None or prev.total() + 1 < cur.total()):
                    best[a] = prev + Counter({coin: 1})
        return best[target]

    def _commit_sale(self, name: str, change: Counter[Decimal]) -> None:
        # it's also possible to do this below. Given how counter whole operations work and that negative
        # keys are dropped on whole ops
        # assert not (change - self.coins)
        assert change <= self.coins, "paying out coins the machine doesn't hold"
        self.items[name].count -= 1
        self.coins -= change
        self.inserted.clear()

    def _refund_all(self) -> Counter[Decimal]:
        refund, self.inserted = self.inserted, Counter()
        self.coins -= refund
        return refund

    def _add_stock(self, name: str, n: int) -> None:
        self.items[name].count += n

    def _has_stock(self) -> bool:
        return any(item.count for item in self.items.values())
