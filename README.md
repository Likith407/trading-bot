# Binance Futures Testnet — Trading Bot

A clean, structured Python CLI application for placing orders on the
**Binance USDT-M Futures Testnet**.

Supports **MARKET**, **LIMIT**, and **STOP_MARKET** (bonus) order types with
full input validation, structured logging, and clear output.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (signing, HTTP, error handling)
│   ├── orders.py          # Order placement logic (market / limit / stop)
│   ├── validators.py      # Input validation helpers
│   └── logging_config.py  # Logging setup (file + console)
├── cli.py                 # CLI entry point (argparse)
├── logs/                  # Auto-created; one timestamped .log per run
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get Testnet Credentials

1. Register at <https://testnet.binancefuture.com>
2. Go to **API Management** → generate a new key pair
3. Copy your **API Key** and **Secret Key**

### 2. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set Credentials

```bash
# Linux / macOS
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"

# Windows (PowerShell)
$Env:BINANCE_API_KEY="your_api_key_here"
$Env:BINANCE_API_SECRET="your_api_secret_here"
```

Alternatively, pass `--api-key` / `--api-secret` flags directly on the command line.

---

## Usage

```
python cli.py <command> [options]
```

### Commands

| Command  | Description                        |
|----------|------------------------------------|
| `market` | Place a MARKET order               |
| `limit`  | Place a LIMIT order                |
| `stop`   | Place a STOP_MARKET order (bonus)  |

### Common flags (all commands)

| Flag          | Required | Description                        |
|---------------|----------|------------------------------------|
| `--symbol`    | ✅       | Trading pair, e.g. `BTCUSDT`       |
| `--side`      | ✅       | `BUY` or `SELL`                    |
| `--quantity`  | ✅       | Order quantity in base asset        |
| `--log-dir`   | ❌       | Log directory (default: `logs/`)   |

---

## How to Run — Examples

### Market BUY

```bash
python cli.py market --symbol BTCUSDT --side BUY --quantity 0.01
```

**Output:**
```
────────────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────
  Type    : MARKET
  Symbol  : BTCUSDT
  Side    : BUY
  Quantity: 0.01
────────────────────────────────────────────────────────

────────────────────────────────────────────────────────
  ORDER RESPONSE
────────────────────────────────────────────────────────
  Order ID        : 3865429871
  Symbol          : BTCUSDT
  Side            : BUY
  Type            : MARKET
  Status          : FILLED
  Orig Qty        : 0.01
  Executed Qty    : 0.01
  Avg Price       : 96423.50
────────────────────────────────────────────────────────
  ✅  Order placed successfully!
```

---

### Limit SELL

```bash
python cli.py limit --symbol BTCUSDT --side SELL --quantity 0.01 --price 98000
```

Optional: `--tif GTC` (default) | `IOC` | `FOK`

---

### Stop-Market SELL (Bonus)

```bash
python cli.py stop --symbol BTCUSDT --side SELL --quantity 0.01 --stop-price 93000
```

Triggers a market SELL when price drops to 93 000.

---

### Using explicit credentials instead of env vars

```bash
python cli.py market \
  --api-key YOUR_KEY \
  --api-secret YOUR_SECRET \
  --symbol ETHUSDT \
  --side BUY \
  --quantity 0.1
```

---

## Logging

Every run creates a timestamped log file under `logs/`:

```
logs/trading_bot_20250115_102301.log
```

- **Console** — INFO level and above (request summary + result)
- **File** — DEBUG level (full request params, raw API response, errors)

Sample log files for a MARKET and LIMIT order are included in `logs/`.

---

## Error Handling

| Error type            | Behaviour                                      |
|-----------------------|------------------------------------------------|
| Invalid input         | `ValidationError` — clear message, exit 1      |
| Binance API error     | `BinanceAPIError` — code + message, exit 1     |
| Network / timeout     | `requests` exception — logged + exit 1         |
| Missing credentials   | Early exit with instructions                   |

---

## Assumptions

- **USDT-M Futures Testnet only** — base URL is hardcoded to `https://testnet.binancefuture.com`
- Quantity precision must satisfy the symbol's `LOT_SIZE` filter on the exchange; the bot forwards your value as-is and Binance will reject it with a clear error if it is wrong
- `timeInForce` defaults to `GTC` for LIMIT orders
- The bot uses the **one-way position mode** (default testnet setting); if you have enabled hedge mode you must add `positionSide` yourself
