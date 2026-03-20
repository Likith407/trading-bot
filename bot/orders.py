"""
Order placement logic — sits between the CLI and the raw Binance client.
Each function validates inputs, builds the API payload, fires the request,
and returns a clean result dict.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from bot.client import BinanceClient, BinanceAPIError
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
    ValidationError,
)

logger = logging.getLogger("trading_bot.orders")


# ------------------------------------------------------------------ #
# Internal helpers                                                     #
# ------------------------------------------------------------------ #

def _fmt(d: Decimal) -> str:
    """Format a Decimal without trailing zeros."""
    return format(d.normalize(), "f")


def _parse_response(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract the fields we care about from the raw API response."""
    return {
        "orderId": raw.get("orderId"),
        "symbol": raw.get("symbol"),
        "side": raw.get("side"),
        "type": raw.get("type"),
        "origQty": raw.get("origQty"),
        "price": raw.get("price"),
        "stopPrice": raw.get("stopPrice"),
        "status": raw.get("status"),
        "executedQty": raw.get("executedQty"),
        "avgPrice": raw.get("avgPrice"),
        "timeInForce": raw.get("timeInForce"),
        "updateTime": raw.get("updateTime"),
    }


# ------------------------------------------------------------------ #
# Public order functions                                               #
# ------------------------------------------------------------------ #

def place_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: str | float,
) -> dict[str, Any]:
    """
    Place a MARKET order.

    Returns a clean result dict with order details.
    Raises ValidationError or BinanceAPIError on failure.
    """
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    qty = validate_quantity(quantity)

    payload = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": _fmt(qty),
    }

    logger.info(
        "Placing MARKET order: %s %s qty=%s", side, symbol, _fmt(qty)
    )
    raw = client.place_order(**payload)
    result = _parse_response(raw)
    logger.info(
        "MARKET order placed — orderId=%s status=%s executedQty=%s avgPrice=%s",
        result["orderId"],
        result["status"],
        result["executedQty"],
        result["avgPrice"],
    )
    return result


def place_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: str | float,
    price: str | float,
    time_in_force: str = "GTC",
) -> dict[str, Any]:
    """
    Place a LIMIT order.

    Returns a clean result dict with order details.
    Raises ValidationError or BinanceAPIError on failure.
    """
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    qty = validate_quantity(quantity)
    prc = validate_price(price)
    if prc is None:
        raise ValidationError("Price is required for LIMIT orders.")

    payload = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "quantity": _fmt(qty),
        "price": _fmt(prc),
        "timeInForce": time_in_force,
    }

    logger.info(
        "Placing LIMIT order: %s %s qty=%s price=%s tif=%s",
        side, symbol, _fmt(qty), _fmt(prc), time_in_force,
    )
    raw = client.place_order(**payload)
    result = _parse_response(raw)
    logger.info(
        "LIMIT order placed — orderId=%s status=%s",
        result["orderId"],
        result["status"],
    )
    return result


def place_stop_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: str | float,
    stop_price: str | float,
) -> dict[str, Any]:
    """
    Place a STOP_MARKET order (bonus order type).

    Triggers a market order when `stop_price` is reached.
    Raises ValidationError or BinanceAPIError on failure.
    """
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    qty = validate_quantity(quantity)
    sp = validate_stop_price(stop_price)
    if sp is None:
        raise ValidationError("Stop price is required for STOP_MARKET orders.")

    payload = {
        "symbol": symbol,
        "side": side,
        "type": "STOP_MARKET",
        "quantity": _fmt(qty),
        "stopPrice": _fmt(sp),
    }

    logger.info(
        "Placing STOP_MARKET order: %s %s qty=%s stopPrice=%s",
        side, symbol, _fmt(qty), _fmt(sp),
    )
    raw = client.place_order(**payload)
    result = _parse_response(raw)
    logger.info(
        "STOP_MARKET order placed — orderId=%s status=%s",
        result["orderId"],
        result["status"],
    )
    return result
