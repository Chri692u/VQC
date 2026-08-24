/** Type-safe constructors for the Dafny-generated VQC value types. */

declare function require(moduleName: string): any;

const Dafny = require("../compiled/VQC.js");

type GeneratedInteger = {
    isNegative(): boolean;
    isInteger(): boolean;
    toFixed(): string;
};

export type MoneyValue = GeneratedInteger;
export type OrderId = GeneratedInteger;
export type ExecutionId = GeneratedInteger;
export type LedgerId = GeneratedInteger;
export type OrderSide = "buy" | "sell";
export type OrderStatus =
    | "new"
    | "accepted"
    | "partially_filled"
    | "filled"
    | "cancelled"
    | "rejected";

export type OrderRecord = {
    dtor_orderId: OrderId;
    dtor_symbol: unknown;
    dtor_quantity: GeneratedInteger;
    dtor_side: unknown;
    dtor_orderType: unknown;
    dtor_status: unknown;
    dtor_filledQuantity: GeneratedInteger;
};

export type FillRecord = {
    dtor_executionId: ExecutionId;
    dtor_orderId: OrderId;
    dtor_symbol: unknown;
    dtor_quantity: GeneratedInteger;
    dtor_price: MoneyValue;
    dtor_timestamp: GeneratedInteger;
};

export type PositionRecord = {
    dtor_symbol: unknown;
    dtor_quantity: GeneratedInteger;
    dtor_averagePrice: MoneyValue;
};

export type Ledger = unknown;
export type Account = unknown;

export type IntegerInput = string | number | bigint;

export interface OrderInput {
    orderId: IntegerInput;
    symbol: string;
    quantity: IntegerInput;
    side?: OrderSide;
    status?: OrderStatus;
    filledQuantity?: IntegerInput;
    limitPrice?: IntegerInput;
}

export interface FillInput {
    executionId: IntegerInput;
    orderId: IntegerInput;
    symbol: string;
    quantity: IntegerInput;
    price: IntegerInput;
    timestamp: IntegerInput;
}

export interface PositionInput {
    symbol: string;
    quantity: IntegerInput;
    averagePrice: IntegerInput;
}

function ToInteger(value: IntegerInput, name: string): GeneratedInteger {
    if (typeof value === "number" && (!Number.isSafeInteger(value))) {
        throw new TypeError(`${name} must be a safe integer when passed as a number`);
    }

    const text = value.toString();
    if (!/^-?\d+$/.test(text)) {
        throw new TypeError(`${name} must be an integer`);
    }

    return new Dafny.BigNumber(text);
}

function ToNatural(value: IntegerInput, name: string): GeneratedInteger {
    const integer = ToInteger(value, name);
    if (integer.isNegative()) {
        throw new RangeError(`${name} must be non-negative`);
    }
    return integer;
}

function ToDafnyString(value: string, name: string): unknown {
    if (typeof value !== "string") {
        throw new TypeError(`${name} must be a string`);
    }
    return Dafny._dafny.Seq.UnicodeFromString(value);
}

function ToSide(side: OrderSide): unknown {
    return side === "buy"
        ? Dafny.Types.OrderSide.create_Buy()
        : Dafny.Types.OrderSide.create_Sell();
}

function ToStatus(status: OrderStatus): unknown {
    switch (status) {
        case "new": return Dafny.Types.OrderStatus.create_New();
        case "accepted": return Dafny.Types.OrderStatus.create_Accepted();
        case "partially_filled": return Dafny.Types.OrderStatus.create_PartiallyFilled();
        case "filled": return Dafny.Types.OrderStatus.create_Filled();
        case "cancelled": return Dafny.Types.OrderStatus.create_Cancelled();
        case "rejected": return Dafny.Types.OrderStatus.create_Rejected();
    }
}

/** Creates a signed Dafny money value in minor units. */
export const Money = {
    FromMinorUnits(value: IntegerInput): MoneyValue {
        return ToInteger(value, "money");
    },

    ToMinorUnits(value: MoneyValue): string {
        return value.toFixed();
    },
};

/** Creates a Dafny order record. A missing limit price means a market order. */
export function Order(input: OrderInput): OrderRecord {
    const orderType = input.limitPrice === undefined
        ? Dafny.Types.OrderType.create_Market()
        : Dafny.Types.OrderType.create_Limit(Money.FromMinorUnits(input.limitPrice));

    return Dafny.Types.Order.create_Order(
        ToNatural(input.orderId, "orderId"),
        ToDafnyString(input.symbol, "symbol"),
        ToNatural(input.quantity, "quantity"),
        ToSide(input.side ?? "buy"),
        orderType,
        ToStatus(input.status ?? "new"),
        ToNatural(input.filledQuantity ?? 0, "filledQuantity"),
    );
}

/** Creates a Dafny fill record for an existing order. */
export function Fill(input: FillInput): FillRecord {
    return Dafny.Types.Fill.create_Fill(
        ToNatural(input.executionId, "executionId"),
        ToNatural(input.orderId, "orderId"),
        ToDafnyString(input.symbol, "symbol"),
        ToNatural(input.quantity, "quantity"),
        Money.FromMinorUnits(input.price),
        ToNatural(input.timestamp, "timestamp"),
    );
}

/** Creates a Dafny long-position record. */
export function Position(input: PositionInput): PositionRecord {
    return Dafny.Types.Position.create_Position(
        ToDafnyString(input.symbol, "symbol"),
        ToNatural(input.quantity, "quantity"),
        Money.FromMinorUnits(input.averagePrice),
    );
}

/** Converts a JavaScript array to the Dafny sequence representation. */
export function Sequence<T>(values: readonly T[]): unknown {
    return Dafny._dafny.Seq.of(...values);
}

export const HaltException = Dafny._dafny.HaltException;
