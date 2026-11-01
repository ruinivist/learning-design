# Design patterns in Python

A brief overview of common design patterns, using the same scenarios as [the Java companion](Design%20Patterns%20(%20Java%20).md).

The ideas mostly stay the same: separate responsibilities, compose objects, and keep callers independent of concrete implementations. Python often needs fewer classes to express them. The examples keep the pattern's roles visible and point out simpler alternatives where they help.

Examples run on Python 3.14 with the standard library. Each Python block is self-contained unless marked as a continuation. Assertions show the behavior to check. Services such as email, video conversion, and database connections are local demonstrations, not real integrations.

Python has no Java-style `interface` keyword. A `Protocol` describes the methods an object must provide without requiring inheritance. Type checkers check that contract; annotations do not enforce it at runtime. Use `ABC` and `@abstractmethod` when subclasses must implement steps or inherit shared behavior. Ordinary duck typing needs neither when the contract is already clear.

# Creational patterns

How to create objects without tying the caller to every concrete class.

## Factory pattern

### When?

Client code works with transports but should not need to know whether delivery uses a truck or a ship. A creator defines the delivery workflow and lets subclasses decide which transport to create.

This is the Factory Method pattern. Adding another creator extends the workflow without changing it. The application still needs to choose a creator somewhere; the pattern moves that decision out of the delivery logic.

### What are the elements?

- Product contract: the operations delivery needs.
- Concrete products: truck and ship.
- Creator: the shared workflow and overridable factory method.
- Concrete creators: choose a product.

### Code

```python
from abc import ABC, abstractmethod
from typing import Protocol

# Products share the operation the workflow needs.
class Transport(Protocol):
    def deliver(self) -> str: ...

class Truck:
    def deliver(self) -> str:
        return "Delivering by land in a box."

class Ship:
    def deliver(self) -> str:
        return "Delivering by sea in a container."

# The creator owns the workflow, not the concrete product choice.
class Logistics(ABC):
    @abstractmethod
    def create_transport(self) -> Transport:
        pass

    def plan_delivery(self) -> str:
        return self.create_transport().deliver()

class RoadLogistics(Logistics):
    def create_transport(self) -> Transport:
        return Truck()

class SeaLogistics(Logistics):
    def create_transport(self) -> Transport:
        return Ship()

# Clients can use either creator through the same workflow.
assert RoadLogistics().plan_delivery() == "Delivering by land in a box."
assert SeaLogistics().plan_delivery() == "Delivering by sea in a container."
```

If no shared workflow needs overriding, a factory function or an injected callable may be enough. A function that switches on a product name is a simple factory, not necessarily Factory Method.

## Abstract factory pattern

### When?

When products belong to compatible families. If you choose a modern chair, you also want a modern sofa. A factory packages that choice instead of making each caller track it.

Picture a grid: product types are rows and style variants are columns. A concrete factory creates products from one column.

### What are the elements?

- Abstract products: contracts for chairs and sofas.
- Concrete products: modern and Victorian versions of each.
- Abstract factory: creates each product type.
- Concrete factories: supply one consistent family.
- Client: receives a factory rather than choosing individual products.

### Code

```python
from typing import Protocol

# Each product type has its own contract.
class Chair(Protocol):
    def sit_on(self) -> str: ...

class Sofa(Protocol):
    def lie_on(self) -> str: ...

# Concrete products belong to matching style families.
class ModernChair:
    def sit_on(self) -> str:
        return "Sitting on a modern chair"

class VictorianChair:
    def sit_on(self) -> str:
        return "Sitting on a Victorian chair"

class ModernSofa:
    def lie_on(self) -> str:
        return "Lying on a modern sofa"

class VictorianSofa:
    def lie_on(self) -> str:
        return "Lying on a Victorian sofa"

# A factory bundles the choices for a whole family.
class FurnitureFactory(Protocol):
    def create_chair(self) -> Chair: ...
    def create_sofa(self) -> Sofa: ...

class ModernFactory:
    def create_chair(self) -> Chair:
        return ModernChair()

    def create_sofa(self) -> Sofa:
        return ModernSofa()

class VictorianFactory:
    def create_chair(self) -> Chair:
        return VictorianChair()

    def create_sofa(self) -> Sofa:
        return VictorianSofa()

# The client depends on the family contract.
class Application:
    def __init__(self, factory: FurnitureFactory):
        self.factory = factory

    def create_furniture(self) -> tuple[Chair, Sofa]:
        return self.factory.create_chair(), self.factory.create_sofa()

chair, sofa = Application(ModernFactory()).create_furniture()
assert "modern" in chair.sit_on() and "modern" in sofa.lie_on()
chair, sofa = Application(VictorianFactory()).create_furniture()
assert "Victorian" in chair.sit_on() and "Victorian" in sofa.lie_on()
```

## Builder pattern

### When?

When construction has several meaningful steps, or the same recipe should work with different builders. A director can store recipes such as sports car and SUV.

Java often uses builders to avoid long constructors with many optional parameters. Python's named arguments and defaults usually solve that problem directly: `Car(seats=2, engine="sport", gps=True)`. Keep a builder when the construction process itself deserves an object.

### What are the elements?

- Product: the object being built.
- Builder contract: construction steps.
- Concrete builder: maintains the unfinished product.
- Director: optional named recipes using those steps.

### Code

```python
from dataclasses import dataclass, replace
from typing import Protocol

# Named fields also support direct construction without a builder.
@dataclass
class Car:
    seats: int = 4
    engine: str = "standard"
    gps: bool = False

class Builder(Protocol):
    def reset(self) -> None: ...
    def set_seats(self, seats: int) -> None: ...
    def set_engine(self, engine: str) -> None: ...
    def set_gps(self, enabled: bool) -> None: ...

# Build returns a separate value so later steps cannot mutate past results.
class CarBuilder:
    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.car = Car()

    def set_seats(self, seats: int) -> None:
        if seats <= 0:
            raise ValueError("Seats must be positive")
        self.car.seats = seats

    def set_engine(self, engine: str) -> None:
        self.car.engine = engine

    def set_gps(self, enabled: bool) -> None:
        self.car.gps = enabled

    def build(self) -> Car:
        return replace(self.car)

# The director stores reusable construction recipes.
class Director:
    def make_sports_car(self, builder: Builder) -> None:
        builder.reset()
        builder.set_seats(2)
        builder.set_engine("sport")
        builder.set_gps(True)

    def make_suv(self, builder: Builder) -> None:
        builder.reset()
        builder.set_seats(5)
        builder.set_engine("SUV")
        builder.set_gps(True)

builder = CarBuilder()
Director().make_sports_car(builder)
sports_car = builder.build()
Director().make_suv(builder)
assert sports_car.seats == 2
assert builder.build() == Car(seats=5, engine="SUV", gps=True)
```

### Merged builder

A single builder needs no separate interface or director. Presets can return configured builders. The immutable result here contains only immutable fields.

```python
from dataclasses import dataclass

# The product is independent of the mutable builder.
@dataclass(frozen=True)
class User:
    name: str
    age: int

class UserBuilder:
    def __init__(self, *, age: int = 20):
        self.name = ""
        self.age = age

    def set_name(self, name: str) -> None:
        self.name = name

    def set_age(self, age: int) -> None:
        self.age = age

    def build(self) -> User:
        if not self.name or self.age < 0:
            raise ValueError("A name and nonnegative age are required")
        return User(self.name, self.age)

    @classmethod
    def old_builder(cls):
        return cls(age=50)

    @classmethod
    def young_builder(cls):
        return cls(age=20)

# Presets replace separate builder subclasses.
builder = UserBuilder.old_builder()
builder.set_name("John Doe")
assert builder.build() == User("John Doe", 50)
assert UserBuilder.young_builder().age == 20
```

## Fluent pattern (builder style)

### When?

When chained calls make construction easier to read. Fluent setters return the builder itself. Fluency is an API style, not a requirement of the Builder pattern, and can be used outside builders.

### What are the elements?

- Product and builder: the same roles as before.
- Fluent methods: configure state and return `self`.
- Terminal method: returns the finished result.

### Code

```python
from dataclasses import dataclass
from typing import Self

# The result contains values rather than a reference to its builder.
@dataclass(frozen=True)
class User:
    name: str
    age: int

class UserBuilder:
    def __init__(self):
        self._name = ""
        self._age = 20

    def with_name(self, name: str) -> Self:
        self._name = name
        return self

    def with_age(self, age: int) -> Self:
        self._age = age
        return self

    def build(self) -> User:
        if not self._name or self._age < 0:
            raise ValueError("A name and nonnegative age are required")
        return User(self._name, self._age)

    @classmethod
    def old_builder(cls) -> Self:
        return cls().with_age(50)

    @classmethod
    def young_builder(cls) -> Self:
        return cls().with_age(20)

# Each setter returns the object used by the next call.
user = UserBuilder().with_name("John Doe").with_age(30).build()
assert user == User("John Doe", 30)
assert UserBuilder.old_builder().with_name("Ada").build().age == 50
assert UserBuilder.young_builder().with_name("Lin").build().age == 20
```

For this small product, `User(name="John Doe", age=30)` is enough. The longer example exists to show the fluent API.

## Prototype pattern

### When?

When you want copies of a configured object without reconstructing every field or knowing its concrete class. A registry can store named prototypes for callers to copy.

`copy.copy()` makes a shallow copy: nested objects remain shared. `copy.deepcopy()` recursively copies supported state, preserving internal sharing and cycles. Files, locks, and external connections need explicit treatment rather than blind copying.

### What are the elements?

- Prototype: exposes a copying operation, or supports Python's copy protocol.
- Concrete prototype: owns the copying rules.
- Optional registry: maps names to reusable templates.

### Code

```python
from copy import deepcopy
from dataclasses import dataclass, field

# Each robot owns a separate mutable weapons list.
@dataclass
class Robot:
    x: int
    y: int
    kind: str
    weapons: list[str] = field(default_factory=list)

    def clone(self):
        return deepcopy(self)

# The registry stores templates, not ready-to-share mutable enemies.
registry = {"android": Robot(0, 0, "Android", ["Laser"])}
enemies = [registry["android"].clone() for _ in range(50)]
enemies[0].weapons.append("Shield")
assert enemies[1].weapons == ["Laser"]
assert registry["android"].weapons == ["Laser"]
assert enemies[0] is not enemies[1]
```

`dataclasses.replace()` or `copy.replace()` can make a record with selected fields changed. They do not automatically deep-copy unchanged nested values. Custom classes can implement `__copy__` and `__deepcopy__` when needed.

## Singleton

### When?

When callers need one shared service instance. Shared access and enforced uniqueness are different requirements. Python normally handles shared access with a module-level instance; it does not need a private constructor.

A module is normally initialized once per interpreter under its import name. That does not make its objects shared across processes or make their methods thread-safe. Reloading modules or importing the same file under different names can also break assumptions about uniqueness.

### What are the elements?

- Shared instance: created once in the service module.
- Access point: callers import that instance.
- Dependencies: preferably passed explicitly into consumers.

### Code

```python
# In an application, this definition and instance would live in settings.py.
class Settings:
    def __init__(self):
        self.theme = "dark"

settings = Settings()

# Consumers receive the shared object explicitly and can use test substitutes.
class Application:
    def __init__(self, config: Settings):
        self.config = config

first = Application(settings)
second = Application(settings)
assert first.config is second.config
assert Application(Settings()).config is not settings
```

This shares one instance by convention; it does not prohibit `Settings()`. Python has no enforced private constructor. If lazy initialization is needed, protect the check and creation with a lock rather than relying on the global interpreter lock. Global access hides dependencies and makes tests share state, so explicit dependency injection is often preferable.

## Object pool pattern

### When?

When creating resources is expensive and returning them for reuse is cheaper. Database connections are a common example. Pooling small ordinary Python objects usually adds bookkeeping without a useful saving.

### What are the elements?

- Pool: tracks available and borrowed objects; it need not be a singleton.
- Reusable object: supports cleanup before another caller uses it.
- Acquire and release: transfer ownership temporarily.

### Code

```python
# This connection records queries locally; it does not connect to a database.
class Connection:
    def __init__(self):
        self.queries: list[str] = []

    def query(self, sql: str) -> None:
        self.queries.append(sql)

    def reset(self) -> None:
        self.queries.clear()

# Identity checks reject foreign resources and duplicate returns.
class ConnectionPool:
    def __init__(self):
        self.available: list[Connection] = []
        self.in_use: dict[int, Connection] = {}

    def acquire(self) -> Connection:
        connection = self.available.pop() if self.available else Connection()
        self.in_use[id(connection)] = connection
        return connection

    def release(self, connection: Connection) -> None:
        if self.in_use.get(id(connection)) is not connection:
            raise ValueError("Connection is not borrowed from this pool")
        del self.in_use[id(connection)]
        connection.reset()
        self.available.append(connection)

# Always release borrowed resources, including when work fails.
pool = ConnectionPool()
connection = pool.acquire()
try:
    connection.query("SELECT 1")
finally:
    pool.release(connection)
reused = pool.acquire()
assert reused is connection and reused.queries == []
pool.release(reused)
try:
    pool.release(reused)
except ValueError:
    pass
else:
    raise AssertionError("Duplicate release was accepted")
```

This teaching pool is unbounded and single-threaded. Reset failure discards the resource rather than making it available with dirty state. Production database pools also need limits, timeouts, health checks, shutdown, and transaction cleanup; use the database driver’s pool.

### Generic pool

Python classes are callable, so a pool can accept creation and reset callables directly. No factory interface is required. The modern type-parameter syntax keeps the relationship between factory and resource visible.

```python
from collections.abc import Callable

# The pool does not need to know the resource class.
class GenericPool[T]:
    def __init__(self, create: Callable[[], T], reset: Callable[[T], None]):
        self.create = create
        self.reset = reset
        self.available: list[T] = []
        self.in_use: dict[int, T] = {}

    def acquire(self) -> T:
        item = self.available.pop() if self.available else self.create()
        if id(item) in self.in_use:
            raise ValueError("Factory returned an already borrowed object")
        self.in_use[id(item)] = item
        return item

    def release(self, item: T) -> None:
        if self.in_use.get(id(item)) is not item:
            raise ValueError("Object is not borrowed from this pool")
        del self.in_use[id(item)]
        self.reset(item)
        self.available.append(item)

# The same pool can recycle lists with a different reset operation.
pool = GenericPool(list, list.clear)
item = pool.acquire()
item.append("temporary")
pool.release(item)
assert pool.acquire() is item and item == []
try:
    pool.release([])
except ValueError:
    pass
else:
    raise AssertionError("Foreign resource was accepted")
```

## Summary

| Pattern | Idea |
| --- | --- |
| Factory Method | Let a subclass choose the product used by a shared workflow. |
| Abstract factory | Create compatible families of products. |
| Builder | Separate construction steps from the finished object. |
| Fluent style | Return the builder to chain configuration calls. |
| Prototype | Copy a configured object. |
| Singleton | Provide one shared instance within a defined scope. |
| Object pool | Borrow, clean, and reuse expensive resources. |

# Structural patterns

How to compose objects into larger structures.

## Adapter

### When?

When existing interfaces do not match. For example, a player expects one `play()` method but an older library exposes separate VLC and MP4 methods. An adapter translates between them.

Think of a travel plug adapter: it changes the connection without changing the device. Adapters are common when integrating existing systems; neither interface has to be defective.

### What are the elements?

- Target: the contract the client expects.
- Adaptee: the existing object with a different API.
- Adapter: wraps the adaptee and translates calls.

### Code

```python
from typing import Protocol

# The client expects one playback operation.
class MediaPlayer(Protocol):
    def play(self, file_type: str, filename: str) -> str: ...

class AdvancedAudioPlayer:
    def play_vlc(self, filename: str) -> str:
        return f"VLC: {filename}"

    def play_mp4(self, filename: str) -> str:
        return f"MP4: {filename}"

# The adapter translates the target API into the library's methods.
class MediaAdapter:
    def __init__(self, advanced: AdvancedAudioPlayer):
        self.advanced = advanced

    def play(self, file_type: str, filename: str) -> str:
        if file_type == "vlc":
            return self.advanced.play_vlc(filename)
        if file_type == "mp4":
            return self.advanced.play_mp4(filename)
        raise ValueError(f"Unsupported format: {file_type}")

class AudioPlayer:
    def __init__(self):
        self.adapter = MediaAdapter(AdvancedAudioPlayer())

    def play(self, file_type: str, filename: str) -> str:
        if file_type == "mp3":
            return f"MP3: {filename}"
        return self.adapter.play(file_type, filename)

player: MediaPlayer = AudioPlayer()
assert player.play("mp3", "song.mp3") == "MP3: song.mp3"
assert player.play("vlc", "film.vlc") == "VLC: film.vlc"
assert player.play("mp4", "film.mp4") == "MP4: film.mp4"
```

## Bridge pattern

### When?

When two dimensions should vary independently. Shapes and colors would otherwise produce `RedCircle`, `BlueCircle`, `RedSquare`, and so on. Give each shape a color object instead of defining every combination.

The client-facing dimension is the abstraction. Here clients draw shapes, so a shape holds the color reference. This is composition over inheritance applied to two independent hierarchies.

### What are the elements?

- Abstraction: shape, which delegates part of its work.
- Refined abstractions: circle and square.
- Implementation contract: color.
- Concrete implementations: red and blue.

### Code

```python
from abc import ABC, abstractmethod
from typing import Protocol

# Colors vary independently of shapes.
class Color(Protocol):
    def fill(self) -> str: ...

class Red:
    def fill(self) -> str:
        return "red"

class Blue:
    def fill(self) -> str:
        return "blue"

# Shapes compose a color instead of inheriting a color-specific shape.
class Shape(ABC):
    def __init__(self, color: Color):
        self.color = color

    @abstractmethod
    def draw(self) -> str:
        pass

class Circle(Shape):
    def draw(self) -> str:
        return f"Circle in {self.color.fill()}"

class Square(Shape):
    def draw(self) -> str:
        return f"Square in {self.color.fill()}"

assert Circle(Red()).draw() == "Circle in red"
assert Square(Blue()).draw() == "Square in blue"
```

Bridge separates dimensions by design. Adapter usually connects interfaces that already exist.

## Composite

### When?

When individual objects and groups should support the same operation. In a file tree, a file returns its size; a directory sums its children, including other directories. Clients do not need separate traversal logic for the two kinds of node.

### What are the elements?

- Component contract: the common operation.
- Leaf: handles its own value.
- Composite: holds components and combines their results.

### Code

```python
from dataclasses import dataclass, field
from typing import Protocol

# Leaves and groups expose the same query.
class FileSystemNode(Protocol):
    def get_size(self) -> int: ...

@dataclass
class File:
    size: int

    def get_size(self) -> int:
        return self.size

# Each directory delegates recursively to its children.
@dataclass
class Directory:
    children: list[FileSystemNode] = field(default_factory=list)

    def add(self, node: FileSystemNode) -> None:
        self.children.append(node)

    def get_size(self) -> int:
        return sum(child.get_size() for child in self.children)

root = Directory([File(10), Directory([File(20), File(30)])])
assert root.get_size() == 60
assert Directory().get_size() == 0
```

This is a tree model. It assumes no cycles and counts a shared child once per reference. Real file systems with symbolic links need a traversal policy.

## Decorator

### When?

When behavior should be stacked at runtime. Instead of a subclass for every combination of coffee, milk, and sugar, wrap a coffee in add-ons that expose the same interface.

Like adding clothes to a person, wrappers add behavior without making the original object know every possible addition. Unlike Bridge's separate dimensions, decorators repeatedly wrap the same contract. Order can matter: logging before authentication differs from logging afterward.

### What are the elements?

- Component contract: shared by the base object and wrappers.
- Concrete component: the original behavior.
- Base decorator: delegates to a wrapped component.
- Concrete decorators: add behavior around delegation.

### Code

```python
from typing import Protocol

# Prices use integer units in this example.
class Coffee(Protocol):
    def get_cost(self) -> int: ...
    def get_description(self) -> str: ...

class SimpleCoffee:
    def get_cost(self) -> int:
        return 5

    def get_description(self) -> str:
        return "Coffee"

# Wrappers preserve the component contract and delegate by default.
class CoffeeDecorator:
    def __init__(self, coffee: Coffee):
        self.coffee = coffee

    def get_cost(self) -> int:
        return self.coffee.get_cost()

    def get_description(self) -> str:
        return self.coffee.get_description()

class Milk(CoffeeDecorator):
    def get_cost(self) -> int:
        return super().get_cost() + 2

    def get_description(self) -> str:
        return super().get_description() + ", Milk"

class Sugar(CoffeeDecorator):
    def get_cost(self) -> int:
        return super().get_cost() + 1

    def get_description(self) -> str:
        return super().get_description() + ", Sugar"

coffee = Sugar(Milk(SimpleCoffee()))
assert coffee.get_cost() == 8
assert coffee.get_description() == "Coffee, Milk, Sugar"
assert Milk(Sugar(SimpleCoffee())).get_description() == "Coffee, Sugar, Milk"
```

Python’s `@decorator` syntax transforms a function or class at definition time. It can implement wrapping too, but it is syntax rather than this particular object structure. Neither requires Java-style `final` classes or runtime access restrictions.

## Facade pattern

### When?

When a common task requires coordinating several subsystems in a particular order. A video-conversion facade lets the caller request conversion without choosing codecs, reading data, or mixing audio directly.

### What are the elements?

- Subsystems: lower-level operations that still exist independently.
- Facade: a small entry point that coordinates them.
- Client: uses that entry point for the common task.

### Code

```python
from pathlib import Path

# These local subsystems describe the workflow without processing media.
class CodecFactory:
    def extract(self, filename: str) -> str:
        return Path(filename).suffix.removeprefix(".")

class BitrateReader:
    def read(self, filename: str, codec: str) -> str:
        return f"{filename} decoded from {codec}"

class AudioMixer:
    def fix(self, data: str) -> str:
        return f"{data}; audio mixed"

# The facade chooses and orders the subsystem calls.
class VideoConverterFacade:
    def convert_video(self, filename: str, output_format: str) -> str:
        if output_format not in {"mp4", "ogg"}:
            raise ValueError("Unsupported output format")
        source = CodecFactory().extract(filename)
        data = BitrateReader().read(filename, source)
        mixed = AudioMixer().fix(data)
        return f"{mixed}; encoded as {output_format}"

result = VideoConverterFacade().convert_video("funny_cat.ogg", "mp4")
assert result == "funny_cat.ogg decoded from ogg; audio mixed; encoded as mp4"
```

A facade simplifies access; callers may still use subsystem APIs directly. If no state or dependency injection is needed, a function can serve as the facade.

## Flyweight pattern

### When?

When many objects contain the same large, immutable data. A forest can share tree types while keeping coordinates on individual trees. The saving comes from sharing common state rather than copying it into every tree.

### What are the elements?

- Intrinsic state: shared properties such as species, color, and texture.
- Flyweight: stores that common state.
- Factory: reuses flyweights with the same complete key.
- Extrinsic state: per-object coordinates, passed to shared operations.

Unlike a pool, flyweights can be used by many clients simultaneously; they are not exclusively borrowed.

### Code

```python
from dataclasses import dataclass

# Frozen records hold immutable shared state.
@dataclass(frozen=True)
class TreeType:
    name: str
    color: str
    texture: bytes

    def draw(self, x: int, y: int) -> str:
        return f"{self.color} {self.name} at ({x}, {y})"

class TreeFactory:
    def __init__(self):
        self.types: dict[tuple[str, str, bytes], TreeType] = {}

    def get_tree_type(self, name: str, color: str, texture: bytes) -> TreeType:
        key = (name, color, texture)
        if key not in self.types:
            self.types[key] = TreeType(name, color, texture)
        return self.types[key]

# Only coordinates and a reference are stored per tree.
@dataclass
class Tree:
    x: int
    y: int
    tree_type: TreeType

    def draw(self) -> str:
        return self.tree_type.draw(self.x, self.y)

factory = TreeFactory()
forest = [Tree(x, 0, factory.get_tree_type("Oak", "green", b"oak texture"))
          for x in range(100)]
assert forest[0].tree_type is forest[99].tree_type
assert forest[1].draw() == "green Oak at (1, 0)"
assert factory.get_tree_type("Oak", "red", b"oak texture") is not forest[0].tree_type
```

The factory retains flyweights for its lifetime and is single-threaded here. A real renderer would normally key textures by a stable asset identifier rather than hashing large byte strings repeatedly.

## Proxy

### When?

When access to an object needs mediation: caching, lazy creation, authorization, or remote communication. The proxy presents the same operations as the real service. A decorator focuses on adding behavior; a proxy focuses on controlling access, although their structures can look alike.

### What are the elements?

- Subject contract: operations both objects expose.
- Real subject: performs the work.
- Proxy: decides when to delegate and may cache results.

### Code

```python
from typing import Protocol

# This service returns local data instead of making network requests.
class YouTubeService(Protocol):
    def list_videos(self) -> tuple[str, ...]: ...
    def download_video(self, video_id: str) -> bytes: ...

class RealYouTubeService:
    def list_videos(self) -> tuple[str, ...]:
        return ("intro", "patterns")

    def download_video(self, video_id: str) -> bytes:
        return video_id.encode()

# The service and cached values are created only when requested.
class CachedYouTubeProxy:
    def __init__(self):
        self._service: RealYouTubeService | None = None
        self._list_cache: tuple[str, ...] | None = None
        self._video_cache: dict[str, bytes] = {}

    def _get_service(self) -> RealYouTubeService:
        if self._service is None:
            self._service = RealYouTubeService()
        return self._service

    def list_videos(self) -> tuple[str, ...]:
        if self._list_cache is None:
            self._list_cache = self._get_service().list_videos()
        return self._list_cache

    def download_video(self, video_id: str) -> bytes:
        if video_id not in self._video_cache:
            self._video_cache[video_id] = self._get_service().download_video(video_id)
        return self._video_cache[video_id]

proxy = CachedYouTubeProxy()
assert proxy._service is None
assert proxy.list_videos() == ("intro", "patterns")
first = proxy.download_video("intro")
assert proxy.download_video("intro") is first
```

The cache has no eviction or expiration and assumes one thread. Real services need a policy for stale data, memory limits, and failures. Immutable cached values prevent callers from mutating the shared results.

## Summary

| Pattern | Idea |
| --- | --- |
| Adapter | Translate an incompatible API. |
| Bridge | Let two dimensions vary independently through composition. |
| Composite | Treat leaves and groups through one contract. |
| Decorator | Stack behavior around an object. |
| Facade | Coordinate subsystems behind a small entry point. |
| Flyweight | Share common state between many objects. |
| Proxy | Control access to another object. |

# Behavioral patterns

How objects divide responsibilities and delegate work.

## Chain of responsibility

### When?

When a request passes through a configurable sequence of handlers. HTTP middleware is a common example. Each handler may process the request, forward it, or stop the chain.

There are several ways to build the chain:

- Linked handlers: each points to the next.
- Inheritance: an override handles the request or calls `super()`; the method resolution order fixes the chain.
- Managed sequence: a separate dispatcher walks a list of handlers.

Request flow also varies: stop at the first match, pass through several handlers, or travel down and back up around delegated calls. Event capture and bubbling are related traversal phases, not automatically supplied by every chain.

### What are the elements?

- Handler contract: accepts a request and returns a response.
- Successor: the next handler or dispatcher-managed step.
- Terminal handler: produces a response if nothing stops earlier.

### Code

```python
from dataclasses import dataclass
from typing import Protocol

# Requests and responses carry the data passed along the chain.
@dataclass
class Request:
    url: str
    user: str | None = None

@dataclass
class Response:
    status: int
    body: str

class Handler(Protocol):
    def handle(self, request: Request) -> Response: ...

class Application:
    def handle(self, request: Request) -> Response:
        return Response(200, "Welcome")

# Authentication can stop the chain before application logic runs.
class AuthMiddleware:
    def __init__(self, next_handler: Handler):
        self.next = next_handler

    def handle(self, request: Request) -> Response:
        if request.user is None:
            return Response(401, "Unauthorized")
        return self.next.handle(request)

# Logging surrounds the downstream call and observes its result.
class LoggerMiddleware:
    def __init__(self, next_handler: Handler):
        self.next = next_handler
        self.events: list[str] = []

    def handle(self, request: Request) -> Response:
        self.events.append(f"Started {request.url}")
        response = self.next.handle(request)
        self.events.append(f"Finished {response.status}")
        return response

chain = LoggerMiddleware(AuthMiddleware(Application()))
assert chain.handle(Request("/private")).status == 401
assert chain.events == ["Started /private", "Finished 401"]
assert chain.handle(Request("/private", "Ada")).status == 200
```

### Event bubbling

A child handles an event and then forwards it to its parent unless propagation stops. This example demonstrates bubbling only. A capture phase would first walk from the root toward the target.

```python
from collections.abc import Callable
from dataclasses import dataclass

# An event carries its propagation state through the tree.
@dataclass
class Event:
    kind: str
    propagation_stopped: bool = False

    def stop_propagation(self) -> None:
        self.propagation_stopped = True

class Component:
    def __init__(self, parent=None):
        self.parent = parent
        self.listeners: dict[str, Callable[[Event], None]] = {}

    def handle_event(self, event: Event) -> None:
        listener = self.listeners.get(event.kind)
        if listener is not None:
            listener(event)
        if not event.propagation_stopped and self.parent is not None:
            self.parent.handle_event(event)

class Button(Component):
    pass

class Div(Component):
    pass

# Parent references form the chain independently of class inheritance.
seen = []
container = Div()
button = Button(container)
button.listeners["click"] = lambda event: seen.append("button")
container.listeners["click"] = lambda event: seen.append("container")
button.handle_event(Event("click"))
assert seen == ["button", "container"]
seen.clear()
button.listeners["click"] = lambda event: event.stop_propagation()
button.handle_event(Event("click"))
assert seen == []
```

## Command pattern

### When?

When the action should be separate from whoever triggers it. A button knows only how to execute its command. Commands can also carry the state needed for undo or capture arguments for delayed execution.

A bound method or callable is enough for a one-shot action. An object earns its place when the action needs history, metadata, or several operations such as `execute()` and `undo()`.

### What are the elements?

- Receiver: knows how to perform the work.
- Command: binds an action and its receiver.
- Invoker: triggers a command without knowing the business logic.
- Optional history or queue: retains commands for later use.

### Code

```python
from typing import Protocol

# The receiver owns the state changed by commands.
class Light:
    def __init__(self):
        self.is_on = False

    def turn_on(self) -> None:
        self.is_on = True

    def turn_off(self) -> None:
        self.is_on = False

class Command(Protocol):
    def execute(self) -> None: ...
    def undo(self) -> None: ...

# Each execution records the actual previous state for undo.
class LightOnCommand:
    def __init__(self, light: Light):
        self.light = light
        self.history: list[bool] = []

    def execute(self) -> None:
        self.history.append(self.light.is_on)
        self.light.turn_on()

    def undo(self) -> None:
        if self.history:
            self.light.is_on = self.history.pop()

class LightOffCommand(LightOnCommand):
    def execute(self) -> None:
        self.history.append(self.light.is_on)
        self.light.turn_off()

# The invoker only knows the command contract.
class RemoteControl:
    def __init__(self, command: Command):
        self.command = command

    def press_button(self) -> None:
        self.command.execute()

light = Light()
command = LightOnCommand(light)
remote = RemoteControl(command)
remote.press_button()
remote.press_button()
command.undo()
assert light.is_on
command.undo()
assert not light.is_on
remote.command = LightOffCommand(light)
remote.press_button()
assert not light.is_on
```

### Queued commands

Capture the service and arguments now, execute later. This is an in-memory queue processed synchronously, not a durable background worker. A failed command remains at the head; retrying a side effect needs an idempotency policy.

```python
from collections import deque
from dataclasses import dataclass, field
from typing import Protocol

# This local service records delivery instead of sending email.
@dataclass
class EmailService:
    sent: list[tuple[str, str]] = field(default_factory=list)

    def send(self, address: str, body: str) -> None:
        self.sent.append((address, body))

class Command(Protocol):
    def execute(self) -> None: ...

@dataclass
class SendEmailCommand:
    service: EmailService
    address: str
    body: str

    def execute(self) -> None:
        self.service.send(self.address, self.body)

# Remove a job only after it completes successfully.
class JobQueue:
    def __init__(self):
        self.jobs: deque[Command] = deque()

    def add_job(self, command: Command) -> None:
        self.jobs.append(command)

    def process_pending_jobs(self) -> None:
        while self.jobs:
            self.jobs[0].execute()
            self.jobs.popleft()

service = EmailService()
queue = JobQueue()
queue.add_job(SendEmailCommand(service, "boss@example.com", "Report attached"))
queue.add_job(SendEmailCommand(service, "client@example.com", "Welcome!"))
assert service.sent == []
queue.process_pending_jobs()
assert len(service.sent) == 2 and not queue.jobs
queue.process_pending_jobs()
assert len(service.sent) == 2
```

## Iterator

### When?

When callers should traverse different collection types through the same API. Python builds this pattern into `for`, `iter()`, and `next()`.

An iterable supplies `__iter__()`. An iterator supplies `__next__()` and returns itself from `__iter__()`. Exhaustion raises `StopIteration`; there is no separate `has_next()` call. A generator implements the iterator machinery for you.

### What are the elements?

- Iterable: can provide an iterator.
- Iterator: tracks traversal progress.
- Collection: owns the data and decides how traversal works.

### Code

```python
from collections.abc import Iterator

# Every iteration creates a fresh generator with independent progress.
class BookList:
    def __init__(self, books: list[str]):
        self.books = books

    def __iter__(self) -> Iterator[str]:
        yield from self.books

library = BookList(["Python", "Design"])
assert list(library) == ["Python", "Design"]
first = iter(library)
second = iter(library)
assert next(first) == next(second) == "Python"
assert next(first) == "Design"
try:
    next(first)
except StopIteration:
    pass
else:
    raise AssertionError("Iterator did not stop")
assert list(BookList([])) == []
```

Use an explicit iterator class when traversal state is complicated enough to deserve one. Returning `iter(self.books)` is sufficient for this collection; the generator shows how to define traversal without Java-style iterator interfaces.

## Mediator pattern

### When?

When several components directly coordinating with each other would create tangled dependencies. An authentication dialog can own the rules connecting a checkbox, password field, and login button.

Think of replacing a mesh of peer-to-peer connections with a hub. The hub need not be global: a mediator normally belongs to a particular dialog or workflow.

### What are the elements?

- Mediator contract: receives component events.
- Concrete mediator: coordinates the components.
- Components: report events without knowing each other's behavior.

### Code

```python
from typing import Protocol

# Components report events through a shared contract.
class Mediator(Protocol):
    def notify(self, sender: object, event: str) -> None: ...

class Component:
    def __init__(self, mediator: Mediator):
        self.mediator = mediator

class Checkbox(Component):
    def check(self) -> None:
        self.mediator.notify(self, "check")

class Textbox(Component):
    def __init__(self, mediator: Mediator):
        super().__init__(mediator)
        self.text = ""
        self.visible = False

class Button(Component):
    def click(self) -> None:
        self.mediator.notify(self, "click")

# The dialog owns both wiring and cross-component rules.
class AuthenticationDialog:
    def __init__(self):
        self.checkbox = Checkbox(self)
        self.password = Textbox(self)
        self.login = Button(self)
        self.error = ""

    def notify(self, sender: object, event: str) -> None:
        if sender is self.checkbox and event == "check":
            self.password.visible = not self.password.visible
        elif sender is self.login and event == "click":
            self.error = "Password missing" if not self.password.text else ""

# Validation here demonstrates coordination, not authentication.
dialog = AuthenticationDialog()
dialog.checkbox.check()
assert dialog.password.visible
dialog.login.click()
assert dialog.error == "Password missing"
dialog.password.text = "example"
dialog.login.click()
assert dialog.error == ""
```

Keep the mediator focused on one interaction. Moving all application logic into one central object merely relocates the coupling.

## Memento pattern

### When?

When an object needs snapshots for undo or rollback. The object that owns the state should decide how to save and restore it, rather than requiring a history manager to understand every field.

Python uses conventions rather than Java's enforced private inner classes. An underscore marks implementation details; it is not an access barrier. A frozen dataclass prevents ordinary field assignment but does not recursively freeze nested mutable values.

### What are the elements?

- Originator: creates and restores snapshots.
- Memento: stores saved state, preferably immutable.
- Caretaker: stores snapshots and returns them without interpreting them.

### Code

```python
from dataclasses import dataclass

# Immutable fields make this snapshot a value independent of later edits.
@dataclass(frozen=True)
class _EditorMemento:
    content: str
    cursor: int

class TextEditor:
    def __init__(self):
        self.content = ""
        self.cursor = 0

    def save(self) -> _EditorMemento:
        return _EditorMemento(self.content, self.cursor)

    def restore(self, snapshot: _EditorMemento) -> None:
        if not isinstance(snapshot, _EditorMemento):
            raise TypeError("Unknown snapshot type")
        self.content = snapshot.content
        self.cursor = snapshot.cursor

# History stores snapshots without inspecting their fields.
class History:
    def __init__(self, editor: TextEditor):
        self.editor = editor
        self.snapshots: list[_EditorMemento] = []

    def backup(self) -> None:
        self.snapshots.append(self.editor.save())

    def undo(self) -> None:
        if self.snapshots:
            self.editor.restore(self.snapshots.pop())

editor = TextEditor()
history = History(editor)
editor.content, editor.cursor = "Version 1", 3
history.backup()
editor.content, editor.cursor = "Version 2", 5
history.backup()
editor.content = "Version 3 (mistake)"
history.undo()
assert (editor.content, editor.cursor) == ("Version 2", 5)
history.undo()
assert (editor.content, editor.cursor) == ("Version 1", 3)
history.undo()
assert editor.content == "Version 1"
```

Snapshots here can be restored into any `TextEditor`. If snapshots must belong to one document, include and validate document identity. Mutable state requires copying or a persistent immutable representation.

## Observer

### When?

When several independent components react to one source of events. A channel should notify subscribers without knowing how each updates a UI, sends a notification, or records analytics. Subscribers avoid polling for changes.

In a push model, notifications contain the changed data. In a pull model, notifications identify the source and observers query what they need. The example pushes a video title.

### What are the elements?

- Observer contract: receives notifications.
- Concrete observers: carry out individual reactions.
- Subject: owns subscriptions and broadcasts events.

### Code

```python
from typing import Protocol

# Subscribers share a notification contract, not an implementation.
class Observer(Protocol):
    def update(self, title: str) -> None: ...

class Subject:
    def __init__(self):
        self.observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        if not any(item is observer for item in self.observers):
            self.observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self.observers = [item for item in self.observers if item is not observer]

    def notify(self, title: str) -> None:
        for observer in tuple(self.observers):
            observer.update(title)

class YouTubeChannel(Subject):
    def upload_video(self, title: str) -> None:
        self.notify(title)

# Each observer keeps its own reaction and state.
class User:
    def __init__(self, name: str):
        self.name = name
        self.notifications: list[str] = []

    def update(self, title: str) -> None:
        self.notifications.append(title)

class Analytics:
    def __init__(self):
        self.upload_count = 0

    def update(self, title: str) -> None:
        self.upload_count += 1

channel = YouTubeChannel()
alice, bob, stats = User("Alice"), User("Bob"), Analytics()
channel.attach(alice)
channel.attach(alice)
channel.attach(stats)
channel.upload_video("Design Patterns 101")
assert alice.notifications == ["Design Patterns 101"]
assert bob.notifications == [] and stats.upload_count == 1
channel.detach(alice)
channel.upload_video("Part 2")
assert len(alice.notifications) == 1 and stats.upload_count == 2
```

Callbacks can replace observer objects for small subscriptions. This example notifies synchronously in subscription order. Membership is snapshotted for each broadcast; subscription changes affect the next broadcast. An exception stops delivery and propagates. The subject holds strong references until detachment.

## State pattern

### When?

When behavior depends on current state and repeated conditionals obscure the rules. The context delegates to a state object, which can also trigger a transition. This is an object-based representation of a state machine.

The audio-player example is small enough for an enum and a conditional; separate classes become more useful as states gain behavior.

### What are the elements?

- Context: owns the current state and delegates actions.
- State contract: actions available in every state.
- Concrete states: implement behavior and transitions, often holding the context.

### Code

```python
from typing import Protocol

# The context delegates instead of branching on its state.
class State(Protocol):
    def click_play(self) -> str: ...

class AudioPlayer:
    def __init__(self):
        self.state: State = StoppedState(self)

    def change_state(self, state: State) -> None:
        self.state = state

    def click_play(self) -> str:
        return self.state.click_play()

# Each state owns the action and its next transition.
class StoppedState:
    def __init__(self, player: AudioPlayer):
        self.player = player

    def click_play(self) -> str:
        self.player.change_state(PlayingState(self.player))
        return "Starting music"

class PlayingState:
    def __init__(self, player: AudioPlayer):
        self.player = player

    def click_play(self) -> str:
        self.player.change_state(PausedState(self.player))
        return "Pausing music"

class PausedState:
    def __init__(self, player: AudioPlayer):
        self.player = player

    def click_play(self) -> str:
        self.player.change_state(PlayingState(self.player))
        return "Resuming music"

player = AudioPlayer()
assert player.click_play() == "Starting music"
assert player.click_play() == "Pausing music"
assert isinstance(player.state, PausedState)
assert player.click_play() == "Resuming music"
assert isinstance(player.state, PlayingState)
```

## Strategy

### When?

When several interchangeable algorithms perform the same task. A navigation app can delegate route planning to a road or walking strategy and replace it at runtime.

Strategy varies behavior through composition. Template Method varies steps through inheritance. Both can use dynamic method dispatch in Python; inheritance does not imply static dispatch.

### What are the elements?

- Strategy contract: a common operation.
- Concrete strategies: alternative algorithms.
- Context: holds the selected strategy and delegates to it.

### Code

```python
from typing import Protocol

# Strategies expose one interchangeable operation.
class RouteStrategy(Protocol):
    def build_route(self, start: str, end: str) -> str: ...

class RoadStrategy:
    def build_route(self, start: str, end: str) -> str:
        return f"Drive from {start} to {end}: 15 minutes"

class WalkingStrategy:
    def build_route(self, start: str, end: str) -> str:
        return f"Walk from {start} to {end}: 40 minutes via park"

# The context never chooses or implements a routing algorithm.
class NavigationApp:
    def __init__(self, strategy: RouteStrategy):
        self.strategy = strategy

    def build_route(self, start: str, end: str) -> str:
        return self.strategy.build_route(start, end)

app = NavigationApp(RoadStrategy())
assert app.build_route("Home", "Work").startswith("Drive")
app.strategy = WalkingStrategy()
assert app.build_route("Home", "Work").startswith("Walk")
```

These routes are fixed demonstration results. When a strategy has no extra state or methods, pass a function with the required signature instead of wrapping it in a class. The context then calls `self.strategy(start, end)`.

## Template method

### When?

When an algorithm has a stable sequence but some steps differ. A data miner reads input, parses it, analyzes results, and optionally reports them. Subclasses customize individual steps while inheriting that workflow.

The defining feature is the shared algorithm skeleton, not inheritance alone. Python's `@final` tells type checkers that a method should not be overridden; it does not block overrides at runtime.

### What are the elements?

- Abstract base class: defines the workflow and required steps.
- Concrete subclasses: implement variable steps.
- Hook: optional override with a default implementation.

### Code

```python
from abc import ABC, abstractmethod
import csv
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import final

# The shared workflow closes its file even if extraction or parsing fails.
class DataMiner(ABC):
    @final
    def mine(self, path: Path) -> int:
        with path.open(encoding="utf-8") as file:
            raw = self.extract_data(file)
            data = self.parse_data(raw)
            count = self.analyze(data)
            self.send_report(count)
            return count

    def extract_data(self, file) -> str:
        return file.read()

    @abstractmethod
    def parse_data(self, raw: str) -> list[dict[str, str]]:
        pass

    def analyze(self, data: list[dict[str, str]]) -> int:
        return len(data)

    def send_report(self, count: int) -> None:
        pass

# Subclasses customize parsing and may override the reporting hook.
class JSONMiner(DataMiner):
    def parse_data(self, raw: str) -> list[dict[str, str]]:
        data = json.loads(raw)
        if not isinstance(data, list) or not all(
            isinstance(row, dict) and all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in row.items()
            ) for row in data
        ):
            raise ValueError("Expected a list of string-valued records")
        return data

class CSVMiner(DataMiner):
    def __init__(self):
        self.reports: list[int] = []

    def parse_data(self, raw: str) -> list[dict[str, str]]:
        return list(csv.DictReader(io.StringIO(raw)))

    def send_report(self, count: int) -> None:
        self.reports.append(count)

# Temporary files exercise the real shared reading and parsing workflow.
with TemporaryDirectory() as directory:
    json_path = Path(directory) / "records.json"
    csv_path = Path(directory) / "records.csv"
    json_path.write_text('[{"name": "Ada"}]', encoding="utf-8")
    csv_path.write_text("name\nAda\nLin\n", encoding="utf-8")
    assert JSONMiner().mine(json_path) == 1
    miner = CSVMiner()
    assert miner.mine(csv_path) == 2
    assert miner.reports == [2]
```

JSON replaces the Java note’s placeholder PDF miner so both formats can be parsed with the standard library. Real PDF extraction requires a suitable library. The template still allows extraction to be overridden when formats require different reading behavior.

## Visitor pattern

### When?

When new operations must be added across a stable set of element types without editing those types for every operation. Each element accepts a visitor and calls its own type-specific visitor method. The visitor contains the operation.

This is double dispatch: the element's `accept()` chooses the method for its own type, then the concrete visitor determines the behavior. No tree is required; visitors work on flat collections too. Tree traversal is a separate responsibility.

### What are the elements?

- Visitor contract: one method per concrete element type.
- Concrete visitors: one class per operation.
- Element contract: accepts a visitor.
- Concrete elements: route the visitor to the matching method.

### Code

```python
from dataclasses import dataclass
from typing import Protocol

# Each element routes to an explicitly named method; Python has no overload dispatch here.
class Visitor[R](Protocol):
    def visit_dot(self, dot: "Dot") -> R: ...
    def visit_rectangle(self, rectangle: "Rectangle") -> R: ...

class Shape(Protocol):
    def accept[R](self, visitor: Visitor[R]) -> R: ...

@dataclass
class Dot:
    x: int
    y: int

    def accept[R](self, visitor: Visitor[R]) -> R:
        return visitor.visit_dot(self)

@dataclass
class Rectangle:
    width: int
    height: int

    def accept[R](self, visitor: Visitor[R]) -> R:
        return visitor.visit_rectangle(self)

# Operations live in visitors rather than inside every element.
class XMLExportVisitor:
    def visit_dot(self, dot: Dot) -> str:
        return f'<dot x="{dot.x}" y="{dot.y}" />'

    def visit_rectangle(self, rectangle: Rectangle) -> str:
        return f'<rect width="{rectangle.width}" height="{rectangle.height}" />'

class AreaCalculatorVisitor:
    def visit_dot(self, dot: Dot) -> int:
        return 0

    def visit_rectangle(self, rectangle: Rectangle) -> int:
        return rectangle.width * rectangle.height

shapes: list[Shape] = [Dot(1, 2), Rectangle(3, 4)]
assert [shape.accept(AreaCalculatorVisitor()) for shape in shapes] == [0, 12]
assert shapes[0].accept(XMLExportVisitor()) == '<dot x="1" y="2" />'
assert shapes[1].accept(XMLExportVisitor()) == '<rect width="3" height="4" />'
```

Adding an operation means adding a visitor. Adding an element type means updating the visitor contract and existing visitors. `functools.singledispatch`, pattern matching, or ordinary methods may be shorter when the classic visitor structure is unnecessary. The XML example uses numeric fields; arbitrary text would need XML escaping or an XML library.

## Summary

| Pattern | Idea |
| --- | --- |
| Chain of responsibility | Pass a request through handlers that may forward or stop it. |
| Command | Capture an action for execution, history, or undo. |
| Iterator | Traverse through a common protocol without exposing storage details. |
| Mediator | Coordinate related components through one local hub. |
| Memento | Let an object save and restore its own state. |
| Observer | Notify subscribers when events occur. |
| State | Delegate behavior to the current state object. |
| Strategy | Swap algorithms through composition. |
| Template Method | Share a workflow and override selected steps. |
| Visitor | Add operations across a stable set of element types. |

# Just enough UML to get started

UML visibility symbols describe a design, but Python does not enforce Java's access rules:

- `+` means public. Python names without a leading underscore usually belong to the public API.
- `-` means private. A leading underscore marks an internal detail by convention. Double-leading underscores trigger name mangling to avoid accidental subclass collisions, not to enforce secrecy.
- `#` means protected. Python has no enforced protected access; an underscore commonly marks members intended for internal or subclass use.
- `~` means package visibility. Python has no equivalent access restriction. Package structure and explicit exports communicate intent.

Composition, inheritance, and dependencies still mean the same things. A protocol can describe a contract even when concrete classes do not explicitly inherit from it.

# Problems
