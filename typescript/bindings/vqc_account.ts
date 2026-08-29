/** Bindings for verified VQC account transitions. */

import { Dafny, IntegerInput, Natural, Sequence } from "./vqc_dafny_core";
import { Money } from "./vqc_currency";
import {
    Account,
    FillRecord,
    OrderRecord,
    OrderStatus,
    PositionRecord,
    toDafnyOrderStatus,
} from "./vqc_types";

type RuntimeLedgerEntry = { readonly ledgerId: { toFixed(): string } };
type RuntimeAccount = {
    readonly ledger: { readonly Elements: readonly RuntimeLedgerEntry[] };
};

/** Returns an identifier greater than every entry in the current ledger. */
function NextLedgerId(account: Account): string {
    const runtimeAccount = account as unknown as RuntimeAccount;
    let greatest = 0n;
    for (const entry of runtimeAccount.ledger.Elements) {
        const entryId = BigInt(entry.ledgerId.toFixed());
        if (entryId > greatest) {
            greatest = entryId;
        }
    }
    return (greatest + 1n).toString();
}

/** Returns a new empty account. */
export function NewAccount(): Account {
    return Dafny.AccountOps.__default.NewAccount() as Account;
}

/** Creates an account from a trusted broker-state snapshot. */
export function Bootstrap(
    cash: Money,
    positions: readonly PositionRecord[],
    orders: readonly OrderRecord[],
    ledgerId: IntegerInput = 1,
    timestamp: IntegerInput = 0,
): Account {
    return Dafny.AccountOps.__default.Bootstrap(
        cash,
        Sequence(positions),
        Sequence(orders),
        Natural(ledgerId, "ledgerId"),
        Natural(timestamp, "timestamp"),
    ) as Account;
}

/** Applies a deposit and its ledger entry. */
export function Deposit(
    account: Account, amount: Money, ledgerId?: IntegerInput, timestamp: IntegerInput = 0,
): Account {
    const resolvedId = ledgerId === undefined ? NextLedgerId(account) : ledgerId;
    return Dafny.AccountOps.__default.Deposit(
        account, Natural(resolvedId, "ledgerId"), amount, Natural(timestamp, "timestamp"),
    ) as Account;
}

/** Applies a withdrawal and its ledger entry. */
export function Withdraw(
    account: Account, amount: Money, ledgerId?: IntegerInput, timestamp: IntegerInput = 0,
): Account {
    const resolvedId = ledgerId === undefined ? NextLedgerId(account) : ledgerId;
    return Dafny.AccountOps.__default.Withdraw(
        account, Natural(resolvedId, "ledgerId"), amount, Natural(timestamp, "timestamp"),
    ) as Account;
}

/** Places a valid new order. */
export function PlaceOrder(account: Account, order: OrderRecord): Account {
    return Dafny.AccountOps.__default.PlaceOrder(account, order) as Account;
}

/** Applies a non-fill lifecycle status change to an existing order. */
export function SetOrderStatus(
    account: Account, orderId: IntegerInput, newStatus: OrderStatus,
): Account {
    return Dafny.AccountOps.__default.SetOrderStatus(
        account, Natural(orderId, "orderId"), toDafnyOrderStatus(newStatus),
    ) as Account;
}

/** Applies a fill to its stored order, position, cash balance, and ledger. */
export function Update(account: Account, fill: FillRecord): Account {
    return Dafny.AccountOps.__default.Update(account, fill) as Account;
}
