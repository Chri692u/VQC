# TypeScript API Overview

The experimental TypeScript binding exposes the verified VQC core.

```typescript
import { VQC } from "./vqc";

const account = VQC.NewAccount();
const order = VQC.Order(1, "GLD", 1);
const next = VQC.PlaceOrder(account, order);
```

## Records and enums

- `Account`, `Ledger`, `OrderRecord`, `FillRecord`, `PositionRecord`
- `OrderSide`: `"buy" | "sell"`
- `OrderType`: `"market" | "limit" | "stop" | "stop_limit"`
- `OrderStatus`: `"pending" | "open" | "partially_filled" | "filled" | "cancelled" | "rejected"`

## Available functions

| Function | Purpose |
| --- | --- |
| `Money.FromDecimal`, `Money.FromMinorUnits` | Create money values. |
| `Sum`, `Cost` | Perform money arithmetic. |
| `Order`, `Fill`, `Position` | Create VQC records. |
| `NewAccount` | Creates an empty account. |
| `Bootstrap` | Creates an account from a trusted snapshot. |
| `Deposit`, `Withdraw` | Apply cash movements and ledger entries. |
| `PlaceOrder` | Adds a fresh pending, unfilled order. |
| `SetOrderStatus` | Applies a non-fill lifecycle transition. |
| `Update` | Applies a priced fill. |
| `RemainingQuantity` | Returns an order's unfilled quantity. |

Validation predicates are `IsValidOrder`, `IsValidFill`, `IsValidPosition`, `IsValidLedger`, and `IsValidAccount`. Failed verified preconditions raise `HaltException`.

## Bindings-only example

`examples/BasicAccount.ts` creates an account, deposits cash, fills one market
order, and cancels one limit order without connecting to a broker. Build and run
it with:

```powershell
npm run build
npm run example
```
