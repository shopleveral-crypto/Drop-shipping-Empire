---
name: top-down-smc
description: Brad Goh (The Trading Geek) top-down, multi-time-frame supply/demand ("market mechanics" / SMC-style) trading framework, plus trade-management and trading-psychology principles from his video with Sanjeev Sangha, "10 Years of Trading Knowledge in 60 Minutes" (youtube.com/watch?v=cFzxyGRtAis). Use when the user asks about this video or strategy, top-down analysis, break of structure / market shift, supply & demand zones, order blocks, premium/discount, liquidity sweeps, trade management (moving stops, MFE/MAE, partials), or trading psychology (fear, patience, risk size).
---

# Top-down supply/demand framework (Brad Goh)

Source: "10 Years of Trading Knowledge in 60 Minutes", Brad Goh (The Trading Geek) with trading-psychology coach Sanjeev Sangha (1% Club). YouTube `cFzxyGRtAis`, 59:12.
Learned from the full English transcript; the chart visuals were not available.

Content split:
- **00:00–15:00** — the analysis framework.
- **15:00–55:00** — a live demo trade (deliberately random, for teaching) plus discussion of trade management and psychology.

**This is a discretionary framework, not a mechanical rule set.** Zones and structure are judged by eye, so it cannot be backtested exactly the way `orb-15-5-1` was. Any backtest needs explicit definitions first, such as swing points, BOS by candle-body close, and how a zone is drawn.

## 1. Every time frame has one job
| Role | Day trading (Brad) | Scalping | Swing (Sanjeev) |
|---|---|---|---|
| Higher TF: **trend direction**, who's in control | Daily / 4H | 1H | Weekly / Monthly |
| Medium TF: **point of interest (POI)**, *where* to trade | 1H / 15m | 15m | Daily |
| Lower TF: **entry confirmation / trigger** | 5m / 1m | 5m / 1m | 4H / 1H |

Price is fractal: the same patterns appear on every time frame, and lower-time-frame action builds the higher-time-frame structure.

## 2. Higher time frame: trend and swing range
- Read **market structure**:
  - A bullish **break of structure (BOS)** means buyers are in control.
  - Mark the current **swing high and swing low**. This "swing range" is all you care about; ignore older price action.
- Mark the **higher-time-frame zones** inside that range: demand zones in an uptrend, starting from the most extreme one.
- Use a **premium/discount** tool (50% of the swing range):
  - In an uptrend, look for longs at demand zones in the **discount** half.
  - In a downtrend, look for shorts at supply zones in the **premium** half.

## 3. Medium time frame: internal structure and point of interest
- Apply the same structure reading to the internal swings.
- A **market shift** is the first BOS against the prior internal trend. It means the internal structure has flipped.
- **Only candle-body closes count as a BOS.** A wick through a high or low is not a break, so that high or low remains the internal high/low.
- **Trend conflict:** if the higher time frame is bullish but the medium time frame has shifted bearish, Brad trades **with the lower/medium-time-frame flow**. That means shorting the pullback, counter to the higher-time-frame trend. Sanjeev's caveat: with-trend trades give more expansive moves and less chop, so pick what suits your edge and psychology.
- **Point of interest:** an institutional zone, meaning a supply/demand zone, order block or flip zone, where a strong impulsive move started (proof that institutions entered there).
  - Prefer the **extreme** zone.
  - Prefer zones with **liquidity resting just beyond them**, such as equal highs/lows or an obvious swing. Price tends to sweep that liquidity, mitigate the zone, then reverse.
  - Skip the weaker, already-mitigated zones in between.
- **To rejoin the higher-time-frame trend:** wait for a market shift back in its direction, i.e. price takes out the last lower high in an uptrend pullback, then look for longs.

## 4. Lower time frame: entry
- Do nothing until price reaches the POI. **"Waiting is the best position."** Set price alerts at the zone in your pre-market routine instead of watching charts.
- When an alert fires, drop to the lower time frame and wait for your **entry confirmation**. The video does not detail the trigger. In his framework it is the same structure logic on the lower time frame, e.g. a lower-time-frame market shift inside the zone.
- **Risk:reward: minimum 1:2** (Brad).
- **Stop:** at a logical, protected swing high/low where price is unlikely to go.
- **Timing matters:** get in before the London or New York open, when liquidity surges. Off-session trades tend to drift sideways, as the demo trade did.

## 5. Trade management
- **Brad: set and forget.** Leave the charts and let the trade breathe.
  - In a drawdown, **go up to a higher time frame**. Price moves slower there, so you react more calmly and logically (Kahneman's System 1 vs System 2).
- **Moving the stop:** stick to it ~80% of the time. In ~20% of cases discretion is allowed, when the technicals show price will sweep a bit more liquidity first. Accept that you may lose a bit more, and only if it was planned in advance and stays within your risk tolerance. For example, open at $500 risk with a $1,000 tolerance.
- **Sanjeev's alternative:**
  - Wide stops (the stop is the worst-case scenario).
  - Scale into winners only as price moves in your favour; average win > average loss matters more than a fixed risk:reward.
  - Exit manually when the idea is invalidated.
  - Use alerts at structural levels so you don't have to check the chart.
- **The key question:** "If I weren't already in this trade, would I enter here now?" If no, you should be getting out. If yes, it's confirmation to stay.
- **Holding winners longer:** track **MFE** (max favourable excursion: how far price ran after you exited) and **MAE** over a large sample. If data shows a gap, move gradually: take 90% at the normal target and let 10% run, then 80/20, then 50/50.
- **Near the target with strong opposing momentum:** discretion to take profit a few points early.

## 6. Psychology principles
- Clear, objective, **mechanical rules** cure impatience, especially for beginners. Without them every move looks like an opportunity.
- **A good setup should be screamingly obvious** ("hits like a 2x4"). If you have to flip between time frames to convince yourself, there's no trade. If you can't explain the idea in the mirror without cringing, skip it.
- **Fear is a signal, not the problem.** Find its root: fear of being wrong (ego/identity) vs fear of the money. Lowering size only fixes the second.
- **Size by the expected losing streak.** At a 50% win rate you can see ~9 losses in a row over ~500 trades. If you can't stomach 9× your risk, the size is too big.
- **Don't carry the last trade into this one.** An urge to grab profit to offset a previous loss means that loss was too big for you, so reduce size until a loss carries no emotion.
- **Smaller size means more consistency, which means more money long term.** Survive first, then thrive: capital preservation.
- **Question conventional advice.** Build your own playbook from your own data. There's no one-size-fits-all.
- **Growth is outside the comfort zone.** Test changes on data first.
- **Identity:** each trade taken per plan is a "vote" for the disciplined trader you want to be (Be → Do → Have).

## Notes
- **The live trade** was a random 10-lot buy on US30, entered off-session for demonstration. It ended in profit after the CPI release. It is not an example of the strategy.
- **Sponsor segment:** EdgeFlow, Brad's own app (trading-window / max-loss guardrails, code TPT10). Treat it as an advert.
