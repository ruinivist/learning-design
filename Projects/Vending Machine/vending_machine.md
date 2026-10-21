# Vending machine design

`Machine` owns inventory, stored cash, the current payment, and its `State` in
[vending_machine.py](vending_machine.py). States decide which actions are legal
and delegate inventory and payment operations to the machine.

![Vending machine UML class diagram](vending-machine-uml.svg)

For recall, use the [incremental breakdown](vending-machine-breakdown.md).

## Reading the UML

1. Start with `Machine`. Its public methods delegate to `_state`; `select()` also drives internal dispensing before returning. `_items`, `_coins`, and `_inserted` hold the data those operations change.
2. Follow inventory ownership. The constructor copies every `Item` and the supplied coin mapping, so callers cannot change machine inventory through their original objects. Each item has a name, positive `price_cents`, and nonnegative stock.
3. Separate the two cash counters. `_coins` holds stored cash; `_inserted` holds refundable payment. `balance_cents` sums only `_inserted`. All denominations, prices, and balances are integer cents.
4. Follow `State` to `Idle`, `HasMoney`, `Dispensing`, and `SoldOut`. The concrete base rejects every event; subclasses override only legal events. States choose transitions after machine operations succeed.
5. Follow a purchase through `HasMoney.select()` to `Machine._sell()`. The machine plans change and commits the sale, then the state becomes `Dispensing`. `Machine.select()` invokes its `dispense()` handler, which installs `Idle` or `SoldOut` before change returns to the caller.

## Happy path

1. Construct a machine with `Item("tea", 140, 2)` and stored coins `{50: 1, 20: 3}`. Stock is available, so the initial state is `Idle`.
2. Caller invokes `insert(200)`. `Idle.insert()` calls `_accept(200)`, which adds the coin only to `_inserted`, then installs `HasMoney`. The balance is 200 cents.
3. Caller invokes `select("tea")`. `HasMoney.select()` calls `_sell("tea")`, which combines stored and inserted coins in a temporary `available` counter and checks the item, stock, and balance.
4. The nested `make_change(60)` finds three 20-cent coins. Taking the 50-cent coin first would leave an unmakeable 10 cents.
5. `_sell()` reduces tea stock to one, sets `_coins = available - change`, and clears `_inserted`. Stored cash is now `{50: 1, 200: 1}` and the balance is zero.
6. `HasMoney.select()` installs `Dispensing` and returns `Counter({20: 3})` to `Machine.select()`.
7. `Machine.select()` calls `_state.dispense(self)`. `Dispensing.dispense()` completes the simulated delivery by checking `_has_stock()` and installing `Idle` because one tea remains. `Machine.select()` then returns the change to the caller. Selling the last item would instead leave the machine in `SoldOut`.

## Design choices

- Keep money in integer cents. Supported coins are 5, 10, 20, 50, 100, and 200 cents; prices must be positive integers. Reject fractional amounts and booleans rather than converting them.
- Hold payment separately until a sale commits. `_refund()` detaches and returns the complete `_inserted` counter; stored cash stays unchanged. `HasMoney.cancel()` then installs `Idle`.
- Use bounded dynamic programming for change. Each held coin is considered once; descending amounts prevent reusing it. Keep the fewest-coin combination for each reachable amount. The search suits a small coin tray and scans coins against the change amount.
- Keep `make_change()` nested inside `_sell()` because only that operation uses it. It reads the temporary `available` counter, which includes the current payment, without spending any coins during planning.
- Check item existence, stock, funds, and makeable change before committing. `SaleRefused.reason` is `UNKNOWN_ITEM`, `SOLD_OUT`, `SHORT`, or `NO_CHANGE`; refused selections keep payment, inventory, and state available for retry or cancellation.
- Use `IllegalActionError` for an event forbidden in the current state. Use `ValueError` for invalid setup, coins, or restocking. Reject duplicate names, blank names, negative or noninteger counts, and unsupported denominations. Restocking requires a known item and a positive integer count.
- Permit restocking only in `Idle` or `SoldOut`. Successful restocking from `SoldOut` installs `Idle`; an empty initial inventory also starts in `SoldOut`.
- Keep `Dispensing` as an internal phase of `Machine.select()`. After the sale commits, its `dispense()` handler completes the simulated delivery and chooses the next state. The caller only selects an item. This synchronous exercise assumes delivery succeeds; it has no motor integration, jam recovery, or rollback. The separate state demonstrates event restrictions and the delivery phase.

## Design patterns

| Pattern | Where | Purpose |
| --- | --- | --- |
| State | `Machine._state`, concrete `State` base, and four subclasses | Give each state its legal events and transitions; inherited events fail by default. |

## Design principles

| Principle | Where / how |
| --- | --- |
| Single responsibility | Machine operations maintain inventory and money; state objects enforce event permissions and transitions. |
| Open/closed | State-specific behavior lives in subclasses while machine forwarding methods stay unchanged. New event types still require interface changes. |

## Concurrency

| Concern | Implementation |
| --- | --- |
| Customer ownership | One payment and state serve one customer flow at a time. There are no separate sessions. |
| Concurrency assumption | Callers must invoke methods sequentially. No locks protect state delegation, cash planning, inventory, or transitions. |
| Purchase lifecycle | `select()` commits, enters `Dispensing`, and completes internal dispensing before returning. This ordering provides no thread-safety guarantee. |

## Common mistakes

- Copy incoming items. Copying just the dictionary would still share mutable `Item` objects with callers.
- Keep `_coins` and `_inserted` separate until commit. Insertion and cancellation must leave stored cash unchanged.
- Search physical coin counts before changing inventory or payment. Greedy change can refuse a sale that bounded search can complete.
- Keep payment after a refused purchase. The customer can add coins, choose another item, or cancel.
- Apply state changes only after the machine operation succeeds. An invalid coin or restock must leave the current state intact.
- Treat `SoldOut` as all inventory empty; one empty item can still produce `Reason.SOLD_OUT` while other items remain available.
- Treat underscore-prefixed fields as internal. Python privacy is conventional, and direct mutation can break the invariants.
- Keep dispensing internal to `select()`. Return change only after the state has moved from `Dispensing` to `Idle` or `SoldOut`.
