"""
Low-level Binance Futures Testnet REST client.
Handles HMAC-SHA256 signing, HTTP communication, and error parsing.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot.client")

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5_000  # ms


class BinanceAPIError(Exception):
    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """
    Thin wrapper around Binance USDT-M Futures Testnet REST endpoints.

    Args:
        api_key:    Testnet API key.
        api_secret: Testnet API secret.
        base_url:   Override base URL (defaults to testnet).
        timeout:    HTTP timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = TESTNET_BASE_URL,
        timeout: int = 10,
    ) -> None:
        self._api_key = api_key
        self._secret = api_secret.encode()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"X-MBX-APIKEY": self._api_key})
        logger.debug("BinanceClient ready (base_url=%s)", self.base_url)

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _now_ms(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: dict[str, Any]) -> str:
        qs = urlencode(params)
        return hmac.new(self._secret, qs.encode(), hashlib.sha256).hexdigest()

    def _add_signature(self, params: dict[str, Any]) -> dict[str, Any]:
        params["timestamp"] = self._now_ms()
        params["recvWindow"] = RECV_WINDOW
        params["signature"] = self._sign(params)
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        signed: bool = False,
    ) -> Any:
        url = f"{self.base_url}{endpoint}"
        params = dict(params or {})
        if signed:
            params = self._add_signature(params)

        logger.debug("→ %s %s  params=%s", method.upper(), endpoint, params)
        try:
            resp = self._session.request(method, url, params=params, timeout=self.timeout)
        except requests.ConnectionError as exc:
            logger.error("Connection error: %s", exc)
            raise
        except requests.Timeout:
            logger.error("Request timed out (%ds) — %s %s", self.timeout, method, url)
            raise

        logger.debug("← HTTP %s  body=%s", resp.status_code, resp.text[:500])

        try:
            data = resp.json()
        except ValueError:
            resp.raise_for_status()
            return resp.text

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            raise BinanceAPIError(data["code"], data.get("msg", "unknown error"))

        resp.raise_for_status()
        return data

    # ------------------------------------------------------------------ #
    # Public API methods                                                   #
    # ------------------------------------------------------------------ #

    def get_exchange_info(self) -> dict:
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_account(self) -> dict:
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(self, **params: Any) -> dict:
        """Place a new order. Pass keyword args that match Binance API fields."""
        logger.debug("Placing order with params: %s", params)
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> dict:
        return self._request(
            "GET",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )
