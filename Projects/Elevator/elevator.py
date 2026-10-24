"""Model elevator requests, movement, and assignment across three cars.
Use sequential calls and explicit ticks for a low-level design interview.
"""

from dataclasses import dataclass
from enum import Enum, auto

# ---------- Requests and direction ----------

FLOORS = 10


class Direction(Enum):
    DOWN = -1
    IDLE = 0
    UP = 1


class RequestType(Enum):
    PICKUP_UP = auto()
    PICKUP_DOWN = auto()
    DESTINATION = auto()


@dataclass(frozen=True)
class Request:
    floor: int
    type: RequestType

    def is_valid(self) -> bool:
        # Both entry points use the same floor and request-type checks.
        return (
            type(self.floor) is int
            and 0 <= self.floor < FLOORS
            and isinstance(self.type, RequestType)
        )


# ---------- One elevator ----------


class Elevator:
    def __init__(self) -> None:
        # Start at the ground floor with no work.
        self._current_floor = 0
        self._direction = Direction.IDLE
        self._requests: set[Request] = set()

    @property
    def current_floor(self) -> int:
        return self._current_floor

    @property
    def direction(self) -> Direction:
        return self._direction

    @property
    def requests(self) -> frozenset[Request]:
        # Let callers inspect requests without changing the working set.
        return frozenset(self._requests)

    def add_request(self, request: Request) -> bool:
        # Reject invalid input; requests for this floor are already served.
        if not request.is_valid():
            return False
        if request.floor != self._current_floor:
            self._requests.add(request)
        return True

    def step(self) -> None:
        """Serve a stop, reverse, or move one floor.
        The controller calls this once per simulation tick.
        """
        # No requests means no movement.
        if not self._requests:
            self._direction = Direction.IDLE
            return

        # When idle, start toward the nearest floor; ties go lower.
        if self._direction is Direction.IDLE:
            target = min(
                self._requests,
                key=lambda r: (abs(r.floor - self._current_floor), r.floor),
            )
            self._direction = (
                Direction.UP if target.floor > self._current_floor else Direction.DOWN
            )

        # Serve cabin destinations and pickups going our way, then end this tick.
        pickup_type = (
            RequestType.PICKUP_UP
            if self._direction is Direction.UP
            else RequestType.PICKUP_DOWN
        )
        served = self._requests & {
            Request(self._current_floor, pickup_type),
            Request(self._current_floor, RequestType.DESTINATION),
        }
        if served:
            self._requests -= served
            if not self._requests:
                self._direction = Direction.IDLE
            return

        # With nothing ahead, turn back and wait until the next tick.
        if not any(
            (r.floor - self._current_floor) * self._direction.value > 0
            for r in self._requests
        ):
            self._direction = Direction(-self._direction.value)
            return

        # Keep moving one floor at a time while requests remain ahead.
        self._current_floor += self._direction.value


# ---------- Multiple-car dispatch ----------


class ElevatorController:
    def __init__(self) -> None:
        # Create three cars; their tuple positions identify them.
        self.elevators = tuple(Elevator() for _ in range(3))

    def request_elevator(self, floor: int, type: RequestType) -> bool:
        # Only valid hall calls need an elevator assignment.
        request = Request(floor, type)
        if not request.is_valid() or type is RequestType.DESTINATION:
            return False
        direction = Direction.UP if type is RequestType.PICKUP_UP else Direction.DOWN

        # Prefer a car approaching the caller in the requested direction.
        on_way = [
            car
            for car in self.elevators
            if car.direction is direction
            and (floor - car.current_floor) * direction.value >= 0
        ]
        idle = [car for car in self.elevators if car.direction is Direction.IDLE]

        # Otherwise use an idle car, then any car; distance ties use car order.
        candidates = on_way or idle or self.elevators
        best = min(candidates, key=lambda car: abs(car.current_floor - floor))
        return best.add_request(request)

    def step(self) -> None:
        # Advance every car once, leaving movement decisions inside the car.
        for car in self.elevators:
            car.step()


# ---------- Runnable example ----------

if __name__ == "__main__":
    controller = ElevatorController()
    controller.request_elevator(2, RequestType.PICKUP_UP)
    controller.step()
    controller.request_elevator(4, RequestType.PICKUP_DOWN)

    # Trace both assigned cars, adding a cabin destination after the first pickup.
    while any(car.requests for car in controller.elevators):
        controller.step()
        for index, car in enumerate(controller.elevators):
            print(f"car {index}: floor {car.current_floor}, {car.direction.name}")
        if (
            controller.elevators[0].current_floor == 2
            and Request(2, RequestType.PICKUP_UP)
            not in controller.elevators[0].requests
        ):
            controller.elevators[0].add_request(Request(6, RequestType.DESTINATION))
