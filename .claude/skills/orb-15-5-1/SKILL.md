---
name: orb-15-5-1
description: The 15-5-1 Opening Range scalping strategy (Jdub Trades, "I Finally Reveal My Most Effective Scalping Strategy", youtube.com/watch?v=UKWAgm-HDYY). Use when the user asks about this strategy, the opening range / ORB, the "15 minute 5 minute 1 minute" method, wants to apply it to a chart, analyse a trade with it, or backtest it on a symbol. Contains the exact rules, the examples from the video, how they were turned into code, and past backtest results.
---

# 15-5-1 Opening Range strategy

Source: Jdub Trades, YouTube `UKWAgm-HDYY` (23:35, published 2026-11-15). Learned from the full English transcript; the chart visuals were not available.
Traded by the author on NQ / ES futures (also SPY, QQQ, US100). Window: first ~2 hours after the New York open.

## Three time frames, each with one job
| Time frame | Job |
|---|---|
| 15m | Defines the **opening range** (first 15m candle after 09:30 New York time) |
| 5m | **Confirmation**: a 5m candle must CLOSE outside the range |
| 1m | **Entry**: retest of the broken level + rejection |

One 15m candle = three 5m candles = fifteen 1m candles.

## Rules
1. **Mark the range.** On the 15m chart, mark the high and low of the first candle after 09:30 New York time (the New York session has the most volume and liquidity).
2. **Wait for a 5m close outside the range.**
   - Close above the high: look for longs. Close below the low: look for shorts.
   - A wick through the level that closes back inside does not count. This is the core filter that avoids morning fake-outs ("price acceptance").
   - With no 5m close outside the range, there is no trade and you don't drop to the 1m chart.
3. **Drop to the 1m chart and wait for the retest.**
   - Price comes back to the broken level (the range low for shorts, the range high for longs).
   - Look for weak or strong price action at the level: rejection wicks, or a candle closing beyond the previous candle's low or high.
   - Don't blindly enter at the level; wait for the buyers or sellers to show up.
   - If a 1m candle closes back inside the range, there is no trade that day.
4. **Plan the trade.**
   - Entry: as close to the level as possible, for a tight risk.
   - Stop: beyond 1m market structure (the swing high/low of the retest).
   - Target: a fixed 1:2 risk:reward at minimum, or a higher-time-frame key level / low or high of day. You can trail the rest.
   - If the stop is far from the level, skip the trade, or take 1:1 and move the stop to break-even.

## Additional points from the author
- **Hard stop vs mental stop.** He uses a mental stop (exits on candle closes), and says it only suits disciplined traders. With options a mental stop is natural; with futures or stocks a fixed stop works.
- **Be aggressive only with a reason.** Skipping the 5m confirmation is only justified by a higher-time-frame level or a news catalyst. Otherwise be patient.
- **Choppy days.** Days that just range inside the 15m range are no-trade days. The filter keeps you out of chop.
- **Results shown in the video.** Six chart examples: one no-trade day, one loss (entry too far from the level so the 1:2 wasn't reached), and four wins. These are curated examples, not statistics.

## Mechanical version used for backtests
Code: `backtests/orb_backtest.py` (Python, Binance 1m zips) and `backtests/orb_15_5_1_eth.pine` (TradingView).
- Opening range = high/low of 09:30–09:45 NY.
- Confirmation = first 5m close outside the range, until 11:30 NY.
- Entry = the first 1m bar after confirmation that touches the level and closes on the breakout side; enter at its close.
- Cancel = a 1m close back inside the range.
- Stop = the pullback extreme since confirmation. Target = 2R.
- Close any open trade at 16:00 NY. One trade per day, weekdays only.
- If the stop and target are hit in the same bar, assume the stop.

## Backtest results so far
- **ETH (BINANCE:ETHUSDT), last 300 trades, 2023-07 → 2026-11.**
  - Before fees: 33.3% wins, 0.00R per trade. Exactly break-even, so no edge.
  - After 0.05%/side fees: −2.5R per trade. The median stop is only 0.10% of price, about the same as the round-trip fee.
  - Filtering for stops of at least 0.2–0.3% leaves too few trades, still around 0R.
  - Verdict: not tradable on ETH. Trades are in `backtests/orb_trades.csv`.
- **SNDK, 3 months of 5m data (TradingView plan limit), 2026-08 → 2026-11.**
  - 10 trades, 7 wins, +3.4% at 1% risk, PF 2.2.
  - Too small a sample to conclude anything.
  - A 300-day test needs 1m data (Polygon free key, or TradingView Premium Deep Backtesting).
- **NQ / ES (the author's own markets): not tested yet.** This is the fair test of the strategy.

When answering about this strategy, state these results honestly. The video shows curated winners; the only large sample so far shows no edge.
