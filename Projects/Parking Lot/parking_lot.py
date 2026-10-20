"""Provides parking state, allocation, pricing, payment, and display updates.
Entry and exit panels coordinate the in-memory example wired in main().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Callable, Generator, Iterable, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import IntEnum
from itertools import count
import logging
from math import ceil
from threading import RLock

# ---------- Vocabulary and errors ----------


class SpotSize(IntEnum):
    MOTORCYCLE = 1
    COMPACT = 2
    LARGE = 3


class VehicleType(IntEnum):
    # Each value names the minimum spot size for this one-spot vehicle model.
    MOTORCYCLE = SpotSize.MOTORCYCLE
    CAR = SpotSize.COMPACT
    VAN = SpotSize.LARGE


class ParkingError(Exception):
    """Base for parking failures handled by panels or their callers."""


class LotFullError(ParkingError):
    """No compatible free spot exists."""


class InvalidTicketError(ParkingError):
    """The ticket is unknown or already settled."""


class SpotStateError(ParkingError):
    """An allocation or occupancy change violates the parking model."""


class PaymentFailedError(ParkingError):
    """Payment failed; checkout must leave the vehicle parked."""


# ---------- Immutable records ----------


@dataclass(frozen=True, slots=True, kw_only=True)
class Vehicle:
    """Carries vehicle data through admission and ticketing.
    Callers supply a canonical plate used to identify an active stay.
    """

    plate: str
    type: VehicleType

    # __post__init__ is unqieu to dataclasses, python auto generates it the __init__
    # if I don't give one and then calls __post_init__, this is better to add validations
    # in
    def __post_init__(self) -> None:
        if not self.plate.strip():
            raise ValueError("Plate must not be blank")


@dataclass(frozen=True, slots=True, kw_only=True)
class Ticket:
    """Records a stay without exposing mutable parking state.
    Checkout and pricing use the entry-time snapshot, including spot size.
    """

    id: str
    # if it's a different entity, prefix with that
    spot_id: str
    floor_id: int
    vehicle: Vehicle
    spot_size: SpotSize
    entry_time: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class Receipt:
    ticket_id: str
    amount: Decimal
    method: str
    # these are all ust timestamps
    paid_at: datetime


# ---------- Spots and floors ----------


class Spot:
    __slots__ = ("_id", "_size", "_occupied_by")

    def __init__(self, *, id: str, size: SpotSize) -> None:
        self._id, self._size = id, size
        self._occupied_by: Vehicle | None = None

    # this whole charade is just to keep vars as _id and allow callers
    # to read them
    @property
    def id(self) -> str:
        return self._id

    @property
    def size(self) -> SpotSize:
        return self._size

    @property
    def is_free(self) -> bool:
        return self._occupied_by is None

    def can_fit(self, vehicle: Vehicle) -> bool:
        return self._size >= vehicle.type

    def _occupy(self, vehicle: Vehicle) -> None:
        if not self.is_free or not self.can_fit(vehicle):
            raise SpotStateError(f"{self.id} is occupied or incompatible")
        self._occupied_by = vehicle

    def _free(self) -> None:
        if self.is_free:
            raise SpotStateError(f"{self.id} is already free")
        self._occupied_by = None


class Floor:
    """Owns spots and publishes committed availability changes.
    Reads and mutations run during setup or under the owning lot's lock.
    """

    def __init__(self, floor_id: int, spots: Iterable[Spot]) -> None:
        self._id = floor_id
        self._spots: dict[str, Spot] = {}
        self._observers: list[Callable[[Floor], None]] = []
        for spot in spots:
            if spot.id in self._spots:
                raise ValueError(f"Duplicate spot ID on floor {floor_id}: {spot.id}")
            self._spots[spot.id] = spot

    @property
    def id(self) -> int:
        return self._id

    @property
    def free_spots(self) -> tuple[Spot, ...]:
        # Read eagerly so allocation observes state within the lot's lock.
        return tuple(spot for spot in self._spots.values() if spot.is_free)

    @property
    def counts(self) -> dict[SpotSize, int]:
        return Counter(spot.size for spot in self.free_spots)

    @property
    def free_count(self) -> int:
        return len(self.free_spots)

    @property
    def total_count(self) -> int:
        return len(self._spots)

    def attach(self, observer: Callable[[Floor], None]) -> None:
        """Registers a read-only display callback during construction."""
        self._observers.append(observer)

    def _notify(self) -> None:
        for observer in tuple(self._observers):
            try:
                observer(self)
            except Exception:
                # A display failure cannot undo parking or suppress other displays.
                logging.getLogger(__name__).exception("Display update failed")

    def _take(self, spot: Spot, vehicle: Vehicle) -> None:
        if self._spots.get(spot.id) is not spot:
            raise SpotStateError(f"{spot.id} is not on floor {self.id}")
        spot._occupy(vehicle)

    def _release(self, spot_id: str) -> None:
        spot = self._spots.get(spot_id)
        if spot is None:
            raise SpotStateError(f"{spot_id} is not on floor {self.id}")
        spot._free()


# ---------- Allocation policy ----------

Allocation = tuple[Floor, Spot]


class AllocationStrategy(ABC):
    """Selects a spot without changing it.
    The lot validates and commits the selection under its lock.
    """

    @abstractmethod
    def choose(
        self, floors: Iterable[Floor], vehicle: Vehicle
    ) -> Allocation | None: ...


class AnyFreeSpotAllocation(AllocationStrategy):
    def choose(self, floors: Iterable[Floor], vehicle: Vehicle) -> Allocation | None:
        for floor in floors:
            for spot in floor.free_spots:
                if spot.can_fit(vehicle):
                    return floor, spot
        return None


# ---------- Parking state ----------


class ParkingLot:
    """Keeps active tickets and occupied spots consistent under one lock.
    Panels use it for admission, ticket lookup, and internal checkout transitions.
    """

    def __init__(self, floors: Sequence[Floor], allocation: AllocationStrategy) -> None:
        self._floors = {floor.id: floor for floor in floors}
        if len(self._floors) != len(floors):
            raise ValueError("Duplicate floor IDs")
        self._allocation = allocation
        self._active: dict[str, Ticket] = {}
        self._checking_out: set[str] = set()
        self._seq = count(1)
        self._lock = RLock()

    def park(self, vehicle: Vehicle, now: datetime) -> Ticket:
        """Admits one vehicle atomically; now must be an aware UTC timestamp."""
        with self._lock:
            # shortcut: linear scans suit this example; index plates/spots for large lots.
            if any(t.vehicle.plate == vehicle.plate for t in self._active.values()):
                raise ParkingError(f"{vehicle.plate} is already parked")
            choice = self._allocation.choose(self._floors.values(), vehicle)
            if choice is None:
                raise LotFullError(vehicle.type.name)
            floor, spot = choice
            if self._floors.get(floor.id) is not floor:
                raise SpotStateError(f"Floor {floor.id} does not belong to this lot")
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
            floor._notify()
            return ticket

    def find_active(self, ticket_id: str) -> Ticket:
        with self._lock:
            ticket = self._active.get(ticket_id)
            if ticket is None:
                raise InvalidTicketError(ticket_id)
            return ticket

    @contextmanager
    def _checkout(self, ticket_id: str) -> Generator[Ticket, None, None]:
        """Holds checkout state stable while ExitPanel coordinates payment.
        A successful block releases the spot; an exception leaves it occupied.
        """
        # shortcut: callbacks/payment hold the lot lock; redesign for remote payments.
        with self._lock:
            ticket = self.find_active(ticket_id)
            if ticket_id in self._checking_out:
                raise ParkingError(f"Checkout already in progress: {ticket_id}")
            self._checking_out.add(ticket_id)
            try:
                yield ticket
                self._release(ticket)
            finally:
                self._checking_out.remove(ticket_id)

    def _release(self, ticket: Ticket) -> None:
        # Only _checkout calls this, with the lot lock held.
        if self._active.get(ticket.id) is not ticket:
            raise InvalidTicketError(ticket.id)
        floor = self._floors[ticket.floor_id]
        floor._release(ticket.spot_id)
        del self._active[ticket.id]
        floor._notify()

    @property
    def free_count(self) -> int:
        with self._lock:
            return sum(floor.free_count for floor in self._floors.values())

    @property
    def total_count(self) -> int:
        return sum(floor.total_count for floor in self._floors.values())


# ---------- Pricing and payment ----------


def money(value: Decimal) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
        raise ValueError("Money must be a finite, nonnegative Decimal")
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class PricingStrategy(ABC):
    """Computes a fee without side effects.
    Quotes and settlement supply aware UTC entry and exit timestamps.
    """

    @abstractmethod
    def price(self, ticket: Ticket, exit_time: datetime) -> Decimal: ...


class HourlyPricing(PricingStrategy):
    """Waives short stays, then charges started hours measured from entry."""

    def __init__(
        self,
        first_hour: Decimal = Decimal("4.00"),
        later_hour: Decimal = Decimal("3.50"),
        grace_minutes: int = 15,
    ) -> None:
        if type(grace_minutes) is not int or grace_minutes < 0:
            raise ValueError("Grace minutes must be a nonnegative integer")
        self._first_hour = money(first_hour)
        self._later_hour = money(later_hour)
        self._grace_minutes = grace_minutes

    def price(self, ticket: Ticket, exit_time: datetime) -> Decimal:
        seconds = (exit_time - ticket.entry_time).total_seconds()
        if seconds < 0:
            raise ValueError("Exit time precedes entry time")
        if seconds <= self._grace_minutes * 60:
            return Decimal("0.00")
        hours = ceil(seconds / 3600)
        return money(self._first_hour + self._later_hour * (hours - 1))


class PaymentProcessor(ABC):
    """Returns a receipt only after successful payment.
    ExitPanel retains the stay when charge raises PaymentFailedError or another error.
    """

    @abstractmethod
    def charge(self, amount: Decimal, ticket_id: str, now: datetime) -> Receipt: ...


class CashPayment(PaymentProcessor):
    """Simulates confirmed cash payment for the example."""

    def charge(self, amount: Decimal, ticket_id: str, now: datetime) -> Receipt:
        return Receipt(
            ticket_id=ticket_id, amount=money(amount), method="cash", paid_at=now
        )


# ---------- Display ----------


class DisplayBoard:
    def __init__(self, floor: Floor) -> None:
        self._floor_id = floor.id
        self._counts: dict[SpotSize, int] = {}
        floor.attach(self.update)
        self.update(floor)

    def update(self, floor: Floor) -> None:
        self._counts = floor.counts

    def render(self) -> str:
        counts = self._counts
        body = "  ".join(f"{size.name} {n}" for size, n in sorted(counts.items()))
        return f"Floor {self._floor_id}: {body or 'FULL'}"


# ---------- Entry and exit coordination ----------

Clock = Callable[[], datetime]


def system_clock() -> datetime:
    # Explicit timestamps and injected clocks must follow the same UTC contract.
    return datetime.now(UTC)


class EntryPanel:
    def __init__(self, lot: ParkingLot, clock: Clock = system_clock) -> None:
        self._lot, self._clock = lot, clock

    def park(self, vehicle: Vehicle, now: datetime | None = None) -> Ticket:
        return self._lot.park(vehicle, now if now is not None else self._clock())


class ExitPanel:
    """Coordinates pricing and payment before the lot releases a vehicle.
    Quotes are advisory; settlement prices the stay again under the shared lock.
    """

    def __init__(
        self,
        lot: ParkingLot,
        pricing: PricingStrategy,
        payment: PaymentProcessor,
        clock: Clock = system_clock,
    ) -> None:
        self._lot, self._pricing, self._payment = lot, pricing, payment
        self._clock = clock

    def _price(self, ticket: Ticket, at: datetime) -> Decimal:
        if at < ticket.entry_time:
            raise ValueError("Exit time precedes entry time")
        return money(self._pricing.price(ticket, at))

    def quote(self, ticket_id: str, now: datetime | None = None) -> Decimal:
        at = now if now is not None else self._clock()
        return self._price(self._lot.find_active(ticket_id), at)

    def settle(self, ticket_id: str, now: datetime | None = None) -> Receipt:
        at = now if now is not None else self._clock()
        with self._lot._checkout(ticket_id) as ticket:
            amount = self._price(ticket, at)
            if amount > 0:
                receipt = self._payment.charge(amount, ticket.id, at)
            else:
                receipt = Receipt(
                    ticket_id=ticket.id, amount=amount, method="free", paid_at=at
                )
        return receipt


# ---------- Composition and happy path ----------

FloorSpec = dict[SpotSize, int]


def build_lot(specs: dict[int, FloorSpec]) -> ParkingLot:
    if any(
        type(quantity) is not int or quantity < 0
        for spec in specs.values()
        for quantity in spec.values()
    ):
        raise ValueError("Spot counts must be nonnegative integers")
    floors = [
        Floor(
            floor_id,
            (
                Spot(id=f"{floor_id}-{size.name}-{index}", size=size)
                for size, quantity in spec.items()
                for index in range(1, quantity + 1)
            ),
        )
        for floor_id, spec in specs.items()
    ]
    return ParkingLot(floors, AnyFreeSpotAllocation())


def main() -> None:
    floor = Floor(1, [Spot(id="1-C1", size=SpotSize.COMPACT)])
    board = DisplayBoard(floor)
    lot = ParkingLot([floor], AnyFreeSpotAllocation())
    entry = EntryPanel(lot)
    exit_panel = ExitPanel(lot, HourlyPricing(), CashPayment())

    print(board.render())
    ticket = entry.park(Vehicle(plate="KA01AB1234", type=VehicleType.CAR))
    print(f"Parked: {ticket.id} at {ticket.spot_id}")
    print(board.render())

    exit_time = ticket.entry_time + timedelta(hours=2)
    print(f"Quote after two hours: {exit_panel.quote(ticket.id, exit_time)}")
    receipt = exit_panel.settle(ticket.id, exit_time)
    print(f"Paid: {receipt.amount} by {receipt.method}")
    print(board.render())


if __name__ == "__main__":
    main()
