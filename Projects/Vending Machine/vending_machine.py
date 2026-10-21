"""Model one vending machine's inventory, cash, and customer payment.
Use as a standalone State-pattern exercise for low-level design interviews.

All money is integer cents. Calls are sequential and dispensing always succeeds:
select() commits the sale and completes internal dispensing before returning.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum, auto


# ---------- Inventory and errors ----------

DENOMINATIONS = frozenset({5, 10, 20, 50, 100, 200})


@dataclass
class Item:
    name: str
    price_cents: int
    count: int

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("item name must be nonempty")
        if type(self.price_cents) is not int or self.price_cents <= 0:
            raise ValueError("price must be positive integer cents")
        if type(self.count) is not int or self.count < 0:
            raise ValueError("stock must be a nonnegative integer")


class Reason(Enum):
    UNKNOWN_ITEM = auto()
    SOLD_OUT = auto()
    SHORT = auto()
    NO_CHANGE = auto()


class SaleRefused(Exception):
    def __init__(self, name: str, reason: Reason) -> None:
        super().__init__(f"can't sell {name}: {reason.name}")
        self.reason = reason


class IllegalActionError(Exception):
    def __init__(self, state: State, event: str) -> None:
        super().__init__(f"{event} not allowed in {type(state).__name__}")


# ---------- States ----------

class State:
    def insert(self, m: Machine, coin: int) -> None:
        raise IllegalActionError(self, "insert")

    def select(self, m: Machine, name: str) -> Counter[int]:
        raise IllegalActionError(self, "select")

    def cancel(self, m: Machine) -> Counter[int]:
        raise IllegalActionError(self, "cancel")

    def dispense(self, m: Machine) -> None:
        raise IllegalActionError(self, "dispense")

    def restock(self, m: Machine, name: str, count: int) -> None:
        raise IllegalActionError(self, "restock")


class Idle(State):
    def insert(self, m: Machine, coin: int) -> None:
        m._accept(coin)
        m._state = HasMoney()

    def restock(self, m: Machine, name: str, count: int) -> None:
        m._add_stock(name, count)


class HasMoney(State):
    def insert(self, m: Machine, coin: int) -> None:
        m._accept(coin)

    def select(self, m: Machine, name: str) -> Counter[int]:
        change = m._sell(name)
        m._state = Dispensing()
        return change

    def cancel(self, m: Machine) -> Counter[int]:
        refund = m._refund()
        m._state = Idle()
        return refund


class Dispensing(State):
    def dispense(self, m: Machine) -> None:
        m._state = Idle() if m._has_stock() else SoldOut()


class SoldOut(State):
    def restock(self, m: Machine, name: str, count: int) -> None:
        m._add_stock(name, count)
        m._state = Idle()


# ---------- Machine ----------

class Machine:
    def __init__(self, items: Iterable[Item], coins: dict[int, int]) -> None:
        self._items: dict[str, Item] = {}
        for item in items:
            if item.name in self._items:
                raise ValueError(f"duplicate item: {item.name}")
            self._items[item.name] = Item(item.name, item.price_cents, item.count)
        for coin, count in coins.items():
            if type(coin) is not int or coin not in DENOMINATIONS:
                raise ValueError(f"unsupported coin: {coin}")
            if type(count) is not int or count < 0:
                raise ValueError("coin count must be a nonnegative integer")
        self._coins = Counter(coins)
        self._inserted: Counter[int] = Counter()
        self._state: State = Idle() if self._has_stock() else SoldOut()

    @property
    def balance_cents(self) -> int:
        return sum(coin * count for coin, count in self._inserted.items())

    def insert(self, coin: int) -> None:
        self._state.insert(self, coin)

    def select(self, name: str) -> Counter[int]:
        change = self._state.select(self, name)
        self._state.dispense(self)
        return change

    def cancel(self) -> Counter[int]:
        return self._state.cancel(self)

    def restock(self, name: str, count: int) -> None:
        self._state.restock(self, name, count)

    # ---------- Inventory and payment operations ----------

    def _accept(self, coin: int) -> None:
        if type(coin) is not int or coin not in DENOMINATIONS:
            raise ValueError(f"unsupported coin: {coin}")
        self._inserted[coin] += 1

    def _refund(self) -> Counter[int]:
        refund, self._inserted = self._inserted, Counter()
        return refund

    def _add_stock(self, name: str, count: int) -> None:
        if type(count) is not int or count <= 0:
            raise ValueError("restock count must be a positive integer")
        if name not in self._items:
            raise ValueError(f"unknown item: {name}")
        self._items[name].count += count

    def _has_stock(self) -> bool:
        return any(item.count > 0 for item in self._items.values())

    def _sell(self, name: str) -> Counter[int]:
        available = self._coins + self._inserted

        def make_change(amount: int) -> Counter[int] | None:
            # shortcut: search every held coin; use for a small tray, optimize for bulk cash.
            best: list[Counter[int] | None] = [Counter()] + [None] * amount
            for coin in available.elements():
                # Descending amounts prevent spending the same physical coin twice.
                for total in range(amount, coin - 1, -1):
                    previous, current = best[total - coin], best[total]
                    if previous is not None and (
                        current is None or previous.total() + 1 < current.total()
                    ):
                        best[total] = previous + Counter({coin: 1})
            return best[amount]

        item = self._items.get(name)
        if item is None:
            raise SaleRefused(name, Reason.UNKNOWN_ITEM)
        if item.count == 0:
            raise SaleRefused(name, Reason.SOLD_OUT)
        if self.balance_cents < item.price_cents:
            raise SaleRefused(name, Reason.SHORT)
        change = make_change(self.balance_cents - item.price_cents)
        if change is None:
            raise SaleRefused(name, Reason.NO_CHANGE)

        item.count -= 1
        self._coins = available - change
        self._inserted.clear()
        return change


# ---------- Runnable example ----------

if __name__ == "__main__":
    machine = Machine([Item("tea", 140, 2)], {50: 1, 20: 3})
    machine.insert(200)
    change = machine.select("tea")
    assert change == Counter({20: 3})
    assert machine.balance_cents == 0
    assert isinstance(machine._state, Idle)
    print("Change (cents):", dict(change))

    machine.insert(100)
    refund = machine.cancel()
    assert refund == Counter({100: 1})
    print("Refund (cents):", dict(refund))
