# BTC Race v4: Deep-Dip Reversal Catcher

## Competition Overview
- **Asset**: CBBTC (Coinbase Wrapped BTC on Solana, Orca Whirlpool), traded against USDC on 1-minute bars with $1,000 starting paper capital.
- **Rules**: Orders decided on a bar's close, filled at the next bar's open. Includes 4 bps fee + 2 bps slippage + price impact per fill. Long only (shorts: false), max 1 open position, max 16 orders/bar.
- **Dev Gate**: The entry races only if its dev grade on the published frozen 24h dev window made a net PnL above $0 after fees.

## Strategy Description
This version (v4) is a deep-dip reversal catcher tuned for falling and choppy market tapes:
- **Signal**: Measures the trailing 60-minute return (`LOOKBACK = 60`). Buys when the return falls into the dip band `[-200, -80]` bps (`DIP_LO_BPS = -200`, `DIP_HI_BPS = -80`).
- **No Regime Veto**: Deliberately omits regime or velocity filters because the largest market reversals initiate from the deepest dips that traditional vetoes exclude.
- **Exits**: Exits on a +110 bps take-profit (`TAKE_PROFIT_BPS = 110`), a 330-batch max hold (`MAX_HOLD_BATCHES = 330`), or a 42 bps trailing stop (`TRAIL_BPS = 42`) once the position achieves positive PnL peak.
- **Guards**: Includes a reset threshold (`RESET_BPS = -10`) and an end guard (`END_GUARD_BARS = 180`) preventing new entries in the final 180 bars of the 1,440-bar window.

## Verified Results
- **New Dev Window (Graded)**: Net PnL **+$5.70** (after all fees), 10 trades, max drawdown ~1.43% (compared to Buy-and-Hold baseline of **-$52.59**).
- **Old Dev Window (Robustness)**: Net PnL **+$13.04** (after all fees), 4 trades.

## Usage
Run the trading bot via standard input/output wire protocol driven by the harness:
```bash
python3 main.py
```
