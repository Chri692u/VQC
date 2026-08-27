# VQC Python API

VQC has two public layers:

```python
from vqc import VQC
from vqc_client import VQCClient
from vqc_utility import DisplayAccount, DisplayLedger, Logger, ReportException
```

- `VQC` exposes verified records, money operations, validation predicates, and
  immutable account transitions.
- `VQCClient` submits broker orders and exposes the latest verified account.

Generated modules, synchronization workers, ID maps, locks, conversion helpers,
and names beginning with `_` are implementation details. In particular, the
daemon is owned privately by `VQCClient` and is not part of the public API.

All verified account operations return a new account instead of mutating their
input. A failed Dafny precondition raises `VQC.HaltException`.

## Verified types and money

The public record aliases are `VQC.Account`, `VQC.Ledger`, `VQC.OrderRecord`,
`VQC.FillRecord`, and `VQC.PositionRecord`.

Orders use broker-neutral enums:

- `VQC.OrderSide`: `BUY`, `SELL`
- `VQC.OrderType`: `MARKET`, `LIMIT`, `STOP`, `STOP_LIMIT`
- `VQC.OrderStatus`: `NEW`, `ACCEPTED`, `PARTIALLY_FILLED`, `FILLED`,
  `CANCELLED`, `REJECTED`

Broker-native strings are normalized inside the selected adapter and do not
enter the verified API.

| Call | Result |
| --- | --- |
| `VQC.Money.FromDecimal(value)` | Converts major units to scaled minor units using round-half-even. |
| `VQC.Money.FromMinorUnits(value)` | Creates money from exact integer minor units. |
| `money.ToDecimal()` | Returns the major-unit `Decimal`. |
| `VQC.Sum(values)` | Returns the verified sum of money values. |
| `VQC.Cost(quantity, price)` | Returns verified whole-quantity notional value. |
| `VQC.Order(...)` | Creates a market, limit, stop, or stop-limit order. |
| `VQC.Fill(execution_id, order_id, symbol, quantity, price, timestamp)` | Creates a priced execution. |
| `VQC.Position(symbol, quantity, average_price)` | Creates a positive long position. |

`VQC.Order` accepts `limit_price` and `stop_price`. Limit orders require the
former, stop orders require the latter, and stop-limit orders require both.

## Verified account operations

| Call | Result |
| --- | --- |
| `VQC.NewAccount()` | Returns an empty valid account. |
| `VQC.Bootstrap(cash, positions, orders, ledger_id=1, timestamp=0)` | Creates the supplied snapshot and one matching opening entry. |
| `VQC.Deposit(account, amount, ledger_id=1, timestamp=0)` | Adds positive cash and a deposit entry. |
| `VQC.Withdraw(account, amount, ledger_id=1, timestamp=0)` | Removes positive cash and adds a withdrawal entry. |
| `VQC.PlaceOrder(account, order)` | Adds a valid order with a fresh order ID. |
| `VQC.SetOrderStatus(account, order_id, new_status)` | Applies a valid non-fill lifecycle transition. |
| `VQC.Update(account, fill)` | Applies a priced fill to the order, cash, position, and ledger. |

Use `Update` only for actual executions. Cumulative filled quantity from an
order-submission response is not treated as a fill because it has no incremental
execution price. Use `SetOrderStatus` for acceptance, cancellation, rejection,
and other non-fill lifecycle events.

Closing a long position removes it from `account.positions`; its order and trade
ledger entries remain as history. Ledger entries expose `ledgerId`, while orders
and fills expose `orderId` and `executionId`.

The read-only predicates are `IsValidOrder`, `IsValidFill`, `IsValidPosition`,
`IsValidLedger`, and `IsValidAccount`. `RemainingQuantity(order)` returns the
unfilled whole-share quantity.

## Broker client

```python
client = VQCClient()
client.MarketOrder("GLD", 1)   # buy one share
client.MarketOrder("GLD", -1)  # sell one share
```

The intentionally small `VQCClient` surface is:

- `broker`: native broker client for broker-specific reads
- `logger`: configured VQC logger
- `account`: read-only latest verified snapshot
- `MarketOrder`, `LimitOrder`, `StopOrder`, `StopLimitOrder`
- `Liquidate`, `MarketIsOpen`

Every order method uses a signed whole-share quantity: positive buys, negative
sells, and zero is invalid. Fractional quantities are rejected rather than
rounded or truncated. Required limit and stop prices must be positive and
finite.

```python
client.LimitOrder("GLD", 1, limit_price="425.00")
client.StopOrder("GLD", -1, stop_price="400.00")
client.StopLimitOrder(
    "GLD", -1, stop_price="400.00", limit_price="399.00"
)
client.Liquidate("GLD")
```

Regular orders are rejected locally when the broker reports that its regular
market is closed. Extended hours are requested only through
`LimitOrder(..., extended_hours=True)`; the broker remains authoritative about
whether that order is eligible to execute. `Liquidate` submits a market sell for
the full verified long position and rejects symbols that already have an open
sell order.

Order submission and background reconciliation share one private state lock.
Applications should read `client.account` and use the public order methods, not
access synchronization fields directly.

## Broker adapters

`BrokerAdapter` is the public protocol for another broker integration, and
`AlpacaAdapter` is the included implementation:

```python
from bindings.alpaca_adapter import AlpacaAdapter
from bindings.broker_adapter import BrokerAdapter

client = VQCClient(adapter=AlpacaAdapter())
```

An adapter owns all broker-specific requests, status normalization, streaming,
and conversion to VQC records. Passing `adapter=...` and `broker=...` allows a
different integration without introducing its types into the client or verified
core. Each client receives its own adapter instance and mapping state.

The current VQC model supports whole-share, long-only positions. An adapter must
reject fractional quantities and short positions instead of silently changing
their values.

## Diagnostics

`Logger(mute=False)` prints consistently tagged messages. `DisplayAccount`,
`DisplayLedger`, and `ReportException` return readable diagnostic strings. The
shared utility class and its mapping/ID helpers are private implementation
details and are intentionally absent from `__all__`.

`examples/IntervalBuy.py` demonstrates regular-session market orders and
extended-hours limit orders derived from a usable ask quote.
