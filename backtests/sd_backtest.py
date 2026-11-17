"""Backtest: TradingLab 3-step strategy (valid-low structure + supply/demand + RR >= 2.5).

Mechanical definitions (the video leaves these open):
- Swing pivot: high/low with PIVOT bars on each side lower/higher (confirmed PIVOT bars later).
- Structure ("valid low" rule): in an uptrend the protected (valid) low is the lowest low
  of the leg that broke the previous swing high (close above it). Trend flips only on a
  close beyond the protected level. Mirror for downtrends.
- Impulse candle: range >= IMPULSE x ATR(14) and body >= 60% of range, in trend direction.
  Zone = high..low of the candle right before it. Zones only in trend direction.
- Entry: limit at the zone edge (top of demand / bottom of supply) on first return.
  Stop: other side of the zone. Target: most extreme price since the zone formed.
  Skip if RR < 2.5. Each zone is used once; zones die if price closes through them
  or the trend flips. One open trade at a time.
- Same-bar stop and target: assume stop. Fees per side as given.

Usage: python3 sd_backtest.py <dir with SYMBOL/ subdirs of Binance 15m zips> [n_trades]
"""
import csv
import io
import sys
import zipfile
from pathlib import Path

PIVOT = 3
IMPULSE = 2.0
MIN_RR = 2.5
FEES = (0.0005, 0.0002)
TFS = {"15m": 1, "1h": 4, "4h": 16}


def load15(folder):
    rows = []
    for zp in sorted(Path(folder).glob("*.zip")):
        with zipfile.ZipFile(zp) as z:
            for name in z.namelist():
                with z.open(name) as f:
                    for r in csv.reader(io.TextIOWrapper(f)):
                        if r and r[0].isdigit():
                            t = int(r[0])
                            t = t // 1000 if t > 1e14 else t
                            rows.append((t, float(r[1]), float(r[2]), float(r[3]), float(r[4])))
    rows.sort()
    out, last = [], None
    for r in rows:
        if r[0] != last:
            out.append(r)
            last = r[0]
    return out


def resample(bars, k):
    if k == 1:
        return bars
    ms = k * 15 * 60 * 1000
    out, cur = [], None
    for t, o, h, l, c in bars:
        b = t - t % ms
        if cur and cur[0] == b:
            cur = [b, cur[1], max(cur[2], h), min(cur[3], l), c]
        else:
            if cur:
                out.append(tuple(cur))
            cur = [b, o, h, l, c]
    out.append(tuple(cur))
    return out


def backtest(bars):
    n = len(bars)
    T, O, H, L, C = zip(*bars)
    tr = [H[0] - L[0]] + [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) for i in range(1, n)]
    atr, a = [], tr[0]
    for x in tr:
        a = a + (x - a) / 14
        atr.append(a)

    trend = 0            # 1 up, -1 down
    prev_ext = None      # last confirmed swing in trend direction (level to break)
    prev_ext_i = None
    protect = None       # valid low (uptrend) / valid high (downtrend)
    protect_i = None
    zones = []           # dicts: dir, top, bot, i
    pos = None
    trades = []

    for i in range(1, n):
        # ---- manage open position
        if pos:
            d = pos["dir"]
            hit_stop = L[i] <= pos["stop"] if d == 1 else H[i] >= pos["stop"]
            hit_tgt = H[i] >= pos["tgt"] if d == 1 else L[i] <= pos["tgt"]
            if hit_stop or hit_tgt:
                px = pos["stop"] if hit_stop else pos["tgt"]
                pos.update(exit=px, exit_t=T[i], win=not hit_stop)
                trades.append(pos)
                pos = None

        # ---- confirm pivots (bar j = i - PIVOT)
        j = i - PIVOT
        if j >= PIVOT:
            ph = all(H[j] > H[j - k] and H[j] >= H[j + k] for k in range(1, PIVOT + 1))
            pl = all(L[j] < L[j - k] and L[j] <= L[j + k] for k in range(1, PIVOT + 1))
            if trend == 0:
                if ph:
                    prev_ext, prev_ext_i = H[j], j
                    trend = 1
                    protect = min(L[max(0, j - 20):j + 1])
                    protect_i = j
            elif trend == 1 and ph:
                prev_ext, prev_ext_i = H[j], j
            elif trend == -1 and pl:
                prev_ext, prev_ext_i = L[j], j

        if trend == 0:
            continue

        # ---- structure: break of previous swing -> new protected level; break of protected -> flip
        if trend == 1:
            if C[i] < protect:
                hi_i = max(range(protect_i, i + 1), key=lambda k: H[k])
                trend, protect, protect_i, prev_ext, prev_ext_i = -1, H[hi_i], hi_i, None, None
                zones = []
            elif prev_ext is not None and C[i] > prev_ext:
                lo_i = min(range(prev_ext_i, i + 1), key=lambda k: L[k])
                protect, protect_i, prev_ext = L[lo_i], lo_i, None
        else:
            if C[i] > protect:
                lo_i = min(range(protect_i, i + 1), key=lambda k: L[k])
                trend, protect, protect_i, prev_ext, prev_ext_i = 1, L[lo_i], lo_i, None, None
                zones = []
            elif prev_ext is not None and C[i] < prev_ext:
                hi_i = max(range(prev_ext_i, i + 1), key=lambda k: H[k])
                protect, protect_i, prev_ext = H[hi_i], hi_i, None

        # ---- entries on existing zones (before adding today's zone)
        alive = []
        for z in zones:
            d = z["dir"]
            if (d == 1 and C[i] < z["bot"]) or (d == -1 and C[i] > z["top"]):
                if pos is None:
                    pass
                continue  # closed through -> dead (and if it touched, handled below already)
            touched = L[i] <= z["top"] if d == 1 else H[i] >= z["bot"]
            if touched and i > z["i"] + 1:
                if pos is None:
                    entry = min(O[i], z["top"]) if d == 1 else max(O[i], z["bot"])
                    stop = z["bot"] if d == 1 else z["top"]
                    tgt = max(H[z["i"]:i]) if d == 1 else min(L[z["i"]:i])
                    risk = (entry - stop) * d
                    if risk > 0 and (tgt - entry) * d / risk >= MIN_RR:
                        pos = dict(dir=d, entry=entry, stop=stop, tgt=tgt, entry_t=T[i])
                        if (L[i] <= stop) if d == 1 else (H[i] >= stop):   # same bar stop
                            pos.update(exit=stop, exit_t=T[i], win=False)
                            trades.append(pos)
                            pos = None
                continue  # zone used (taken or skipped)
            alive.append(z)
        zones = alive

        # ---- new zone from impulse candle
        rng = H[i] - L[i]
        body = C[i] - O[i]
        if rng >= IMPULSE * atr[i - 1] and abs(body) >= 0.6 * rng and (1 if body > 0 else -1) == trend:
            zones.append(dict(dir=trend, top=H[i - 1], bot=L[i - 1], i=i))
            zones = zones[-10:]
    return trades


def summarize(trades, fee):
    rs = []
    for t in trades:
        risk = abs(t["entry"] - t["stop"])
        g = (t["exit"] - t["entry"]) * t["dir"] / risk
        rs.append(g - fee * (t["entry"] + t["exit"]) / risk)
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    eq = peak = mdd = 0.0
    comp = 1.0
    streak = worst = 0
    for r in rs:
        eq += r
        peak = max(peak, eq)
        mdd = max(mdd, peak - eq)
        comp *= max(0.0, 1 + 0.01 * r)
        streak = streak + 1 if r <= 0 else 0
        worst = max(worst, streak)
    return dict(n=len(rs), win=len(wins) / len(rs) * 100 if rs else 0, total_r=sum(rs),
                avg_r=sum(rs) / len(rs) if rs else 0,
                pf=sum(wins) / -sum(losses) if losses and sum(losses) < 0 else float("inf"),
                mdd_r=mdd, streak=worst, comp=(comp - 1) * 100)


def main():
    root = Path(sys.argv[1])
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 350
    from datetime import datetime, timezone
    day = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")
    results = []
    out_rows = []
    for sym_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        base = load15(sym_dir)
        for tf, k in TFS.items():
            tr = backtest(resample(base, k))[-want:]
            if not tr:
                continue
            s0 = summarize(tr, 0.0)
            s5, s2 = (summarize(tr, f) for f in FEES)
            results.append((sym_dir.name, tf, day(tr[0]["entry_t"]), day(tr[-1]["entry_t"]), s0, s5, s2))
            for t in tr:
                out_rows.append(dict(symbol=sym_dir.name, tf=tf, side="long" if t["dir"] == 1 else "short",
                                     entry_time=day(t["entry_t"]), entry=t["entry"], stop=t["stop"],
                                     target=t["tgt"], exit=t["exit"], win=t["win"]))
    hdr = f"{'symbol':8} {'tf':4} {'period':23} {'n':>4} {'win%':>5} | {'R gross':>8} | {'R @0.05%':>8} {'PF':>5} {'maxDD':>6} {'+%1risk':>8} | {'R @0.02%':>8}"
    print(hdr)
    print("-" * len(hdr))
    for sym, tf, a, b, s0, s5, s2 in sorted(results, key=lambda x: -x[5]["total_r"]):
        print(f"{sym:8} {tf:4} {a}..{b} {s5['n']:>4} {s0['win']:5.1f} | {s0['total_r']:8.1f} | "
              f"{s5['total_r']:8.1f} {s5['pf']:5.2f} {s5['mdd_r']:6.1f} {s5['comp']:7.1f}% | {s2['total_r']:8.1f}")
    out = Path(__file__).with_name("sd_trades.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    print("\nTrades written to", out)


if __name__ == "__main__":
    main()
