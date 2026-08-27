"""
API Bindings for the VQC Currency module.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from bindings.vqc_dafny_core import EnsureDafnyCore

EnsureDafnyCore()

import Currency as CurrencyModule

DafnyCurrency = CurrencyModule.default__


class Money(int):
    """Integer-backed money value with explicit decimal conversion methods.

    The underlying Dafny model stores money as an integer, so the Python wrapper
    preserves that exact integer representation internally. For user-facing
    decimal values, provide explicit conversion methods.
    """

    SCALE = 100  # Number of minor units in one major currency unit.
    ROUNDING = ROUND_HALF_EVEN  # Deterministic accounting-style tie breaking.

    @classmethod
    def _AsDecimal(cls, value: Any) -> Decimal:
        if isinstance(value, bool):
            raise TypeError("money values cannot be booleans")
        if isinstance(value, Decimal):
            return value
        if isinstance(value, float):
            return Decimal(str(value))
        if isinstance(value, str):
            return Decimal(value)
        if isinstance(value, int):
            return Decimal(int(value))
        return Decimal(int(value))

    @classmethod
    def _Normalize(cls, value: Any) -> int:
        if isinstance(value, bool):
            raise TypeError("money values cannot be booleans")
        if isinstance(value, Money):
            return int(value)
        if isinstance(value, (Decimal, float, str)):
            return int(
                (cls._AsDecimal(value) * cls.SCALE).to_integral_value(
                    rounding=cls.ROUNDING
                )
            )
        if isinstance(value, int):
            return int(value)
        return int(value)

    @staticmethod
    def _Coerce(value: Any) -> int:
        return Money._Normalize(value)

    @classmethod
    def FromMinorUnits(cls, value: int) -> "Money":
        """Create money from its exact integer minor-unit representation."""
        return int.__new__(cls, int(value))

    @classmethod
    def FromDecimal(cls, value: Decimal | float | int | str) -> "Money":
        """Create money from a major-unit value, rounded to the nearest cent."""
        decimal_value = cls._AsDecimal(value)
        if not decimal_value.is_finite():
            raise ValueError("money values must be finite")
        minor_units = (decimal_value * cls.SCALE).to_integral_value(
            rounding=cls.ROUNDING
        )
        return cls.FromMinorUnits(minor_units)

    def ToDecimal(self) -> Decimal:
        """Return the major-unit decimal representation."""
        return Decimal(int(self)) / Decimal(self.SCALE)

    def __new__(cls, value: int | float | Decimal | str = 0):
        if isinstance(value, bool):
            raise TypeError("money values cannot be booleans")
        if isinstance(value, (Decimal, float, str)):
            decimal_value = cls._AsDecimal(value)
            if not decimal_value.is_finite():
                raise ValueError("money values must be finite")
            value = (decimal_value * cls.SCALE).to_integral_value(
                rounding=cls.ROUNDING
            )
        return int.__new__(cls, int(value))

    def __add__(self, other):
        return Money.FromMinorUnits(int(self) + self._Coerce(other))

    __radd__ = __add__

    def __sub__(self, other):
        return Money.FromMinorUnits(int(self) - self._Coerce(other))

    def __rsub__(self, other):
        return Money.FromMinorUnits(self._Coerce(other) - int(self))

    def __mul__(self, other):
        if (
            isinstance(other, bool)
            or not isinstance(other, int)
            or isinstance(other, Money)
        ):
            raise TypeError("money can only be multiplied by an integer quantity")
        return Money.FromMinorUnits(int(self) * other)

    __rmul__ = __mul__

    def __pos__(self):
        return Money.FromMinorUnits(+int(self))

    def __neg__(self):
        return Money.FromMinorUnits(-int(self))

    def __abs__(self):
        return Money.FromMinorUnits(abs(int(self)))

    def __lt__(self, other):
        return int(self) < self._Coerce(other)

    def __le__(self, other):
        return int(self) <= self._Coerce(other)

    def __gt__(self, other):
        return int(self) > self._Coerce(other)

    def __ge__(self, other):
        return int(self) >= self._Coerce(other)

    def __str__(self):
        return str(self.ToDecimal())

    def __repr__(self):
        return f"Money({self.ToDecimal()})"


def Sum(values: list[Money]) -> Money:
    """Return the verified sum of money values."""
    return Money.FromMinorUnits(DafnyCurrency.Sum([int(value) for value in values]))


def Cost(quantity: int, price: Money) -> Money:
    """Return the verified cost of a whole quantity at one price."""
    return Money.FromMinorUnits(DafnyCurrency.Cost(quantity, int(price)))

