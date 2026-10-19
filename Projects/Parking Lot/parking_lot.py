"""LLD practice: a multi-floor parking lot. Interview-sized -- ~40 min to write.

Every abstraction has exactly one implementation. A second pricing rule,
payment method, or allocation policy is a new class in the section that owns
that concept, and nothing else moves.

Common mistakes and correctness tradeoffs live in parking lot.md.
Keep this file bare: in the room you speak the rationale, you don't type it.
"""

from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import IntEnum
from itertools import count
import logging
from math import ceil
from threading import RLock
from typing import Self

# ===================== vocabulary =====================

# why enums? no type bloat, we wold only need new types if some behavior was overriden
# here only "consumers" behave differently like pricing and lot picker, this itself does not own
# those behavs so enum is enough as we don't override anything
class SpotSize(IntEnum):
    MOTORCYCLE = 1
    COMPACT = 2
    LARGE = 3


# the two enums share a numbering on purpose: a VehicleType's value IS the smallest SpotSize it fits.
# This can be made into more complex can_fit but this is enough for now
# nore that the allocation strategy DOES become couple with the enum values, something that isn't idea
# but good enough for now, a map is just more bloat, I can make an indirection at someplace else via
# a dict or something that'll just map it value here to size there
class VehicleType(IntEnum):
    MOTORCYCLE = 1
    CAR = 2
    VAN = 3


# ===================== errors =====================

# the base error class for the app
class ParkingError(Exception):
    """One base so callers can catch the lot."""

# derived ones
class LotFullError(ParkingError):
    """No eligible spot for this vehicle."""


class InvalidTicketError(ParkingError):
    """Unknown, already settled, or not the object the lot issued."""


class SpotStateError(ParkingError):
    """Occupied twice or freed twice -- an internal bug, never input."""


class PaymentFailedError(ParkingError):
    """Declined. The spot must stay occupied."""


# ===================== data only models =====================


@dataclass(frozen=True, slots=True, kw_only=True)
class Vehicle:
    """Type is a field, not a subclass -- nothing dispatches on it."""

    plate: str
    type: VehicleType #fk


@dataclass(frozen=True, slots=True, kw_only=True)
class Ticket:
    """spot_id not Spot: a ticket outlives and out-travels the spot it names.

    spot_size is copied, not looked up, so price() stays (ticket, exit_time) --
    a size-tiered rule is a new PricingStrategy, not a lot reference.
    """

    id: str
    spot_id: str
    floor_id: int
    vehicle: Vehicle # fk
    spot_size: SpotSize # fk
    entry_time: datetime


# ===================== spot =====================

# fields: an id to name it, size and occupant for its own behaviour. No floor
# back-pointer -- nothing read it, and Floor already owns the floor->spot map.
# eq=False on purpose: an entity, not a value. Identity __eq__ and __hash__
# survives -- dataclass nulls it only when it generates __eq__.
@dataclass(slots=True, kw_only=True, eq=False)
class Spot:
    id: str
    size: SpotSize
    occupied_by: Vehicle | None = field(default=None, init=False)

    @property
    def is_free(self) -> bool:
        return self.occupied_by is None

    def occupy(self, vehicle: Vehicle) -> None:
        if self.occupied_by is not None:
            raise SpotStateError(f"{self.id} already holds {self.occupied_by.plate}")
        # this class would own any size checks, none for now
        self.occupied_by = vehicle

    def free(self) -> None:
        if self.occupied_by is None:
            raise SpotStateError(f"{self.id} is already free")
        self.occupied_by = None


# ===================== floor =====================


class Observer[T](ABC):
    """GoF Observer. Generic so update() keeps the concrete subject type."""

    @abstractmethod
    def update(self, subject: T) -> None: ...


class Subject(ABC):
    """GoF Subject: the observer list, attach/detach, and notify.

    Self typing means a subclass's observers are Observer[ThatSubclass] --
    no cast in notify(), no `class Floor(Subject["Floor"])` self-reference.
    """

    def __init__(self) -> None:
        self._observers: list[Observer[Self]] = []

    def attach(self, observer: Observer[Self]) -> None:
        self._observers.append(observer)

    def detach(self, observer: Observer[Self]) -> None:
        self._observers.remove(observer)

    def notify(self) -> None:
        # A failed display must not fail a committed parking operation or other displays.
        for observer in tuple(self._observers):
            try:
                observer.update(self)
            except Exception:
                logging.getLogger(__name__).exception("Observer update failed: %r", observer)


class Floor(Subject):
    """Owns its spots. Free-ness lives on the Spot only -- no index to drift.

    LOCKING: nothing here locks. Public members are reads, safe for a strategy
    or a board. Underscored members mutate and assume the caller already holds
    ParkingLot's lock -- the lot is their only legitimate caller. Reads are
    eager for the same reason, see free_spots.
    """

    def __init__(self, floor_id: int, spots: Iterable[Spot]) -> None:
        super().__init__()
        self.id = floor_id
        # Reject duplicate IDs before a dictionary silently drops a spot.
        self._spots: dict[str, Spot] = {}
        for spot in spots:
            if spot.id in self._spots:
                raise ValueError(f"Duplicate spot ID on floor {floor_id}: {spot.id}")
            self._spots[spot.id] = spot


    @property
    def free_spots(self) -> tuple[Spot, ...]:
        """The one derivation. counts and free_count are both just this, reduced.

        A tuple, not a generator: a generator defers the read to the consumer's
        next(), so whether it ran under the lock would depend on a caller you
        cannot see from here. Eager means the read happens in the caller's
        critical section or not at all.
        """
        # ponytail: O(n) per read, n = one floor's spots. A park costs one read to
        # allocate plus one per board, via notify() -> counts. Free-index at 10k+.
        return tuple(s for s in self._spots.values() if s.is_free)

    @property
    def counts(self) -> dict[SpotSize, int]:
        """Counted from the spots themselves, so it cannot disagree with them."""
        return Counter(s.size for s in self.free_spots)

    @property
    def free_count(self) -> int:
        return len(self.free_spots)

    @property
    def total_count(self) -> int:
        return len(self._spots)

    # _take and _release take different arguments on purpose: entry and exit are
    # not mirror images. At entry the strategy has already picked a live Spot; at
    # exit all the lot holds is a string off the ticket. Both guards are the same
    # dict lookup -- ownership is "is this spot mine", asked two ways.

    def _take(self, spot: Spot, vehicle: Vehicle) -> None:
        if self._spots.get(spot.id) is not spot:  # a buggy strategy, not input
            raise SpotStateError(f"{spot.id} is not on floor {self.id}")
        spot.occupy(vehicle)  # raises if the strategy handed back a taken spot

    def _release(self, spot_id: str) -> None:
        spot = self._spots.get(spot_id)
        if spot is None:  # the lookup IS the ownership check
            raise SpotStateError(f"{spot_id} is not on floor {self.id}")
        spot.free()


# ===================== lot =====================


# names the concept, and one edit when TRUCK makes it tuple[Floor, Sequence[Spot]]
Allocation = tuple[Floor, Spot]


class AllocationStrategy(ABC):
    """Reads floor state, returns a choice. The lot does the mutation."""

    @abstractmethod
    def choose(
        self, floors: Sequence[Floor], vehicle: Vehicle
    ) -> Allocation | None: ...


class ParkingLot:
    """Aggregate root: floors, the lock, the ticket registry. Knows nothing of money."""

    def __init__(self, floors: Sequence[Floor], allocation: AllocationStrategy) -> None:
        self.floors = tuple(floors)
        self._by_id = {floor.id: floor for floor in self.floors}
        # Entry and exit must resolve each floor ID to the same floor.
        if len(self._by_id) != len(self.floors):
            raise ValueError("Duplicate floor IDs")
        self._allocation = allocation
        # for now one coarse lot-wide lock; can make it more granular if needed so say locking at gates/floors
        self._lock = RLock()
        self._active: dict[str, Ticket] = {}
        self._seq = count(1)

    def park(self, vehicle: Vehicle, now: datetime) -> Ticket:
        """Choose, take, mint and register -- all under one lock."""
        with self._lock:
            choice = self._allocation.choose(self.floors, vehicle)
            if choice is None:
                raise LotFullError(vehicle.type.name)
            floor, spot = choice
            floor._take(spot, vehicle)
            ticket = Ticket(
                id=f"T-{next(self._seq):04d}",
                spot_id=spot.id,
                floor_id=floor.id,
                vehicle=vehicle,
                spot_size=spot.size,
                entry_time=now,
            )
            self._active[ticket.id] = ticket
            # Notify only after occupancy and ticket state agree, still under the lock.
            floor.notify()
            return ticket

    def find_active(self, ticket_id: str) -> Ticket:
        """Authoritative lookup. A panel can obtain a Ticket, never originate one:
        untrusted input crosses as an id, validated output as a frozen object.
        Note the Ticket is immutable but not self-validating -- it says nothing
        about whether it is still in _active by the time the caller uses it.
        """
        with self._lock:
            ticket = self._active.get(ticket_id)
            if ticket is None:
                raise InvalidTicketError(ticket_id)
            return ticket

    def release(self, ticket: Ticket) -> None:
        with self._lock:
            if self._active.get(ticket.id) is not ticket:
                raise InvalidTicketError(ticket.id)
            floor = self._by_id[ticket.floor_id]
            floor._release(ticket.spot_id)
            del self._active[ticket.id]
            floor.notify()

    @contextmanager
    def checkout(self, ticket_id: str) -> Iterator[Ticket]:
        # All exit panels share this lock; separate lookup/release locks permit double charging.
        # shortcut: payment blocks the lot, use ticket-level coordination for network payments.
        with self._lock:
            ticket = self.find_active(ticket_id)
            yield ticket
            self.release(ticket)

    @property
    def free_count(self) -> int:
        with self._lock:  # a scan across floors; unlocked it tears mid-park
            return sum(floor.free_count for floor in self.floors)

    @property
    def total_count(self) -> int:
        # no lock: spots are never added or removed after construction
        return sum(floor.total_count for floor in self.floors)


# ===================== allocation =====================


class AnyFreeSpotAllocation(AllocationStrategy):
    """First free spot the vehicle fits in.

    Because the choice is a Spot, smallest-first is a true sibling: swap this for
    min(floor.free_spots, key=...), nothing else moves. Nearest-gate is NOT --
    choose() has no gate, so it needs a gate id threaded panel -> park -> here.
    Left out on purpose: an argument every current strategy ignores.
    """

    def choose(
        self, floors: Sequence[Floor], vehicle: Vehicle
    ) -> Allocation | None:
        for floor in floors:
            for spot in floor.free_spots:
                if spot.size >= vehicle.type:
                    return floor, spot
        return None


# ===================== pricing =====================

# Decimal only, on purpose: a float must never reach money. Decimal(0.1) is
# 0.10000000000000000555..., Decimal("0.1") is exact.
def money(value: Decimal) -> Decimal:
    # Negative or nonfinite prices are errors, not free parking.
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
        raise ValueError("Money must be a finite, nonnegative Decimal")
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class PricingStrategy(ABC):
    """Pure function of (ticket, exit_time) -- the clock is an argument."""

    @abstractmethod
    def price(self, ticket: Ticket, exit_time: datetime) -> Decimal: ...


class HourlyPricing(PricingStrategy):
    """Per started hour after a grace period. A daily cap is a sibling, not an `if`."""

    def __init__(
        self,
        first_hour: Decimal = Decimal("4.00"),
        later_hour: Decimal = Decimal("3.50"),
        grace_minutes: int = 15,
    ) -> None:
        # Validate configuration before it can produce an invalid quote or charge.
        for rate in (first_hour, later_hour):
            money(rate)
        if not isinstance(grace_minutes, int) or grace_minutes < 0:
            raise ValueError("Grace minutes must be a nonnegative integer")
        self.first_hour = first_hour
        self.later_hour = later_hour
        self.grace_minutes = grace_minutes

    def price(self, ticket: Ticket, exit_time: datetime) -> Decimal:
        minutes = (exit_time - ticket.entry_time).total_seconds() / 60
        if minutes < 0:
            raise ValueError("exit_time precedes entry_time")
        if minutes <= self.grace_minutes:
            return money(Decimal(0))
        hours = max(1, ceil(minutes / 60))
        return money(self.first_hour + self.later_hour * (hours - 1))


# ===================== payment =====================


@dataclass(frozen=True, slots=True, kw_only=True)
class Receipt:
    ticket_id: str
    amount: Decimal
    method: str
    paid_at: datetime


class PaymentProcessor(ABC):
    """DIP: ExitPanel depends on this, not on cash. charge() is a template method."""

    method = "unknown"

    @abstractmethod
    def authorize(self, amount: Decimal) -> bool: ...

    def charge(self, amount: Decimal, ticket_id: str, now: datetime) -> Receipt:
        if not self.authorize(amount):
            raise PaymentFailedError(f"{self.method} declined {amount}")
        return Receipt(
            ticket_id=ticket_id, amount=amount, method=self.method, paid_at=now
        )


class CashPayment(PaymentProcessor):
    method = "cash"

    def authorize(self, amount: Decimal) -> bool:
        return True


# ===================== display =====================


class DisplayBoard(Observer[Floor]):
    """Free-spot counts. Pushed to, never polls."""

    def __init__(self, floor: Floor) -> None:
        self.floor_id = floor.id
        self.counts: dict[str, int] = {}
        floor.attach(self)
        self.update(floor)  # GoF attach only registers, so pull the initial state

    def update(self, subject: Floor) -> None:
        self.counts = {size.name: n for size, n in sorted(subject.counts.items())}

    def render(self) -> str:
        if not self.counts:
            return f"Floor {self.floor_id}: FULL"
        body = "  ".join(f"{name} {n}" for name, n in self.counts.items())
        return f"Floor {self.floor_id}: {body}"


# ===================== panels =====================
# this isn't java, Runnable.run() is really pointless when all you need is a cpp
# like callable
Clock = Callable[[], datetime]


def system_clock() -> datetime:
    return datetime.now(UTC)

# by passing in clock, you can test this easily by mocking a "tick" in clock
# impossible timing issues in tests otherwise if you rely on walltime
class EntryPanel:
    def __init__(self, lot: ParkingLot, clock: Clock = system_clock) -> None:
        self._lot, self._clock = lot, clock

    def park(self, vehicle: Vehicle, now: datetime | None = None) -> Ticket:
        return self._lot.park(vehicle, now or self._clock())


class ExitPanel:
    def __init__(
        self,
        lot: ParkingLot,
        pricing: PricingStrategy,
        payment: PaymentProcessor,
        clock: Clock = system_clock,
    ) -> None:
        self._lot, self._pricing, self._payment = lot, pricing, payment
        self._clock = clock

    def quote(self, ticket_id: str, now: datetime | None = None) -> Decimal:
        """Advisory -- settle re-prices, so the clock runs while they find a card."""
        at = now or self._clock()
        return money(self._pricing.price(self._lot.find_active(ticket_id), at))

    def settle(self, ticket_id: str, now: datetime | None = None) -> Receipt:
        """Price, charge, then release. The ordering is the invariant."""
        at = now or self._clock()
        with self._lot.checkout(ticket_id) as ticket:
            amount = money(self._pricing.price(ticket, at))
            receipt = (
                self._payment.charge(amount, ticket.id, at)  # a decline propagates,
                if amount > 0  # leaving the car parked, which is correct
                else Receipt(ticket_id=ticket.id, amount=money(Decimal(0)), method="free", paid_at=at)
            )
        return receipt


# ===================== composition root =====================

FloorSpec = dict[SpotSize, int]


def build_lot(specs: dict[int, FloorSpec]) -> ParkingLot:
    floors = [
        Floor(
            fid,
            [
                # readable for humans, never parsed: size.name[0] collides the
                # day a second M-size lands. Anything needed from an id is a field.
                Spot(id=f"{fid}{size.name[0]}{i:02d}", size=size)
                for size, quantity in spec.items()
                for i in range(1, quantity + 1)
            ],
        )
        for fid, spec in specs.items()
    ]
    return ParkingLot(floors, AnyFreeSpotAllocation())
