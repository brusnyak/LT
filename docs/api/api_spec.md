# API Specifications

## 1. Data Endpoints

### `GET /api/data/candles`
Fetch OHLCV data for a specific pair and timeframe.
-   **Params**:
    -   `pair` (str): e.g., "EURUSD"
    -   `timeframe` (str): e.g., "5m", "4h"
    -   `limit` (int): Number of candles (default 1000)
-   **Response**:
    ```json
    [
        {"time": 1625097600, "open": 1.1850, "high": 1.1860, "low": 1.1840, "close": 1.1855, "volume": 100},
        ...
    ]
    ```

## 2. Strategy Endpoints

### `GET /api/strategy/range-4h`
Analyze data and return 4H Range levels and signals.
-   **Params**:
    -   `pair` (str): e.g., "EURUSD"
-   **Response**:
    ```json
    {
        "ranges": [
            {
                "date": "2023-10-25",
                "high": 1.0580,
                "low": 1.0520,
                "start_time": 1698206400, // 00:00 NY
                "end_time": 1698220800    // 04:00 NY
            }
        ],
        "signals": [
            {
                "time": 1698240000,
                "type": "LONG",
                "price": 1.0515,
                "sl": 1.0500,
                "tp": 1.0545,
                "reason": "Re-entry after breakdown"
            }
        ]
    }
    ```

## 3. Account Endpoints

### `GET /api/account`
Get current account state.
-   **Response**:
    ```json
    {
        "balance": 20000.0,
        "equity": 20000.0,
        "daily_loss": 0.0,
        "trades_today": 0
    }
    ```

### `POST /api/account/reset`
Reset account to initial state ($20k).
