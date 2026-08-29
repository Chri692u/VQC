/** Bindings for Dafny currency operations and scaled VQC money values. */

import { Dafny, Integer, IntegerInput, Natural, Sequence } from "./vqc_dafny_core";

export type DecimalInput = string | number | bigint;

/**
 * A signed integer money value in minor units. The scale is 100, so 42533
 * represents 425.33. It is also a Dafny runtime integer accepted by the core.
 */
export class Money extends Dafny.BigNumber {
    static readonly SCALE = 100;

    private constructor(value: DecimalInput, minorUnits: boolean) {
        if (minorUnits) {
            super(Integer(value, "money"));
        } else {
            const decimal = new Dafny.BigNumber(value.toString());
            if (!decimal.isFinite()) {
                throw new RangeError("money values must be finite");
            }
            super(
                decimal
                    .multipliedBy(Money.SCALE)
                    .integerValue(Dafny.BigNumber.ROUND_HALF_EVEN),
            );
        }
    }

    static FromMinorUnits(value: IntegerInput): Money {
        return new Money(value, true);
    }

    static FromDecimal(value: DecimalInput): Money {
        return new Money(value, false);
    }

    static FromFloat(value: number): Money {
        return Money.FromDecimal(value);
    }

    ToDecimal(): string {
        return this.dividedBy(Money.SCALE).toFixed();
    }
}

/** Returns the verified sum of money values. */
export function Sum(values: readonly Money[]): Money {
    return Money.FromMinorUnits(Dafny.Currency.__default.Sum(Sequence(values)));
}

/** Returns the verified cost of a quantity at a minor-unit price. */
export function Cost(quantity: IntegerInput, price: Money): Money {
    return Money.FromMinorUnits(Dafny.Currency.__default.Cost(Natural(quantity, "quantity"), price));
}
