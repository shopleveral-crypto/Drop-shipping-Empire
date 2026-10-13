"""Builds the paid-social ad videos from the raw phone clips.

Pipeline: trim/speed/zoom/grade each shot -> end card -> concat -> overlay
motion graphics (rendered by Chromium) -> original music + SFX -> export
the versions listed under "exports" in timeline.json (9:16 or 4:5,
with the full mix or SFX only).

Usage: python3 build.py --work <scratch dir> [--fonts <dir>]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source")
OUT = os.path.join(HERE, "output")
FONTS = {
    "Rubik.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/rubik/Rubik%5Bwght%5D.ttf",
    "Heebo.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/heebo/Heebo%5Bwght%5D.ttf",
}
GRADES = {
    "base": "eq=contrast=1.06:saturation=1.22:gamma=1.03,colorbalance=rm=0.03:bm=-0.03",
    "dim": "eq=contrast=1.05:saturation=1.10:gamma=1.17:brightness=0.015,colorbalance=rm=-0.01:bm=0.02",
}
FINISH = "vignette=angle=0.42,unsharp=5:5:0.45,setsar=1,format=yuv420p"
X264 = ["-c:v", "libx264", "-preset", "fast", "-crf", "12", "-pix_fmt", "yuv420p"]


def run(cmd):
    print("+", " ".join(cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True)


def zoom_scale(dur, drift, punch=0.12):
    # Punch-in at the cut that settles over 0.3s, then a slow push (drift > 0) or pull (drift < 0).
    ramp = f"t/{dur}" if drift >= 0 else f"(1-t/{dur})"
    z = f"(1+{abs(drift)}*{ramp}+{punch}*pow(max(0\\,1-t/0.3)\\,2))"
    return (f"scale=w='2*trunc(540*{z})':h='2*trunc(960*{z})':eval=frame:flags=lanczos,"
            f"crop=1080:1920")


def build_segments(tl, work):
    fps = tl["fps"]
    paths = []
    for i, s in enumerate(tl["segments"]):
        frames = round(s["end"] * fps) - round(s["start"] * fps)
        dur = frames / fps
        speed = (s["out"] - s["in"]) / dur
        drift = 0.05 if i % 2 == 0 else -0.05
        vf = (f"setpts=(PTS-STARTPTS)/{speed:.5f},fps={fps},tpad=stop_mode=clone:stop_duration=1,"
              f"{zoom_scale(dur, drift)},{GRADES[s['grade']]},{FINISH}")
        out = os.path.join(work, f"seg{i}.mp4")
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(s["in"]), "-i", os.path.join(SRC, s["src"]),
             "-vf", vf, "-frames:v", str(frames), "-an", *X264, out])
        paths.append(out)

    ec = tl["endcard"]
    frames = round(ec["end"] * fps) - round(ec["start"] * fps)
    dur = frames / fps
    still = os.path.join(work, "endcard.png")
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(ec["at"]), "-i", os.path.join(SRC, ec["src"]),
         "-frames:v", "1", still])
    out = os.path.join(work, "seg_end.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(fps), "-i", still,
         "-vf", f"{zoom_scale(dur, 0.04, punch=0.05)},{GRADES['base']},{FINISH}",
         "-frames:v", str(frames), *X264, out])
    paths.append(out)

    listfile = os.path.join(work, "concat.txt")
    with open(listfile, "w") as f:
        f.writelines(f"file '{p}'\n" for p in paths)
    base = os.path.join(work, "base.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", base])
    return base


def loudnorm(src, dst, target=-14.0):
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json",
         "-f", "null", "-"], capture_output=True, text=True, check=True).stderr
    m = json.loads(probe[probe.rindex("{"):])
    af = (f"loudnorm=I={target}:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:"
          f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"offset={m['target_offset']},aresample=48000")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-ar", "48000", dst])


def build_audio(tl, work):
    music, sfx = os.path.join(work, "music.wav"), os.path.join(work, "sfx.wav")
    run([sys.executable, "-I", os.path.join(HERE, "music.py"), os.path.join(HERE, "timeline.json"), music, sfx])
    mixes = {}
    full = os.path.join(work, "mix_full.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", music, "-i", sfx, "-filter_complex",
         "[0]highpass=f=45,bass=g=-3:f=120,volume=0.8[m];[1]volume=1.0[s];[m][s]amix=inputs=2:normalize=0", full])
    mixes["full"] = os.path.join(work, "mix_full_norm.wav")
    loudnorm(full, mixes["full"])
    mixes["sfx"] = os.path.join(work, "mix_sfx_norm.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", sfx, "-af", "volume=0.9", mixes["sfx"]])
    return mixes


def render_overlay(hook, work, fonts):
    out = os.path.join(work, f"ovl_{hook}")
    shutil.rmtree(out, ignore_errors=True)
    env = dict(os.environ, NODE_PATH=subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip())
    run(["node", os.path.join(HERE, "render_overlay.cjs"), os.path.join(HERE, "timeline.json"), hook, fonts, out])
    return out


def compose(base, ovl, audio, dst, fps, crop=None):
    vf = "[0:v][1:v]overlay=0:0:format=auto"
    if crop:
        vf += f",crop={crop}"
    vf += ",format=yuv420p[v]"
    run(["ffmpeg", "-v", "error", "-y", "-i", base, "-framerate", str(fps), "-i", os.path.join(ovl, "f_%04d.png"),
         "-i", audio, "-filter_complex", vf, "-map", "[v]", "-map", "2:a", "-shortest",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-r", str(fps), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dst])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--fonts")
    args = ap.parse_args()
    os.makedirs(args.work, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    fonts = args.fonts or os.path.join(args.work, "fonts")
    os.makedirs(fonts, exist_ok=True)
    for name, url in FONTS.items():
        if not os.path.exists(os.path.join(fonts, name)):
            urllib.request.urlretrieve(url, os.path.join(fonts, name))

    tl = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
    base = build_segments(tl, args.work)
    mixes = build_audio(tl, args.work)
    overlays = {}
    for ex in tl["exports"]:
        if ex["hook"] not in overlays:
            overlays[ex["hook"]] = render_overlay(ex["hook"], args.work, fonts)
        crop = None
        if ex.get("aspect") == "4x5":
            crop = f"{tl['width']}:1350:0:{(tl['height'] - 1350) // 2}"
        compose(base, overlays[ex["hook"]], mixes[ex["audio"]], os.path.join(OUT, ex["name"] + ".mp4"), tl["fps"], crop)
    print("done ->", OUT)


if __name__ == "__main__":
    main()
