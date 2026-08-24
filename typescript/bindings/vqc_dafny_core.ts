/** Internal access to the JavaScript generated from the Dafny VQC core. */

declare function require(moduleName: string): any;

export const Dafny = require("../compiled/VQC.js");

export type IntegerInput = string | number | bigint;
export type DafnyInteger = {
    isNegative(): boolean;
    toFixed(): string;
};

export type DafnyString = { readonly _dafnyString: unique symbol };
export type DafnySequence<T> = { readonly _dafnySequence: T };

export function Integer(value: IntegerInput, name: string): DafnyInteger {
    if (typeof value === "number" && !Number.isSafeInteger(value)) {
        throw new TypeError(`${name} must be a safe integer when passed as a number`);
    }

    const text = value.toString();
    if (!/^-?\d+$/.test(text)) {
        throw new TypeError(`${name} must be an integer`);
    }

    return new Dafny.BigNumber(text);
}

export function Natural(value: IntegerInput, name: string): DafnyInteger {
    const integer = Integer(value, name);
    if (integer.isNegative()) {
        throw new RangeError(`${name} must be non-negative`);
    }
    return integer;
}

export function StringValue(value: string, name: string): DafnyString {
    if (typeof value !== "string") {
        throw new TypeError(`${name} must be a string`);
    }
    return Dafny._dafny.Seq.UnicodeFromString(value) as DafnyString;
}

export function Sequence<T>(values: readonly T[]): DafnySequence<T> {
    return Dafny._dafny.Seq.of(...values) as DafnySequence<T>;
}
