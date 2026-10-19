# Entity vs value

Entity: has a lifecycle, two instances with identical fields are different things.
Value: defined by its fields, two instances with the same fields are interchangeable.

Test: swap the object for a copy with identical fields. Does anything break?

Two empty bike bays are not the same bay, so `Spot` is an entity. Two tickets with the same
fields describe the same stay, so `Ticket` is a value.

## The three cases

An id field gives an entity two possible spellings. Equality can be the object, or the id.

```python
@dataclass(slots=True, kw_only=True, eq=False)                  # 1. reference identity
class Spot:
    id: str
    size: SpotSize
    occupied: Vehicle | None = None

@dataclass(slots=True, kw_only=True, eq=True, unsafe_hash=True) # 2. key identity
class Spot:
    id: str
    size: SpotSize = field(compare=False)
    occupied: Vehicle | None = field(default=None, compare=False)

@dataclass(slots=True, kw_only=True, frozen=True)              # 3. value
class Ticket:
    id: str
    spot_id: str
    spot_size: SpotSize
    entry_time: datetime
```

`unsafe_hash` is only unsafe when a hashed field mutates. Here the hash covers `id` alone and
the id never changes, which is the case the flag is for.

Case 3 on a mutable entity fails because of the mutation, not the id: `s1_empty == s1_occupied`
is False, so the same bay at two moments reads as two bays. Identity must survive state
changing.

## Which one to use

| | equality is | use when |
|--|---|---|
| 1. reference identity | the object | one instance per thing, in process, no store |
| 2. key identity | the id | the same thing can be materialised twice |
| 3. value | all fields | no lifecycle, interchangeable, immutable |

The parking lot uses case 1 for `Spot`: `Floor._spots` builds every bay once and nothing
reloads one, so reference and key identity coincide and case 1 is cheaper. Back it with a
database and two queries return two unequal objects for bay `s1`, which is the Hibernate
problem and what case 2 fixes. Case 2's own trap: unsaved entities all have `id = None` and
so all compare equal.

## Equality-dependent operations

| | 1. reference | 2. key | 3. value |
|--|---|---|---|
| `a == b` | same object | same id | same fields |
| hashed by | memory address | the id | all fields |
| `list.remove(x)` | the one you passed | first with that id | first state-equal one |
| as a dict key | one key per instance | one key per id | one key per field tuple |
| survives a reload | no | yes | not applicable |
| `==` as "this is my object" | same as `is` | always true, asserts nothing | weaker than `is`, works |

Row 3 under case 3 is the observer bug. `Subject.detach` calls
`self._observers.remove(observer)`. With a plain class it removes the one you passed. Convert

<!-- Reconstruction gap: original lines 70–83 are not visible in the supplied screenshots. The preceding sentence continues in this gap. -->

## Reference strategy

<!-- Reconstruction gap: original lines 85–90 are not visible in the supplied screenshots, including the table header for the following rows. -->

| id plus store | at resolve time | yes | yes | only via the store |
| value snapshot | no, frozen | yes | no | nobody |

Default to the live reference. Use an id only when it crosses a boundary: serialized,
outlives the transaction lock, or you do not own its lifetime. `Ticket.spot_id` clears
three of those.

`Ticket.spot_size` is a snapshot copied at park time, which keeps pricing at
`price(ticket, exit_time)` with no lot reference in the money path. Per field, ask whether it
needs to be current or correct as of then.

An id on an entity is its own identity. An id on a value is a foreign key to an entity
elsewhere: `Ticket.id` names the stay in the lot's registry, not the ticket object.

## Key lookup vs object identity

```python
# claim: correct, the pop IS the test
ticket = self._active.pop(id, None)
if ticket is None: raise TicketNotFound(id)

# release: wrong, pop mutates before the check decides
if self._settling.pop(ticket.id, None) is not ticket: raise TicketNotFound(ticket.id)
```

The second drops a real stay when the check fails. Its bay stays occupied and it never
reaches the reconciliation list.

| question | about | atomic in the container? |
|---|---|---|
| is id `T-5` present | the key | yes |
| is this the object stored under `T-5` | the payload | no: get, compare, then delete |

An atomic remove-and-return works as the check only when the check is about the key. The two
questions split because a value object is indexed by one of its own fields. Key an entity by
itself and they collapse into one.

Use `is`, not `==`. Under case 2 you looked the object up by its id, so key equality against
it is true by construction. Under case 3 `==` works but only catches a copy whose fields
differ, and it stops covering any field later marked `compare=False`.

Databases fold the payload check back into a key shaped operation:

```sql
DELETE FROM stays WHERE id = ? AND version = ?
```

Atomic again, row count is the verdict. That is optimistic concurrency control. The version
column exists because "the row with this id" and "the row I read" are different claims.

## Concurrency

Immutable values are free to share: no lock, no copy. Both entity cases have mutable state
and so carry a lock scope. `Ticket` being frozen is what lets it leave the critical section
and come back hours later, so the money path runs outside the lot's mutex while a card
authorizes.

## Heuristics

Mutable plus full value equality is always wrong. Pick case 1 or case 2.

Case 2 needs the id immutable for the object's lifetime, or the hash changes in a dict.

A value carrying an `id` is usually a snapshot of an entity. Say so, or the next reader tries
to dereference it.

Hand-writing `__eq__` means choosing case 2. Check that unsaved instances cannot all collide
on a null id.

Indexing a value by its own field: write down which of the two questions each lookup asks.
