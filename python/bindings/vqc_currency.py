"""
API Bindings for the VQC Currency module.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Any

from bindings.vqc_dafny_core import EnsureDafnyCore

EnsureDafnyCore()

from _dafny import HaltException
import Currency as CurrencyModule
DafnyCurrency = CurrencyModule.default__

class Money(int):
    """Integer-backed money value with explicit decimal conversion methods.

    The underlying Dafny model stores money as an integer, so the Python wrapper
    preserves that exact integer representation internally. For user-facing
    decimal values, provide explicit conversion methods.
    """

    SCALE = 100

    @classmethod
    def AsDecimal(cls, value: Any) -> Decimal:
        if isinstance(value, bool):
            return Decimal(int(value))
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
    def Normalize(cls, value: Any) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, Money):
            return int(value)
        if isinstance(value, (Decimal, float, str)):
            return int((cls.AsDecimal(value) * cls.SCALE).to_integral_value())
        if isinstance(value, int):
            return int(value)
        return int(value)

    @staticmethod
    def Coerce(value: Any) -> int:
        return Money.Normalize(value)

    @classmethod
    def FromMinorUnits(cls, value: int) -> "Money":
        return int.__new__(cls, int(value))

    @classmethod
    def FromDecimal(cls, value: Decimal | float | int | str) -> "Money":
        minor_units = (cls.AsDecimal(value) * cls.SCALE).to_integral_value()
        return cls.FromMinorUnits(minor_units)

    @classmethod
    def FromFloat(cls, value: float) -> "Money":
        return cls.FromDecimal(value)

    def ToDecimal(self) -> Decimal:
        return Decimal(int(self)) / Decimal(self.SCALE)

    def __new__(cls, value: int | float | Decimal | str = 0):
        if isinstance(value, (Decimal, float, str)):
            value = (cls.AsDecimal(value) * cls.SCALE).to_integral_value()
        return int.__new__(cls, int(value))

    def __add__(self, other):
        return Money(int(self) + self.Coerce(other))

    __radd__ = __add__

    def __sub__(self, other):
        return Money(int(self) - self.Coerce(other))

    def __rsub__(self, other):
        return Money(self.Coerce(other) - int(self))

    def __mul__(self, other):
        return Money(int(self) * self.Coerce(other))

    __rmul__ = __mul__

    def __pos__(self):
        return Money(+int(self))

    def __neg__(self):
        return Money(-int(self))

    def __abs__(self):
        return Money(abs(int(self)))

    def __lt__(self, other):
        return int(self) < self.Coerce(other)

    def __le__(self, other):
        return int(self) <= self.Coerce(other)

    def __gt__(self, other):
        return int(self) > self.Coerce(other)

    def __ge__(self, other):
        return int(self) >= self.Coerce(other)

    def __str__(self):
        return str(self.ToDecimal())

    def __repr__(self):
        return f"Money({self.ToDecimal()})"


def Sum(values: list[Money]) -> Money:
    return Money(DafnyCurrency.Sum([int(value) for value in values]))


def Cost(quantity: int, price: Money) -> Money:
    return Money(DafnyCurrency.Cost(quantity, int(price)))

