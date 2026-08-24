/** Bindings for VQC record construction, order utility, and validation. */

import { Dafny, IntegerInput, Natural, StringValue } from "./vqc_dafny_core";
import { Money } from "./vqc_currency";

declare const accountBrand: unique symbol;
declare const ledgerBrand: unique symbol;
declare const orderBrand: unique symbol;
declare const fillBrand: unique symbol;
declare const positionBrand: unique symbol;

export type Account = { readonly [accountBrand]: "Account" };
export type Ledger = { readonly [ledgerBrand]: "Ledger" };
export type OrderRecord = { readonly [orderBrand]: "Order" };
export type FillRecord = { readonly [fillBrand]: "Fill" };
export type PositionRecord = { readonly [positionBrand]: "Position" };

export type OrderSide = "buy" | "sell";
export type OrderType = "market" | "limit";
export type OrderStatus =
    | "new"
    | "accepted"
    | "partially_filled"
    | "filled"
    | "cancelled"
    | "rejected";

type DafnyOrderSide = { readonly _dafnyOrderSide: unique symbol };
type DafnyOrderType = { readonly _dafnyOrderType: unique symbol };
type DafnyOrderStatus = { readonly _dafnyOrderStatus: unique symbol };

function SideEnum(side: OrderSide): DafnyOrderSide {
    if (side === "buy") {
        return Dafny.Types.OrderSide.create_Buy() as DafnyOrderSide;
    }
    if (side === "sell") {
        return Dafny.Types.OrderSide.create_Sell() as DafnyOrderSide;
    }
    throw new Error(`unsupported side: ${side}`);
}

/** Converts a public status string to the generated Dafny status value. */
export function StatusEnum(status: OrderStatus): DafnyOrderStatus {
    switch (status) {
        case "new": return Dafny.Types.OrderStatus.create_New() as DafnyOrderStatus;
        case "accepted": return Dafny.Types.OrderStatus.create_Accepted() as DafnyOrderStatus;
        case "partially_filled": return Dafny.Types.OrderStatus.create_PartiallyFilled() as DafnyOrderStatus;
        case "filled": return Dafny.Types.OrderStatus.create_Filled() as DafnyOrderStatus;
        case "cancelled": return Dafny.Types.OrderStatus.create_Cancelled() as DafnyOrderStatus;
        case "rejected": return Dafny.Types.OrderStatus.create_Rejected() as DafnyOrderStatus;
    }
}

/** Creates a VQC order record. */
export function Order(
    orderId: IntegerInput,
    symbol: string,
    quantity: IntegerInput,
    side: OrderSide = "buy",
    orderType: OrderType = "market",
    status: OrderStatus = "new",
    filledQuantity: IntegerInput = 0,
    limitPrice?: Money,
): OrderRecord {
    let orderTypeEnum: DafnyOrderType;
    if (orderType === "market") {
        orderTypeEnum = Dafny.Types.OrderType.create_Market() as DafnyOrderType;
    } else if (orderType === "limit") {
        if (limitPrice === undefined) {
            throw new Error("limit order requires a limitPrice");
        }
        orderTypeEnum = Dafny.Types.OrderType.create_Limit(limitPrice) as DafnyOrderType;
    } else {
        throw new Error(`unsupported order type: ${orderType}`);
    }

    return Dafny.Types.Order.create_Order(
        Natural(orderId, "orderId"),
        StringValue(symbol, "symbol"),
        Natural(quantity, "quantity"),
        SideEnum(side),
        orderTypeEnum,
        StatusEnum(status),
        Natural(filledQuantity, "filledQuantity"),
    ) as OrderRecord;
}

/** Creates a VQC fill record for an existing order. */
export function Fill(
    executionId: IntegerInput,
    orderId: IntegerInput,
    symbol: string,
    quantity: IntegerInput,
    price: Money,
    timestamp: IntegerInput,
): FillRecord {
    return Dafny.Types.Fill.create_Fill(
        Natural(executionId, "executionId"),
        Natural(orderId, "orderId"),
        StringValue(symbol, "symbol"),
        Natural(quantity, "quantity"),
        price,
        Natural(timestamp, "timestamp"),
    ) as FillRecord;
}

/** Creates a VQC long-position record. */
export function Position(
    symbol: string,
    quantity: IntegerInput,
    averagePrice: Money,
): PositionRecord {
    return Dafny.Types.Position.create_Position(
        StringValue(symbol, "symbol"),
        Natural(quantity, "quantity"),
        averagePrice,
    ) as PositionRecord;
}

export function RemainingQuantity(order: OrderRecord): string {
    return Dafny.Orders.__default.RemainingQuantity(order).toFixed();
}

export function IsValidOrder(order: OrderRecord): boolean {
    return Dafny.Validation.__default.IsValidOrder(order);
}

export function IsValidFill(fill: FillRecord): boolean {
    return Dafny.Validation.__default.IsValidFill(fill);
}

export function IsValidPosition(position: PositionRecord): boolean {
    return Dafny.Validation.__default.IsValidPosition(position);
}

export function IsValidLedger(ledger: Ledger): boolean {
    return Dafny.Validation.__default.IsValidLedger(ledger);
}

export function IsValidAccount(account: Account): boolean {
    return Dafny.Validation.__default.IsValidAccount(account);
}

export const HaltException = Dafny._dafny.HaltException;
