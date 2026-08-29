/** Small bindings-only VQC example. No broker or network access is involved. */

import {
    Bootstrap,
    Deposit,
    Fill,
    IsValidAccount,
    Money,
    Order,
    PlaceOrder,
    SetOrderStatus,
    Update,
} from "../vqc";

let account = Bootstrap(Money.FromDecimal("1000.00"), [], [], 1, 1_700_000_000);

// With no explicit ledger ID, the binding selects the next available ID.
account = Deposit(account, Money.FromDecimal("250.00"), undefined, 1_700_000_001);

const appleOrder = Order(100, "AAPL", 2, "buy", "market");
account = PlaceOrder(account, appleOrder);
account = SetOrderStatus(account, 100, "open");

const appleFill = Fill(
    3,
    100,
    "AAPL",
    2,
    Money.FromDecimal("125.50"),
    1_700_000_002,
);
account = Update(account, appleFill);

const goldOrder = Order(
    101,
    "GLD",
    1,
    "buy",
    "limit",
    "pending",
    0,
    Money.FromDecimal("225.00"),
);
account = PlaceOrder(account, goldOrder);
account = SetOrderStatus(account, 101, "open");
account = SetOrderStatus(account, 101, "cancelled");

console.log("Account remains valid:", IsValidAccount(account));
console.log("Created one filled AAPL order and one cancelled GLD limit order.");
console.log("\nAAPL order:");
console.dir(appleOrder, { depth: null });
console.log("\nAAPL fill:");
console.dir(appleFill, { depth: null });
console.log("\nGLD order:");
console.dir(goldOrder, { depth: null });
console.log("\nFinal account:");
console.dir(account, { depth: null });
