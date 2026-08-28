# Python API Overview

VQC provides a verified core through `VQC` and a broker-backed trading client through `VQCClient`.

```python
from vqc import VQC
from vqc_client import OrderTimeInForce, VQCClient
from vqc_utility import DisplayAccount, DisplayLedger, Logger, ReportException
```

## Verified core

Public records are `Account`, `Ledger`, `OrderRecord`, `FillRecord`, and `PositionRecord`. Orders use `OrderSide`, `OrderType`, and `OrderStatus`.

| Call | Purpose |
| --- | --- |
| `VQC.Money.FromDecimal(value)` | Creates money from major units. |
| `VQC.Money.FromMinorUnits(value)` | Creates money from exact minor units. |
| `money.ToDecimal()` | Returns major units as a `Decimal`. |
| `VQC.Order(...)`, `VQC.Fill(...)`, `VQC.Position(...)` | Create VQC records. |
| `VQC.Sum(values)`, `VQC.Cost(quantity, price)` | Perform money arithmetic. |
| `VQC.NewAccount()` | Creates an empty account. |
| `VQC.Bootstrap(cash, positions, orders, ledger_id=1, timestamp=0)` | Creates an account from a trusted snapshot. |
| `VQC.Deposit(account, amount, ledger_id=None, timestamp=0)` | Deposits cash. |
| `VQC.Withdraw(account, amount, ledger_id=None, timestamp=0)` | Withdraws cash. |
| `VQC.PlaceOrder(account, order)` | Adds a fresh pending, unfilled order. |
| `VQC.SetOrderStatus(account, order_id, status)` | Applies a non-fill lifecycle transition. |
| `VQC.Update(account, fill)` | Applies a priced fill. |
| `VQC.RemainingQuantity(order)` | Returns the unfilled quantity. |

Validation predicates are `IsValidOrder`, `IsValidFill`, `IsValidPosition`, `IsValidLedger`, and `IsValidAccount`. Failed verified preconditions raise `VQC.HaltException`.

## Broker client

```python
from bindings.alpaca_adapter import AlpacaAdapter
from vqc_client import VQCClient
from vqc_utility import Logger

client = VQCClient("KEYS.env", AlpacaAdapter(), Logger())
client.MarketOrder("GLD", 1)
```

The latest verified snapshot is available through `client.account`.

| Method | Purpose |
| --- | --- |
| `MarketOrder(symbol, quantity, time_in_force=DAY)` | Submits a market order. |
| `LimitOrder(symbol, quantity, limit_price, extended_hours=False, time_in_force=DAY)` | Submits a limit order. |
| `StopOrder(symbol, quantity, stop_price, time_in_force=DAY)` | Submits a stop order. |
| `StopLimitOrder(symbol, quantity, stop_price, limit_price, time_in_force=DAY)` | Submits a stop-limit order. |
| `Liquidate(symbol)` | Sells the verified long position. |
| `MarketIsOpen()` | Reads the broker's regular-session clock. |

Positive quantities buy and negative quantities sell. `OrderTimeInForce` provides `DAY`, `GTC`, `OPG`, `CLS`, `IOC`, and `FOK`, subject to broker rules.

## Diagnostics

- `Logger(mute=False)` emits tagged messages.
- `DisplayAccount(account)` and `DisplayLedger(ledger)` format state.
- `ReportException(error)` formats a VQC runtime error.

See [examples/TUTORIAL.md](examples/TUTORIAL.md) for a guided example.
