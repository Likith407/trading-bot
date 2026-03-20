"""Validate and normalise all user-supplied inputs before they reach the API."""

from __future__ import annotations
import re
from decimal import Decimal, InvalidOperation

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


class ValidationError(ValueError):
    """Raised when user input fails validation."""


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not re.fullmatch(r"[A-Z]{3,20}", s):
        raise ValidationError(f"Invalid symbol '{s}'. Expected e.g. BTCUSDT.")
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValidationError(f"Side must be BUY or SELL, got '{s}'.")
    return s


def validate_order_type(order_type: str) -> str:
    ot = order_type.strip().upper()
    if ot not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Order type must be one of {sorted(VALID_ORDER_TYPES)}, got '{ot}'."
        )
    return ot


def _to_decimal(value: str | float, name: str) -> Decimal:
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        raise ValidationError(f"'{name}' must be a number, got '{value}'.")
    if d <= 0:
        raise ValidationError(f"'{name}' must be > 0, got {d}.")
    return d


def validate_quantity(qty: str | float) -> Decimal:
    return _to_decimal(qty, "quantity")


def validate_price(price: str | float | None) -> Decimal | None:
    return None if price is None else _to_decimal(price, "price")


def validate_stop_price(stop_price: str | float | None) -> Decimal | None:
    return None if stop_price is None else _to_decimal(stop_price, "stop_price")
