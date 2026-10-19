# vending machine

## problem

Model a vending machine with the State pattern, one class per state, each handling every event.

- states: idle, has money, dispensing, out of service
- events: insert coin/note, select product, cancel, dispense done, restock
- products live in slots with a price and a count
- change uses the fewest coins, from coins the machine actually holds
- cancel refunds everything inserted
- all money is `Decimal`

Trap: if change can't be made, refuse the sale before dispensing, never after.
Greedy fails on some coin sets (1/3/4, amount 6).

## high level idea

```
                ┌──────────────────────────────┐
   client ────▶ │ VendingMachine (context)     │
                │ - slots: id → product, count │
                │ - coins: denom → count       │
                │ - balance: Decimal           │
                │ - state ─────────────────────┼──┐
                └──────────────────────────────┘  │ has-a (current state)
                                                  ▼
                              ┌──────────────────────────────┐
                              │ State (abstract)             │
                              │ insert(machine, money)       │
                              │ select(machine, slot)        │
                              │ cancel(machine)              │
                              │ dispensed(machine)           │
                              │ restock(machine, ...)        │
                              └──────────────┬───────────────┘
                     ┌────────────┬──────────┴───┬──────────────┐
                     ▼            ▼              ▼              ▼
                ┌────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────┐
                │ Idle   │  │ HasMoney │  │ Dispensing │  │ OutOfService │
                └────────┘  └──────────┘  └────────────┘  └──────────────┘
```

## transitions

```
                                       insert (balance grows)
                                            ┌───────┐
                                            │       ▼
   ┌────────────────┐  insert    ┌────────────────────────┐
   │     Idle       │ ─────────▶ │       HasMoney         │
   │                │ ◀───────── │                        │
   └────────────────┘  cancel    └────────────────────────┘
       │      ▲        (refund)            │ select, stock ok
       │      │                            │ AND change makeable
       │      │ dispensed                  ▼
       │      │ (give change)    ┌────────────────────┐
       │      └───────────────── │    Dispensing      │
       │                         └────────────────────┘
       │ last slot empty / fault
       ▼
   ┌────────────────┐
   │ OutOfService   │ ── restock ──▶ Idle
   └────────────────┘

   select in HasMoney with sold out or no change: rejected, stay in HasMoney
   select in Idle: rejected, state unchanged
   any other event in the wrong state (e.g. restock while Dispensing): raise
```

## followups

Change making: DP over coins actually held (min coins, bounded counts), not greedy.
Run it at select time, before entering Dispensing, so refusal is clean.
don't make the methods abstract else you would need to define them in each state for no reason.

is it possible to fix it compile time? Well if you look at my fsm.py, it has a definite set of "events"
so a full mapping was defined in the transition, for vending machine it's all at runtime like what amt
entered, what drink selected etc. you can't type check those at compile time so it's fine to do it at runtime

# key elems

make a base fast state with all the methods that throw.
Any that inherit will override only the needed ones. This way you solve the fat interface in a runtime way.

## sketch

```
Machine
  slots, coins, balance, state = Idle

  insert(c) / select(s) / cancel / dispensed / restock   → state.<same>(self, ...)

  accept(c)             coins[c]++, balance += c
  plan_change(s)        → change | fail        (sold out, short, can't make change)
  commit_sale(s, chg)   stock--, coins -= chg, balance = 0
  refund_all()          ...
  add_stock(s, n)       ...
  has_stock()           ...

State                   every event → raise Illegal

  Idle          insert         accept                       → HasMoney
                restock        add_stock

  HasMoney      insert         accept
                select         plan_change   (fail: reject, stay)
                               commit_sale                  → Dispensing
                cancel         refund_all                   → Idle

  Dispensing    dispensed                                   → has_stock ? Idle : OutOfService

  OutOfService  restock        add_stock                    → Idle
```

machine owns all the data and the helpers, states own only "which helpers, then where to"

## some notes while implementing

an error class should be defined based on how parent handles it differently, if there is no difference
at that level then it must not be a separate exception
If you wanna put info, do it in attributes, not my expanding types.

for example: an edge not existing is an illegal action
a sale refused due to sold out or no change should be a different exception as the called would need to handle
it differently

## guidance on exception vs enum vs bool returns

**name test**
if you name something "doxyz" and it' can't doxyz then it must raise.

If this xyz is an API, then as part of good api design any state mutators should also have a can prefix version
if the "not" can is common and normal part of the flow/
so then so that callers can guard based on check instead of forcing them to handle exceptions in the usual path.
This does not in any way remove the need fo rname test as this si just advice for callers, for correctness the
func itself should raise

in case the asnwer can be "Nothing" use an Optional instead of raising. This is generally for "queries"
as opposed to commands.
Queries are of form "askxyz" as opposed to "doxyz", queries generally should not raise and unless a valid response
outside of we KNOT it's nothing or we KNOW it's some val x. Unknown cases should be fine for exceptions.

bool or erro code returns are generally to be avoided for commands since easy to miss rvs.
unless language forces it like go does.

**should exceptions have error suffix**? if they are a logic flaw yes
for example "StopIteration" is the normal end of iteration, not a logic error
in my case IllegalAction if reached is a logical error so must be suffixed as such.

**error vs exception**?
this was a distinction in java.
Throwable -> Error or Exception ( both these inherit from throwable )
an Error is serious JVM problem that you don't expect to catch or handle in ur application code
Exceptions are the ones you catch and handle

for python, "error" is just a name suffix, usage as described above. the base "type" is always Exception

## differentiate state passthrough funcs from the rest

I was thinking of this, but it is not a good idea to ler the caller know the internals of machine, as in
that the state object handles the state transition ( to a caller, machine should just be a blackbox )

