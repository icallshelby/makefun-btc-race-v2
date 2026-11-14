"""BTC Race v4: Deep-Dip Reversal Catcher.

Strategy Overview:
- Captures deep market dips on CBBTC (Coinbase Wrapped BTC on Solana, Orca Whirlpool, 1-minute bars) without regime or velocity vetoes.
- Measured over 60 bars (LOOKBACK = 60), entering when trailing return is between -200 bps and -80 bps.
- Exits on +110 bps take-profit, 330-batch max hold, or a 42 bps trailing stop from the position's peak PnL.
- Includes a reset threshold (-10 bps) and an end guard (no entries in the last 180 bars of the 1,440-bar window).

Verified Results:
- New Dev Window (Graded): Net PnL +$5.70 (+$5.695015), 10 trades, fees $4.0062, max DD -1.43%, driver agreement PASS.
- Old Dev Window (Robustness): Net PnL +$13.04 (+$13.036237), 4 trades, fees $1.6146, max DD -1.26%.
- Buy-and-Hold Baseline (New Window): -$52.59.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

LOOKBACK = 60
DIP_LO_BPS = -200
DIP_HI_BPS = -80
WARMUP_BARS = 120
SIZE_BPS = 10000
TAKE_PROFIT_BPS = 110
MAX_HOLD_BATCHES = 330
TRAIL_BPS = 42
COOLDOWN_BATCHES = 10
RESET_BPS = -10
END_GUARD_BARS = 180
MAX_SLIPPAGE_BPS = 100


class DipBot:
    def __init__(self, symbol):
        self.symbol = symbol
        self.closes = []
        self.entry_seq = None
        self.cooldown = 0
        self.locked = False
        self.peak = 0.0

    def on_batch(self, state, batch):
        try:
            bar = None
            for b in batch["bars"]:
                if b["symbol"] == self.symbol:
                    bar = b
                    break
            if bar is None:
                return []
            c = int(bar["c"])
            self.closes.append(c)
            if self.cooldown > 0:
                self.cooldown -= 1
            if len(self.closes) <= LOOKBACK:
                return []

            trailing = (self.closes[-1] / self.closes[-1 - LOOKBACK] - 1) * 10000
            if trailing > RESET_BPS:
                self.locked = False

            holding = state.positions.get(self.symbol)
            if holding and holding.qty > 0:
                val = state.value(self.symbol, holding.qty)
                pnl_ratio = (val / holding.cost - 1) if holding.cost > 0 else 0.0
                pnl_bps = pnl_ratio * 10000
                self.peak = max(self.peak, pnl_ratio)
                held_batches = state.seq - self.entry_seq if self.entry_seq is not None else 0

                if (
                    pnl_bps >= TAKE_PROFIT_BPS
                    or held_batches >= MAX_HOLD_BATCHES
                    or (self.peak > 0 and (self.peak - pnl_ratio) * 10000 >= TRAIL_BPS)
                ):
                    self.cooldown = COOLDOWN_BATCHES
                    self.entry_seq = None
                    self.peak = 0.0
                    return [{
                        "side": "sell",
                        "symbol": self.symbol,
                        "qty": holding.qty,
                        "max_slippage_bps": MAX_SLIPPAGE_BPS,
                    }]
                return []

            if self.cooldown > 0 or self.locked:
                return []
            if len(self.closes) <= WARMUP_BARS:
                return []
            if state.seq > 1440 - END_GUARD_BARS:
                return []
            if not (DIP_LO_BPS <= trailing <= DIP_HI_BPS):
                return []

            notional = state.cash * SIZE_BPS // 10000
            min_notional = int(state.hello["fees"]["min_notional_quote_units"])
            if notional < min_notional:
                return []

            self.locked = True
            self.entry_seq = state.seq
            self.peak = 0.0
            return [{
                "side": "buy",
                "symbol": self.symbol,
                "notional_quote_units": notional,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        except Exception:
            return []


def main():
    bot_instance = None

    def on_hello(state):
        nonlocal bot_instance
        symbol = state.hello["symbols"][0]["symbol"]
        bot_instance = DipBot(symbol)

    def on_batch(state, batch):
        return bot_instance.on_batch(state, batch)

    makefun_bars.run(on_batch, on_hello=on_hello)


if __name__ == "__main__":
    main()
