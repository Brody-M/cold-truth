#!/usr/bin/env python3
"""
Cold Truth — Asha Degree Video Assembler (Pexels Edition)
=========================================================
Fetches real stock footage from Pexels per shot, processes with FFmpeg
(trim/loop, scale, Ken Burns for stills, text overlay), and assembles
the final video with voiceover.

Usage:
    python assemble_video_pexels.py           # fresh run
    python assemble_video_pexels.py --resume  # retry shots in pexels_failed.json

Outputs:
    pexels_footage/          — raw downloaded clips / images
    processed_pexels/        — trimmed, scaled, overlaid clips
    pexels_failed.json       — shots that could not be sourced
    Asha_Degree_FINAL_v3.mp4 — final assembled video
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

# ── UTF-8 stdout on Windows ───────────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE          = Path(r"C:\Youtube Automation Obsidian\Brody's Vault\5_PRODUCTION")
SHOT_LIST     = BASE / "Asha_Degree_Shot_List.md"
VOICEOVER     = BASE / "Asha_Degree_voiceover.mp3"
FOOTAGE_DIR   = BASE / "pexels_footage"
PROCESSED_DIR = BASE / "processed_pexels"
CONCAT_OUT    = BASE / "Asha_Degree_concat_pexels.mp4"
OUTPUT        = BASE / "Asha_Degree_FINAL_v3.mp4"
FAILED_FILE   = BASE / "pexels_failed.json"

# ── Video settings ─────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1920, 1080
FPS           = 30
FONT_FILE     = r"C\:/Windows/Fonts/arialbd.ttf"

# ── Pexels API ─────────────────────────────────────────────────────────────────
PEXELS_KEY          = "xaWZ4W5wLwPD7uCfL8CfDFJ6Y9pmSmd8aShXPJcZi3f8aLOosmA0P9f4"
PEXELS_VIDEO_URL    = "https://api.pexels.com/videos/search"
PEXELS_IMAGE_URL    = "https://api.pexels.com/v1/search"
PEXELS_HEADERS      = {"Authorization": PEXELS_KEY}
PER_PAGE            = 10    # results per term (pick best one)
REQUEST_DELAY       = 0.5   # seconds between Pexels API calls


# ══════════════════════════════════════════════════════════════════════════════
# SUBPROCESS / FFMPEG HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def run(cmd: list, label: str = "", cwd: str | None = None) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd,
            encoding="utf-8", errors="replace"
        )
    except FileNotFoundError:
        return False, f"command not found: {cmd[0]}"
    if result.returncode != 0 and label:
        print(f"    [WARN] {label}:\n{result.stderr[-600:].strip()}")
    return result.returncode == 0, result.stderr


def get_duration(path: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "json", str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def ts_to_sec(ts: str) -> float:
    m, s = ts.split(":")
    return int(m) * 60 + int(s)


def fmt_dur(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def sanitize_overlay(text: str) -> str:
    text = text.strip("`")
    for src, dst in [("—", " - "), ("–", " - "), ("‘", "'"), ("’", "'"),
                     ("“", '"'), ("”", '"')]:
        text = text.replace(src, dst)
    return text.strip()


def make_text_overlay_png(text: str, shot_num: int) -> Path | None:
    """
    Render a lower-third text overlay as a 1920x1080 RGBA PNG using Pillow.
    Returns the PNG path, or None if Pillow is unavailable.

    Why Pillow instead of FFmpeg drawtext:
      FFmpeg's filter-string `\:` escape for Windows drive letters (C\:/) is
      broken in this build when paths are passed via subprocess on Windows —
      the filter parser rejects the fontfile= and textfile= options.
      Pillow handles Windows paths natively; the PNG is then composited via
      FFmpeg's overlay filter where the path goes into -i (not a filter string).
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("    [WARN] Pillow not installed — text overlay skipped")
        return None

    img  = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    fsize = 52 if len(text) <= 30 else (44 if len(text) <= 45 else 36)
    font  = None
    for font_path in [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ]:
        try:
            font = ImageFont.truetype(font_path, fsize)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox   = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (WIDTH  - text_w) // 2
    y =  HEIGHT - text_h  - 72

    pad = 16
    draw.rectangle(
        [x - pad, y - pad, x + text_w + pad, y + text_h + pad],
        fill=(0, 0, 0, 166),   # black @ ~65% opacity
    )
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    out_dir = Path(tempfile.gettempdir()) / "coldtruth_overlays"
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / f"overlay_{shot_num:02d}.png"
    img.save(png, "PNG")
    return png


def composite_overlay(video: Path, overlay_png: Path, out: Path) -> bool:
    """
    Composite a full-frame RGBA PNG overlay onto a video clip.
    The PNG path goes into -i (not a filter string) so Windows path
    escaping is not an issue.
    """
    ok, _ = run([
        "ffmpeg", "-y",
        "-i", str(video),
        "-i", str(overlay_png),
        "-filter_complex", "[0:v][1:v]overlay=0:0",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-an",
        str(out),
    ], f"composite_overlay {video.stem}")
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# FAILED-SHOTS REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

def load_failed() -> dict:
    if FAILED_FILE.exists():
        try:
            return json.loads(FAILED_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def mark_failed(num: int, reason: str) -> None:
    data = load_failed()
    data[str(num)] = reason
    FAILED_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def clear_failed(num: int) -> None:
    data = load_failed()
    data.pop(str(num), None)
    FAILED_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ══════════════════════════════════════════════════════════════════════════════
# SHOT LIST PARSER
# ══════════════════════════════════════════════════════════════════════════════

def parse_shot_list(path: Path) -> list[dict]:
    content = path.read_text(encoding="utf-8")
    shots   = []

    for block in re.split(r"\n(?=### \d+\.)", content):
        m = re.match(r"### (\d+)\. `(\d+:\d+)`", block)
        if not m:
            continue
        num = int(m.group(1))
        ts  = m.group(2)

        vis_m  = re.search(r"\*\*Visual:\*\* (.+)", block)
        visual = vis_m.group(1).strip() if vis_m else ""

        terms_sec = re.search(r"\*\*Search Terms:\*\*(.+?)(?:\n\*\*|\Z)", block, re.DOTALL)
        terms     = re.findall(r"`([^`]+)`", terms_sec.group(1)) if terms_sec else []

        ov_m    = re.search(r"\*\*Text Overlay:\*\* (.+)", block)
        overlay = None
        if ov_m:
            raw = ov_m.group(1).strip()
            if not raw.lower().startswith("none"):
                overlay = raw

        shots.append({
            "num":     num,
            "ts":      ts,
            "visual":  visual,
            "terms":   terms[:3],
            "overlay": overlay,
        })

    vo_dur = get_duration(VOICEOVER)
    for i, shot in enumerate(shots):
        start = ts_to_sec(shot["ts"])
        end   = ts_to_sec(shots[i + 1]["ts"]) if i + 1 < len(shots) else vo_dur
        shot["start"]    = start
        shot["duration"] = max(round(end - start, 2), 2.0)

    return shots


# ══════════════════════════════════════════════════════════════════════════════
# PEXELS SEARCH & DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════

def _best_video_file(video_files: list) -> dict | None:
    """
    Pick the best video file from a Pexels video's file list.
    Prefers HD (1080p), then HD (720p), then any landscape file.
    Requires file_type to be video/mp4.
    """
    def score(f: dict) -> int:
        if f.get("file_type") != "video/mp4":
            return -1
        w = f.get("width", 0)
        h = f.get("height", 0)
        # Prefer landscape
        if w < h:
            return 0
        if h >= 1080:
            return 3
        if h >= 720:
            return 2
        return 1

    ranked = sorted(video_files, key=score, reverse=True)
    best   = ranked[0] if ranked else None
    if best and score(best) < 1:
        return None
    return best


def search_pexels_video(term: str) -> str | None:
    """
    Search Pexels for a video matching `term`.
    Returns a download URL string, or None if nothing usable found.
    """
    try:
        r = requests.get(
            PEXELS_VIDEO_URL,
            headers=PEXELS_HEADERS,
            params={"query": term, "per_page": PER_PAGE,
                    "orientation": "landscape", "size": "medium"},
            timeout=15,
        )
        time.sleep(REQUEST_DELAY)
    except requests.RequestException as e:
        print(f"    [Pexels video] Network error: {e}")
        return None

    if r.status_code != 200:
        print(f"    [Pexels video] HTTP {r.status_code} for '{term}'")
        return None

    videos = r.json().get("videos", [])
    for vid in videos:
        best = _best_video_file(vid.get("video_files", []))
        if best and best.get("link"):
            return best["link"]
    return None


def search_pexels_image(term: str) -> str | None:
    """
    Search Pexels for a still image matching `term` (fallback when no video found).
    Returns a URL to the large image, or None.
    """
    try:
        r = requests.get(
            PEXELS_IMAGE_URL,
            headers=PEXELS_HEADERS,
            params={"query": term, "per_page": PER_PAGE,
                    "orientation": "landscape"},
            timeout=15,
        )
        time.sleep(REQUEST_DELAY)
    except requests.RequestException as e:
        print(f"    [Pexels image] Network error: {e}")
        return None

    if r.status_code != 200:
        print(f"    [Pexels image] HTTP {r.status_code} for '{term}'")
        return None

    photos = r.json().get("photos", [])
    if photos:
        src = photos[0].get("src", {})
        return src.get("large2x") or src.get("large") or src.get("original")
    return None


def download_file(url: str, dest: Path, label: str = "") -> bool:
    """
    Download a URL to dest. Verifies that response is video or image content.
    Returns True on success.
    """
    try:
        r = requests.get(url, headers=PEXELS_HEADERS, timeout=60, stream=True)
    except requests.RequestException as e:
        print(f"    [DL] Network error {label}: {e}")
        return False

    if r.status_code != 200:
        print(f"    [DL] HTTP {r.status_code} {label}")
        return False

    ct = r.headers.get("content-type", "")
    if not (ct.startswith("video/") or ct.startswith("image/")):
        print(f"    [DL] Bad content-type '{ct}' for {label} — skipping")
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as fh:
        for chunk in r.iter_content(65536):
            fh.write(chunk)

    size = dest.stat().st_size
    if size < 10_000:
        print(f"    [DL] Suspiciously small ({size} bytes) — discarding")
        dest.unlink(missing_ok=True)
        return False

    print(f"    Downloaded {size / 1_048_576:.1f} MB → {dest.name}")
    return True


def fetch_shot_footage(shot: dict) -> tuple[Path | None, str]:
    """
    Try all 3 search terms for video, then fall back to image.
    Returns (local_path, kind) where kind is 'video' or 'image', or (None, 'failed').
    """
    num   = shot["num"]
    terms = shot["terms"] if shot["terms"] else [shot["visual"]]

    # ── 1. Try video search for each term ──────────────────────────────────────
    for i, term in enumerate(terms):
        print(f"    Term {i+1}/{len(terms)}: '{term}'")
        url = search_pexels_video(term)
        if not url:
            print(f"           No video results.")
            continue

        dest = FOOTAGE_DIR / f"shot_{num:02d}_raw.mp4"
        if download_file(url, dest, label=f"shot {num:02d} video"):
            return dest, "video"
        print(f"           Download failed — trying next term.")

    # ── 2. Fall back to image search ───────────────────────────────────────────
    print(f"    No video found — trying image fallback...")
    for i, term in enumerate(terms):
        url = search_pexels_image(term)
        if not url:
            continue
        dest = FOOTAGE_DIR / f"shot_{num:02d}_raw.jpg"
        if download_file(url, dest, label=f"shot {num:02d} image"):
            return dest, "image"

    return None, "failed"


# ══════════════════════════════════════════════════════════════════════════════
# CLIP PROCESSING
# ══════════════════════════════════════════════════════════════════════════════

def process_video_clip(raw: Path, out: Path, duration: float) -> bool:
    """Scale, trim/loop a video clip to the target duration. No text overlay."""
    ok, _ = run([
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(raw),
        "-t", str(duration),
        "-vf", f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
               f"crop={WIDTH}:{HEIGHT},fps={FPS}",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-an",
        str(out),
    ], f"process_video {raw.stem}")
    return ok


def process_image_clip(raw: Path, out: Path, duration: float) -> bool:
    """Convert a still image to video with Ken Burns zoom. No text overlay."""
    frames = int(duration * FPS)
    kb = (
        f"scale=8000:-1,"
        f"zoompan=z='min(zoom+0.0008,1.3)':d={frames}"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={WIDTH}x{HEIGHT},"
        f"fps={FPS}"
    )
    ok, _ = run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(raw),
        "-t", str(duration),
        "-vf", kb,
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-an",
        str(out),
    ], f"process_image {raw.stem}")
    return ok


def make_dark_placeholder(out: Path, duration: float) -> bool:
    """Generate a dark vignette gradient as a last-resort placeholder."""
    ok, _ = run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=#1a1a1a:s={WIDTH}x{HEIGHT}:r={FPS}",
        "-t", str(duration),
        "-vf", "vignette=angle=PI/4:mode=backward",
        "-c:v", "libx264", "-crf", "28", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        str(out),
    ], f"dark_placeholder {out.stem}")
    return ok


def process_shot(raw: Path, kind: str, out: Path, duration: float,
                 overlay: str | None) -> bool:
    """
    Process one shot:
      1. Convert raw footage → clean 1920×1080 video (no text)
      2. If overlay text: create PNG via Pillow, composite with FFmpeg overlay filter

    Pillow handles Windows font paths natively (no filter-string escaping).
    The PNG path goes into FFmpeg's -i argument, not a filter string.
    """
    # ── Step 1: base video ────────────────────────────────────────────────────
    if overlay:
        # Use a temp file so we can composite overlay onto it in step 2
        base = out.with_suffix(".base.mp4")
    else:
        base = out

    if kind == "video":
        ok = process_video_clip(raw, base, duration)
    elif kind == "image":
        ok = process_image_clip(raw, base, duration)
    else:
        ok = False

    if not ok:
        print(f"    !! Base processing failed — using dark placeholder")
        make_dark_placeholder(base if overlay else out, duration)
        ok = True   # placeholder is "good enough" to continue

    # ── Step 2: text overlay (if any) ─────────────────────────────────────────
    if overlay:
        clean = sanitize_overlay(overlay)
        shot_num = int(out.stem.split("_")[1])
        png = make_text_overlay_png(clean, shot_num)
        if png:
            comp_ok = composite_overlay(base, png, out)
            base.unlink(missing_ok=True)
            if not comp_ok:
                print(f"    !! Overlay composite failed — using base clip without text")
                base.rename(out) if not out.exists() else None
                make_dark_placeholder(out, duration)   # last resort
        else:
            # Pillow unavailable — promote base to output without overlay
            if base.exists() and not out.exists():
                base.rename(out)

    return out.exists() and out.stat().st_size > 10_000


# ══════════════════════════════════════════════════════════════════════════════
# ASSEMBLER
# ══════════════════════════════════════════════════════════════════════════════

def assemble(clips: list[Path], voiceover: Path, output: Path) -> bool:
    concat_list = PROCESSED_DIR / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as fh:
        for clip in clips:
            fh.write(f"file '{clip.name}'\n")

    print("  Concatenating clips...")
    ok, _ = run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_list), "-c", "copy", str(CONCAT_OUT)],
        "concat (copy)", cwd=str(PROCESSED_DIR),
    )
    if not ok:
        print("  Re-encoding concat (stream copy failed)...")
        ok, _ = run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(concat_list),
             "-c:v", "libx264", "-crf", "20", "-preset", "fast",
             "-pix_fmt", "yuv420p", str(CONCAT_OUT)],
            "concat (re-encode)", cwd=str(PROCESSED_DIR),
        )
        if not ok:
            return False

    print("  Mixing voiceover...")
    ok, _ = run([
        "ffmpeg", "-y",
        "-i", str(CONCAT_OUT), "-i", str(voiceover),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(output),
    ], "voiceover mix")

    CONCAT_OUT.unlink(missing_ok=True)
    concat_list.unlink(missing_ok=True)
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Cold Truth — Pexels assembler")
    parser.add_argument("--resume", action="store_true",
                        help="Only retry shots in pexels_failed.json")
    args = parser.parse_args()

    print("=" * 65)
    print("  Cold Truth — Asha Degree Assembler  [Pexels Edition]")
    print(f"  Mode: {'RESUME' if args.resume else 'NORMAL'}")
    print(f"  Output: {OUTPUT.name}")
    print("=" * 65)

    # ── Preflight ──────────────────────────────────────────────────────────────
    ok, _ = run(["ffmpeg", "-version"])
    if not ok:
        print("\nERROR: FFmpeg not found. Install: winget install Gyan.FFmpeg")
        sys.exit(1)
    print("FFmpeg: OK")

    if not VOICEOVER.exists():
        print(f"\nERROR: Voiceover not found: {VOICEOVER}")
        sys.exit(1)
    print(f"Voiceover: {VOICEOVER.name} ({VOICEOVER.stat().st_size / 1_048_576:.1f} MB)")

    FOOTAGE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Parse shot list ─────────────────────────────────────────────────────
    print(f"\n[1/4] Parsing shot list...")
    shots  = parse_shot_list(SHOT_LIST)
    vo_dur = get_duration(VOICEOVER)
    print(f"      {len(shots)} shots | voiceover {fmt_dur(vo_dur)}\n")
    print(f"  {'#':>2}  {'TS':>5}  {'DUR':>6}  VISUAL")
    print(f"  {'--':>2}  {'-----':>5}  {'------':>6}  {'-'*52}")
    for s in shots:
        print(f"  {s['num']:>2}  {s['ts']:>5}  {s['duration']:>5.1f}s  {s['visual'][:54]}")

    # ── 2. Fetch footage ───────────────────────────────────────────────────────
    print(f"\n[2/4] Fetching footage from Pexels ({len(shots)} shots)...")

    failed_reg  = load_failed()
    fetch_results = {}   # num -> ('video'|'image'|'placeholder'|'cached', path)
    import time as _time

    for shot in shots:
        num     = shot["num"]
        terms   = shot["terms"]
        raw_mp4 = FOOTAGE_DIR / f"shot_{num:02d}_raw.mp4"
        raw_jpg = FOOTAGE_DIR / f"shot_{num:02d}_raw.jpg"

        print(f"\n  Shot {num:02d} [{shot['ts']}] {shot['duration']:.1f}s"
              f" — {shot['visual'][:54]}")

        # Skip if we already have valid footage
        existing_video = raw_mp4.exists() and raw_mp4.stat().st_size > 50_000
        existing_image = raw_jpg.exists() and raw_jpg.stat().st_size > 20_000

        if existing_video:
            print(f"    Cached video ({raw_mp4.stat().st_size / 1_048_576:.1f} MB) — skipping")
            fetch_results[num] = ("video", raw_mp4)
            continue
        if existing_image:
            print(f"    Cached image ({raw_jpg.stat().st_size / 1_048_576:.1f} MB) — skipping")
            fetch_results[num] = ("image", raw_jpg)
            continue

        # In resume mode, skip shots that aren't in the failed registry
        if args.resume and str(num) not in failed_reg:
            print(f"    Not in failed registry — skipping (no --resume needed)")
            fetch_results[num] = ("skipped", None)
            continue

        # Fetch from Pexels
        path, kind = fetch_shot_footage(shot)

        if kind == "failed" or path is None:
            print(f"    !! All terms exhausted — using dark placeholder")
            mark_failed(num, "no_footage_found")
            fetch_results[num] = ("placeholder", None)
        else:
            clear_failed(num)
            fetch_results[num] = (kind, path)
            print(f"    OK [{kind}]")

    ok_count = sum(1 for k, _ in fetch_results.values() if k in ("video", "image", "cached"))
    ph_count = sum(1 for k, _ in fetch_results.values() if k == "placeholder")
    print(f"\n  Fetch complete: {ok_count} OK | {ph_count} placeholders | "
          f"{len(shots) - ok_count - ph_count} skipped/cached")

    # ── 3. Process clips ───────────────────────────────────────────────────────
    print(f"\n[3/4] Processing clips (scale · loop · Ken Burns · overlay)...")
    processed: list[Path] = []

    for shot in shots:
        num       = shot["num"]
        proc      = PROCESSED_DIR / f"shot_{num:02d}_processed.mp4"
        duration  = shot["duration"]
        overlay   = shot["overlay"]
        kind, raw = fetch_results.get(num, ("placeholder", None))

        ov_note = f" + overlay" if overlay else ""
        print(f"  Shot {num:02d}: {duration:.1f}s [{kind}]{ov_note}  — ", end="", flush=True)

        # Use cached processed file only if it's clearly real footage (> 2 MB).
        # Dark placeholders are ~50-110 KB and must NOT be treated as cached.
        if proc.exists() and proc.stat().st_size > 2_000_000 and kind in ("video", "image"):
            print(f"processed cached ({proc.stat().st_size // 1_048_576} MB)")
            processed.append(proc)
            continue

        if kind in ("placeholder", "skipped") or raw is None:
            print(f"dark placeholder")
            ok = make_dark_placeholder(proc, duration)
            if overlay and ok and proc.exists():
                # Add text overlay via Pillow PNG → FFmpeg overlay
                clean    = sanitize_overlay(overlay)
                shot_num = int(proc.stem.split("_")[1])
                png      = make_text_overlay_png(clean, shot_num)
                if png:
                    tmp = proc.with_suffix(".tmp.mp4")
                    proc.rename(tmp)
                    comp_ok = composite_overlay(tmp, png, proc)
                    tmp.unlink(missing_ok=True)
                    if not comp_ok:
                        make_dark_placeholder(proc, duration)
        else:
            ok = process_shot(raw, kind, proc, duration, overlay)
            print(f"{'OK' if proc.exists() and proc.stat().st_size > 10_000 else 'FAILED'}")

        processed.append(proc)

    # ── 4. Assemble ────────────────────────────────────────────────────────────
    print(f"\n[4/4] Assembling final video...")
    import time as t_mod
    t0 = t_mod.time()

    ok = assemble(processed, VOICEOVER, OUTPUT)

    if ok and OUTPUT.exists():
        size_mb   = OUTPUT.stat().st_size / 1_048_576
        final_dur = get_duration(OUTPUT)
        print(f"\n{'=' * 65}")
        print(f"  COMPLETE")
        print(f"  File:     {OUTPUT}")
        print(f"  Size:     {size_mb:.1f} MB")
        print(f"  Duration: {fmt_dur(final_dur)}")
        print(f"  Assembly: {t_mod.time() - t0:.0f}s")
        print(f"\n  Shot results:")
        for shot in shots:
            num      = shot["num"]
            kind, _  = fetch_results.get(num, ("?", None))
            proc     = PROCESSED_DIR / f"shot_{num:02d}_processed.mp4"
            size_str = f"{proc.stat().st_size / 1_048_576:.1f} MB" if proc.exists() else "MISSING"
            marker   = "OK" if kind in ("video", "image", "cached") else "PH"
            print(f"    [{marker}] Shot {num:>2} [{kind:>11}]  {shot['duration']:>5.1f}s  {size_str}")
        print(f"{'=' * 65}")
    else:
        print("\n!! Assembly failed — check warnings above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
