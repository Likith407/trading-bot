#!/usr/bin/env python3
"""
Binance Futures Testnet — Trading Bot CLI
==========================================

Usage examples:
  python cli.py market  --symbol BTCUSDT --side BUY  --quantity 0.01
  python cli.py limit   --symbol BTCUSDT --side SELL --quantity 0.01 --price 95000
  python cli.py stop    --symbol BTCUSDT --side SELL --quantity 0.01 --stop-price 93000

API credentials are read from environment variables:
  BINANCE_API_KEY
  BINANCE_API_SECRET

Or supplied via --api-key / --api-secret flags.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logging
from bot.orders import (
    place_market_order,
    place_limit_order,
    place_stop_market_order,
)
from bot.validators import ValidationError


# ------------------------------------------------------------------ #
# Output helpers                                                       #
# ------------------------------------------------------------------ #

SEPARATOR = "─" * 56


def _print_request_summary(order_type: str, args: argparse.Namespace) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  ORDER REQUEST SUMMARY")
    print(SEPARATOR)
    print(f"  Type    : {order_type}")
    print(f"  Symbol  : {args.symbol.upper()}")
    print(f"  Side    : {args.side.upper()}")
    print(f"  Quantity: {args.quantity}")
    if hasattr(args, "price") and args.price:
        print(f"  Price   : {args.price}")
    if hasattr(args, "stop_price") and args.stop_price:
        print(f"  StopPx  : {args.stop_price}")
    print(SEPARATOR)


def _print_order_result(result: dict) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  ORDER RESPONSE")
    print(SEPARATOR)
    fields = [
        ("Order ID",      "orderId"),
        ("Symbol",        "symbol"),
        ("Side",          "side"),
        ("Type",          "type"),
        ("Status",        "status"),
        ("Orig Qty",      "origQty"),
        ("Executed Qty",  "executedQty"),
        ("Avg Price",     "avgPrice"),
        ("Limit Price",   "price"),
        ("Stop Price",    "stopPrice"),
        ("Time-in-Force", "timeInForce"),
    ]
    for label, key in fields:
        val = result.get(key)
        if val not in (None, "", "0", "0.00000000"):
            print(f"  {label:<16}: {val}")
    print(SEPARATOR)
    print(f"  ✅  Order placed successfully!\n")


def _print_error(message: str) -> None:
    print(f"\n  ❌  {message}\n", file=sys.stderr)


# ------------------------------------------------------------------ #
# Sub-command handlers                                                 #
# ------------------------------------------------------------------ #

def cmd_market(client: BinanceClient, args: argparse.Namespace) -> None:
    _print_request_summary("MARKET", args)
    result = place_market_order(client, args.symbol, args.side, args.quantity)
    _print_order_result(result)


def cmd_limit(client: BinanceClient, args: argparse.Namespace) -> None:
    if args.price is None:
        _print_error("--price is required for LIMIT orders.")
        sys.exit(1)
    _print_request_summary("LIMIT", args)
    result = place_limit_order(
        client, args.symbol, args.side, args.quantity, args.price,
        time_in_force=args.tif,
    )
    _print_order_result(result)


def cmd_stop(client: BinanceClient, args: argparse.Namespace) -> None:
    if args.stop_price is None:
        _print_error("--stop-price is required for STOP_MARKET orders.")
        sys.exit(1)
    _print_request_summary("STOP_MARKET", args)
    result = place_stop_market_order(
        client, args.symbol, args.side, args.quantity, args.stop_price
    )
    _print_order_result(result)


# ------------------------------------------------------------------ #
# Argument parsing                                                     #
# ------------------------------------------------------------------ #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Binance Futures Testnet — Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Global credential flags
    parser.add_argument("--api-key",    default=None, help="Binance API key (or set BINANCE_API_KEY)")
    parser.add_argument("--api-secret", default=None, help="Binance API secret (or set BINANCE_API_SECRET)")
    parser.add_argument("--log-dir",    default="logs", help="Directory for log files (default: logs/)")

    sub = parser.add_subparsers(dest="command", required=True)

    # Shared order arguments
    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--symbol",   required=True, help="Trading pair, e.g. BTCUSDT")
        p.add_argument("--side",     required=True, choices=["BUY", "SELL", "buy", "sell"])
        p.add_argument("--quantity", required=True, type=float, help="Order quantity")

    # market
    m = sub.add_parser("market", help="Place a MARKET order")
    add_common(m)

    # limit
    lim = sub.add_parser("limit", help="Place a LIMIT order")
    add_common(lim)
    lim.add_argument("--price", type=float, required=True, help="Limit price")
    lim.add_argument("--tif",   default="GTC", choices=["GTC", "IOC", "FOK"], help="Time-in-force (default: GTC)")

    # stop (bonus)
    stp = sub.add_parser("stop", help="Place a STOP_MARKET order (bonus)")
    add_common(stp)
    stp.add_argument("--stop-price", type=float, required=True, dest="stop_price", help="Trigger price")

    return parser


# ------------------------------------------------------------------ #
# Entry point                                                          #
# ------------------------------------------------------------------ #

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Logging
    logger = setup_logging(log_dir=args.log_dir)

    # Credentials — flags take priority over env vars
    api_key    = args.api_key    or os.getenv("BINANCE_API_KEY",    "")
    api_secret = args.api_secret or os.getenv("BINANCE_API_SECRET", "")

    if not api_key or not api_secret:
        _print_error(
            "API credentials missing.\n"
            "  Set BINANCE_API_KEY / BINANCE_API_SECRET env vars\n"
            "  or pass --api-key / --api-secret flags."
        )
        sys.exit(1)

    client = BinanceClient(api_key=api_key, api_secret=api_secret)

    dispatch = {
        "market": cmd_market,
        "limit":  cmd_limit,
        "stop":   cmd_stop,
    }

    try:
        dispatch[args.command](client, args)
    except ValidationError as exc:
        logger.error("Validation error: %s", exc)
        _print_error(f"Validation error: {exc}")
        sys.exit(1)
    except BinanceAPIError as exc:
        logger.error("Binance API error [%s]: %s", exc.code, exc.message)
        _print_error(f"Binance API error [{exc.code}]: {exc.message}")
        sys.exit(1)
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        _print_error(f"Unexpected error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
