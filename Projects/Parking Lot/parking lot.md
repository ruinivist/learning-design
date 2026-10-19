# Parking lot design

`ParkingLot` owns floors, active tickets, and locking. Allocation chooses a spot;
pricing computes a fee; payment authorizes it. Panels coordinate these pieces.

![Parking lot UML class diagram](parking-lot-uml.svg)

## Reading the UML

1. **Start with `ParkingLot`:** owns tickets and locking; keeps tickets and occupied spots in sync.
2. **Follow lot → floors → spots:** floors group spots; each spot holds a vehicle.
3. **Entry:** `EntryPanel` calls the lot. Its allocation strategy chooses a spot, so selection rules can change without changing parking logic.
4. **Exit:** `ExitPanel` uses pricing and payment. Pricing is replaceable; payment subclasses supply approval while sharing `charge()`'s workflow.
5. **Data:** `Vehicle` enters, `Ticket` records the stay for checkout and pricing, `Receipt` records payment.
6. **Displays:** floors notify observers after state changes. `DisplayBoard` handles presentation separately from parking logic.

## Happy path

1. `EntryPanel.park()` supplies the entry time and calls `ParkingLot.park()`.
2. The lot locks; `AllocationStrategy.choose()` selects a free, compatible spot.
3. The floor occupies the spot; the lot creates and registers a `Ticket`, notifies
   displays, then unlocks and returns the ticket.
4. At exit, `ExitPanel.settle(ticket.id)` supplies the exit time and enters
   `ParkingLot.checkout()`, which locks and looks up the active ticket.
5. `PricingStrategy.price()` computes the fee. For a positive fee,
   `PaymentProcessor.charge()` calls `authorize()` and creates a `Receipt`.
6. On success, checkout calls `release()`: the floor frees the spot, the lot
   removes the active ticket, and displays update. The lot unlocks;
   `settle()` returns the receipt.

## Design BOW

- **Strategy:** Swap allocation or pricing without changing the lot or panels.
- **Observer:** Floors notify display boards after committed state changes.
- **Template Method:** `charge()` handles approval and receipt creation;
  payment subclasses implement `authorize()`.
- **Composition:** Lot owns floors; floors own spots. Vehicles and tickets
  are immutable data objects; vehicle categories use enums, not subclasses.

## GoF patterns

| Pattern             | Where                                           | Purpose                                                                                     |
| ------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **Strategy**        | `AllocationStrategy`, `PricingStrategy`         | Swap spot selection or pricing rules without changing their callers.                        |
| **Observer**        | `Subject`, `Observer`, `Floor`, `DisplayBoard`  | Notify displays when floor availability changes.                                            |
| **Template Method** | `PaymentProcessor.charge()` calls `authorize()` | Keep approval checking and receipt creation fixed while subclasses supply payment behavior. |

## SOLID principles

| Principle                 | Where / how                                                                                                               |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Single Responsibility** | Allocation chooses spots, pricing computes fees, payment handles approval, and the lot maintains parking state.           |
| **Open/Closed**           | Add allocation, pricing, or payment subclasses without changing the coordinating workflow.                                |
| **Dependency Inversion**  | The lot and exit panel receive abstract strategies/processors; `build_lot()` and callers choose concrete implementations. |

## Concurrency

| Concern                 | Implementation                                                                                 |
| ----------------------- | ---------------------------------------------------------------------------------------------- |
| **Double allocation**   | One lot lock covers choosing a spot, occupying it, and registering its ticket.                 |
| **Double charging**     | All exit panels share the lot's checkout lock across lookup, pricing, payment, and release.    |
| **Reentrant locking**   | `RLock` lets checkout call `find_active()` and `release()`, which acquire the same lock again. |
| **Consistent displays** | Observers read committed spot/ticket state while the lot lock is held.                         |
| **Tradeoff**            | Payment and observer callbacks block other lot operations; suitable for this in-memory toy.    |

## common mistakes

- Lock entire checkout to prevent double charging.
- Commit spot/ticket state before notifying; log observer failures independently.
- Reject duplicate floor IDs and spot IDs within each floor.
- Reject negative/nonfinite prices and invalid grace periods.
