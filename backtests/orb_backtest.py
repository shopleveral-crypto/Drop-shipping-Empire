"""Backtest: Opening Range 15m -> 5m close confirmation -> 1m retest entry.

Rules (from Jdub Trades' "Most Effective Scalping Strategy"):
 1. Mark high/low of the first 15m candle after the New York open (09:30-09:45 NY).
 2. Wait for a 5m candle to CLOSE above the high (long) or below the low (short).
    Only the first such close of the day counts.
 3. On the 1m chart, wait for price to come back and retest the broken level:
    - long: a 1m bar trades down to the OR high but closes above it -> enter at close
    - short: a 1m bar trades up to the OR low but closes below it -> enter at close
    - a 1m close back inside the range cancels the setup for the day
    Stop = extreme of the pullback since confirmation (1m market structure).
    Target = fixed 1:2 risk:reward.
 Entries allowed until 11:30 NY; open trades are closed at 16:00 NY.
 Weekdays only (the NY stock-market open has no meaning on weekends).

Usage: python3 orb_backtest.py <dir with Binance ETHUSDT-1m-*.zip> [n_trades]
"""
import csv
import io
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
RR = 2.0
FEE = 0.0005          # 0.05% per side
LAST_ENTRY = 1130
FLAT = 1600


def load(data_dir):
    days = defaultdict(list)
    for zp in sorted(Path(data_dir).glob("*.zip")):
        with zipfile.ZipFile(zp) as z:
            for name in z.namelist():
                with z.open(name) as f:
                    for row in csv.reader(io.TextIOWrapper(f)):
                        if not row or not row[0].isdigit():
                            continue
                        t = int(row[0])
                        t = t / 1e6 if t > 1e14 else t / 1e3   # us (2025+) or ms
                        dt = datetime.fromtimestamp(t, timezone.utc).astimezone(NY)
                        hm = dt.hour * 100 + dt.minute
                        if dt.weekday() >= 5 or hm < 930 or hm >= FLAT:
                            continue
                        days[dt.date()].append(
                            (hm, dt.minute, float(row[1]), float(row[2]), float(row[3]), float(row[4])))
    for d in days:
        days[d].sort()
    return days


def run_day(bars):
    orb = [b for b in bars if b[0] < 945]
    if len(orb) < 15:
        return None
    orh = max(b[3] for b in orb)
    orl = min(b[4] for b in orb)
    rest = [b for b in bars if b[0] >= 945]
    direction = 0
    arm = None
    ext = None
    for i, (hm, mi, o, h, l, c) in enumerate(rest):
        if direction == 0:
            if hm >= LAST_ENTRY:
                return None
            if mi % 5 == 4:                     # this 1m bar closes a 5m candle
                if c > orh:
                    direction, arm, ext = 1, i, l
                elif c < orl:
                    direction, arm, ext = -1, i, h
            continue
        if i == arm:
            continue
        ext = min(ext, l) if direction == 1 else max(ext, h)
        if hm >= LAST_ENTRY:
            return None
        if direction == 1:
            if c < orh:
                return None
            if l <= orh:
                return manage(rest[i + 1:], 1, c, ext, hm, orh, orl)
        else:
            if c > orl:
                return None
            if h >= orl:
                return manage(rest[i + 1:], -1, c, ext, hm, orh, orl)
    return None


def manage(after, d, entry, stop, entry_hm, orh, orl):
    risk = (entry - stop) * d
    if risk <= 0:
        return None
    target = entry + d * RR * risk
    exit_px, reason = None, "EOD"
    for hm, mi, o, h, l, c in after:
        hit_stop = l <= stop if d == 1 else h >= stop
        hit_tgt = h >= target if d == 1 else l <= target
        if hit_stop:                            # same-bar ambiguity -> assume the stop
            exit_px, reason = stop, "stop"
            break
        if hit_tgt:
            exit_px, reason = target, "target"
            break
        exit_px = c
    if exit_px is None:
        return None
    gross_r = (exit_px - entry) * d / risk
    fee_r = FEE * (entry + exit_px) / risk
    return dict(side="long" if d == 1 else "short", entry=entry, stop=stop, target=target,
                exit=exit_px, reason=reason, entry_hm=entry_hm, risk_pct=risk / entry * 100,
                or_pct=(orh - orl) / entry * 100, gross_r=gross_r, net_r=gross_r - fee_r)


def stats(trades, key):
    rs = [t[key] for t in trades]
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    eq, peak, mdd = 0.0, 0.0, 0.0
    comp = 1.0
    streak = worst = 0
    for r in rs:
        eq += r
        peak = max(peak, eq)
        mdd = max(mdd, peak - eq)
        comp *= 1 + 0.01 * r
        streak = streak + 1 if r <= 0 else 0
        worst = max(worst, streak)
    return dict(n=len(rs), win_rate=len(wins) / len(rs) * 100, total_r=sum(rs), avg_r=sum(rs) / len(rs),
                pf=(sum(wins) / -sum(losses)) if losses and sum(losses) else float("inf"),
                max_dd_r=mdd, worst_losing_streak=worst, compounded_1pct=(comp - 1) * 100)


def main():
    data_dir = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    days = load(data_dir)
    trades = []
    for d in sorted(days):
        t = run_day(days[d])
        if t:
            t["date"] = d.isoformat()
            trades.append(t)
    trades = trades[-n:]
    print(f"Days scanned: {len(days)} | trades used: {len(trades)} "
          f"({trades[0]['date']} -> {trades[-1]['date']})")
    for key, label in (("gross_r", "Before fees"), ("net_r", "After 0.05%/side fees")):
        print(f"\n== {label}")
        for k, v in stats(trades, key).items():
            print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")
    for side in ("long", "short"):
        sub = [t for t in trades if t["side"] == side]
        if sub:
            s = stats(sub, "net_r")
            print(f"\n{side}: n={s['n']} win={s['win_rate']:.1f}% totalR={s['total_r']:.1f} avgR={s['avg_r']:.3f}")
    reasons = defaultdict(int)
    for t in trades:
        reasons[t["reason"]] += 1
    print("\nExit reasons:", dict(reasons))
    rp = sorted(t["risk_pct"] for t in trades)
    print(f"Median stop distance: {rp[len(rp)//2]:.3f}% of price | fee round-trip = {2*FEE*100:.2f}%")
    out = Path(__file__).with_name("orb_trades.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(trades[0].keys()))
        w.writeheader()
        w.writerows(trades)
    print("Trades written to", out)


if __name__ == "__main__":
    main()
