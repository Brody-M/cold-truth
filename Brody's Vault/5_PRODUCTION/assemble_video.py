#!/usr/bin/env python3
"""
Cold Truth — Asha Degree Video Assembler
=========================================
Downloads stock footage from Pexels, trims/scales each clip, adds text
overlays, concatenates everything, and layers the voiceover.

Usage:
    python assemble_video.py

Resumes automatically: skips clips already downloaded or processed.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

# ── Configuration ──────────────────────────────────────────────────────────────
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY", "")
if not PEXELS_KEY:
    print("ERROR: PEXELS_API_KEY environment variable not set.")
    print("  Set it with: $env:PEXELS_API_KEY = '<your key>'")
    sys.exit(1)
BASE          = Path(r"C:\Youtube Automation Obsidian\Brody's Vault\5_PRODUCTION")
SHOT_LIST     = BASE / "Asha_Degree_Shot_List.md"
VOICEOVER     = BASE / "Asha_Degree_voiceover.mp3"
FOOTAGE_DIR   = BASE / "footage"
PROCESSED_DIR = BASE / "processed"
# NOTE: CONCAT_OUT lives in BASE — apostrophe in path is fine as a subprocess arg.
CONCAT_OUT    = BASE / "Asha_Degree_concat.mp4"
OUTPUT        = BASE / "Asha_Degree_FINAL.mp4"

WIDTH, HEIGHT = 1920, 1080
FPS           = 30

# Arial Bold confirmed at C:\Windows\Fonts\arialbd.ttf.
# FFmpeg filter strings require the drive-letter colon escaped as \:
FONT_FILE = r"C\:/Windows/Fonts/arialbd.ttf"


# ── Utilities ──────────────────────────────────────────────────────────────────

def run(cmd: list, label: str = "", cwd: str | None = None) -> tuple[bool, str]:
    """Run a subprocess; return (success, stderr). Optional cwd overrides working dir."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    except FileNotFoundError:
        return False, f"command not found: {cmd[0]}"
    if result.returncode != 0 and label:
        snippet = result.stderr[-600:].strip()
        print(f"    [WARN] {label}:\n{snippet}")
    return result.returncode == 0, result.stderr


def get_duration(path: Path) -> float:
    """Return media duration in seconds via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", str(path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def ts_to_sec(ts: str) -> float:
    """Convert 'M:SS' timestamp string to total seconds."""
    m, s = ts.split(":")
    return int(m) * 60 + int(s)


def fmt_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


# ── Text / Path Helpers ────────────────────────────────────────────────────────

def sanitize_overlay(text: str) -> str:
    """
    Clean up overlay text pulled from the shot list markdown before any
    FFmpeg processing:
      - Strip wrapping backtick characters
      - Replace em dash (—) and en dash (–) with ' - '
      - Replace curly/smart single and double quotes with straight equivalents
    """
    text = text.strip("`")
    text = text.replace("—", " - ")    # em dash  —
    text = text.replace("–", " - ")    # en dash  –
    text = text.replace("‘", "'")      # left  single curly quote  '
    text = text.replace("’", "'")      # right single curly quote  '
    text = text.replace("“", '"')      # left  double curly quote  "
    text = text.replace("”", '"')      # right double curly quote  "
    return text.strip()


def escape_drawtext(text: str) -> str:
    """
    Escape a string for use as an inline FFmpeg drawtext text='...' value.
    Order is critical — backslash must be escaped first so later replacements
    don't double-escape the backslashes they introduce.

    Escaping rules applied:
      \\  →  \\\\   (backslash)
      '   →  \\'    (apostrophe / single quote ends the quoted value)
      %   →  \\%    (percent is a strftime escape in drawtext)
      :   →  \\:    (colon is the FFmpeg filter option separator)
      ,   →  \\,    (comma is the FFmpeg filter-chain separator)
    """
    text = text.replace("\\", "\\\\")   # 1. backslash  — must be first
    text = text.replace("'",  "\\'")    # 2. apostrophe
    text = text.replace("%",  "\\%")    # 3. percent
    text = text.replace(":",  "\\:")    # 4. colon
    text = text.replace(",",  "\\,")    # 5. comma
    return text


def ffmpeg_escape_path(path: Path) -> str:
    """
    Convert a Windows Path to an FFmpeg filter-option-safe string:
      - All backslashes replaced with forward slashes
      - Drive-letter colon escaped as \\: (e.g. C: → C\\:)
        so FFmpeg doesn't interpret it as a filter option separator
    """
    s = str(path).replace("\\", "/")
    s = re.sub(r"^([A-Za-z]):", r"\1\\:", s)
    return s


def write_overlay_textfile(text: str, shot_num: int) -> Path:
    """
    Write sanitized overlay text to a file inside the OS temp directory.
    Using temp dir guarantees no apostrophes or other problematic characters
    in the file path, which matters because the path is embedded in the
    FFmpeg drawtext filter string.
    Returns the Path of the written file.
    """
    tmp_dir = Path(tempfile.gettempdir()) / "coldtruth_overlays"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    txt_path = tmp_dir / f"shot_{shot_num:02d}_overlay.txt"
    txt_path.write_text(text, encoding="utf-8")
    return txt_path


# ── Shot List Parser ───────────────────────────────────────────────────────────

def parse_shot_list(path: Path) -> list[dict]:
    """
    Parse the markdown shot list and return a list of shot dicts:
        num, ts, duration, terms (list of 3), overlay (str | None)
    """
    content = path.read_text(encoding="utf-8")
    shots = []

    for block in re.split(r"\n(?=### \d+\.)", content):
        m = re.match(r"### (\d+)\. `(\d+:\d+)`", block)
        if not m:
            continue

        num = int(m.group(1))
        ts  = m.group(2)

        # Extract the three backtick-quoted search terms
        terms_section = re.search(r"\*\*Search Terms:\*\*(.+?)(?:\n\*\*|\Z)", block, re.DOTALL)
        terms = re.findall(r"`([^`]+)`", terms_section.group(1)) if terms_section else []
        terms = terms[:3]

        # Extract text overlay (None if starts with "None")
        ov_m = re.search(r"\*\*Text Overlay:\*\* (.+)", block)
        overlay = None
        if ov_m:
            raw = ov_m.group(1).strip()
            if not raw.lower().startswith("none"):
                overlay = raw

        shots.append({"num": num, "ts": ts, "terms": terms, "overlay": overlay})

    # Calculate per-shot duration from sequential timestamps
    vo_dur = get_duration(VOICEOVER)
    for i, shot in enumerate(shots):
        start = ts_to_sec(shot["ts"])
        if i + 1 < len(shots):
            end = ts_to_sec(shots[i + 1]["ts"])
        else:
            end = vo_dur
        shot["start"]    = start
        shot["duration"] = max(round(end - start, 2), 1.5)

    return shots


# ── Pexels Downloader ──────────────────────────────────────────────────────────

def download_pexels(terms: list[str], output_path: Path) -> bool:
    """
    Try each search term in order. Download the best HD landscape clip found.
    Returns True on success.
    """
    headers = {"Authorization": PEXELS_KEY}

    for term in terms:
        try:
            r = requests.get(
                "https://api.pexels.com/videos/search",
                headers=headers,
                params={"query": term, "per_page": 10, "orientation": "landscape", "size": "large"},
                timeout=20,
            )
            if r.status_code != 200:
                print(f"    Pexels [{r.status_code}] for '{term}'")
                time.sleep(1)
                continue

            videos = r.json().get("videos", [])
            # Prefer clips with at least 10 s of content
            usable = [v for v in videos if v.get("duration", 0) >= 10]
            if not usable:
                usable = videos  # fall back to anything

            for video in usable:
                # Pick highest-resolution mp4
                files = [
                    f for f in video.get("video_files", [])
                    if f.get("file_type") == "video/mp4"
                ]
                files.sort(key=lambda f: f.get("height", 0) * f.get("width", 0), reverse=True)
                hd = [f for f in files if f.get("height", 0) >= 720]
                best = hd[0] if hd else (files[0] if files else None)
                if not best:
                    continue

                url = best["link"]
                print(f"    ↓ '{term}' — {best['width']}×{best['height']}, {video['duration']}s")

                resp = requests.get(url, stream=True, timeout=180)
                total = 0
                with open(output_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        f.write(chunk)
                        total += len(chunk)
                print(f"    ✓ {total / 1_048_576:.1f} MB → {output_path.name}")
                time.sleep(0.4)
                return True

        except Exception as exc:
            print(f"    Error on '{term}': {exc}")
        time.sleep(0.6)

    return False


def make_placeholder(output_path: Path, duration: float) -> None:
    """Black silent placeholder clip — used when footage download fails."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s={WIDTH}x{HEIGHT}:r={FPS}",
        "-t", str(duration),
        "-c:v", "libx264", "-crf", "23", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    run(cmd, "make_placeholder")


# ── Clip Processor ─────────────────────────────────────────────────────────────

def process_clip(raw: Path, out: Path, duration: float, overlay: str | None) -> None:
    """
    Trim raw clip to `duration` seconds (looping if necessary), scale/crop to
    1920×1080, optionally burn in a lower-third text overlay, output video-only MP4.

    Overlay pipeline:
      1. sanitize_overlay()      — strip backticks, fix dashes/curly quotes
      2. write_overlay_textfile() — write to OS temp dir (no apostrophe in path)
      3. drawtext textfile=       — FFmpeg reads the text from the file, avoiding
                                    all inline escaping pitfalls
    """
    # Scale to fill frame (cover), then hard-crop to exact resolution
    vf_parts = [
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase",
        f"crop={WIDTH}:{HEIGHT}",
        f"fps={FPS}",
    ]

    if overlay:
        # Step 1: sanitize raw markdown text
        clean = sanitize_overlay(overlay)

        # Step 2: write to temp file (path guaranteed apostrophe-free)
        shot_num = int(out.stem.split("_")[1])   # "shot_01_processed" → 1
        txt_path = write_overlay_textfile(clean, shot_num)
        escaped_txt_path = ffmpeg_escape_path(txt_path)

        # Step 3: build drawtext filter using textfile= (no inline text escaping needed)
        fontsize  = 52 if len(clean) <= 30 else (44 if len(clean) <= 45 else 36)
        show_from = 0.5
        show_to   = max(duration - 0.5, show_from + 0.5)
        dt = (
            f"drawtext=fontfile={FONT_FILE}"
            f":textfile={escaped_txt_path}"
            f":fontcolor=white"
            f":fontsize={fontsize}"
            f":x=(w-text_w)/2"
            f":y=h-text_h-72"
            f":box=1"
            f":boxcolor=black@0.65"
            f":boxborderw=16"
            f":enable='between(t,{show_from},{show_to})'"
        )
        vf_parts.append(dt)

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",       # loop source clip if shorter than duration
        "-i", str(raw),
        "-t", str(duration),
        "-vf", ",".join(vf_parts),
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-an",                      # no audio — voiceover added in final step
        str(out),
    ]
    ok, _ = run(cmd, f"process shot {raw.stem}")
    if not ok:
        print(f"    !! Processing failed — falling back to placeholder")
        make_placeholder(out, duration)


# ── Final Assembly ─────────────────────────────────────────────────────────────

def assemble(clips: list[Path], voiceover: Path, output: Path) -> bool:
    """
    Concatenate all processed clips (video-only), then mix with voiceover audio.

    concat_list.txt is written to PROCESSED_DIR using bare filenames only
    (no directory path). FFmpeg runs with cwd=PROCESSED_DIR so those relative
    names resolve correctly. This means the apostrophe in 'Brody's Vault' never
    appears inside the concat file, which would break FFmpeg's single-quote
    path syntax.
    """
    # Write concat list: bare filenames, no single-quote wrapping.
    # Filenames like shot_01_processed.mp4 contain no spaces, so no quoting needed.
    concat_path = PROCESSED_DIR / "concat_list.txt"
    with open(concat_path, "w", encoding="utf-8") as f:
        for clip in clips:
            f.write(f"file {clip.name}\n")

    # ── Step 1: concatenate ────────────────────────────────────────────────────
    print("  Concatenating clips...")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_path),     # absolute path as subprocess arg — apostrophe is fine
        "-c", "copy",
        str(CONCAT_OUT),            # absolute output path — same reasoning
    ]
    # cwd=PROCESSED_DIR so bare filenames in concat_list.txt resolve correctly
    ok, _ = run(concat_cmd, "concat (copy)", cwd=str(PROCESSED_DIR))
    if not ok:
        # Fallback: re-encode during concat to resolve any codec mismatch
        print("  Retrying concat with re-encode...")
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_path),
            "-c:v", "libx264", "-crf", "20", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            str(CONCAT_OUT),
        ]
        ok, _ = run(concat_cmd, "concat (re-encode)", cwd=str(PROCESSED_DIR))
        if not ok:
            return False

    # ── Step 2: mix voiceover ──────────────────────────────────────────────────
    print("  Mixing voiceover...")
    mix_cmd = [
        "ffmpeg", "-y",
        "-i", str(CONCAT_OUT),
        "-i", str(voiceover),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output),
    ]
    ok, _ = run(mix_cmd, "voiceover mix")

    # Cleanup intermediates
    CONCAT_OUT.unlink(missing_ok=True)
    concat_path.unlink(missing_ok=True)
    return ok


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 62)
    print("  Cold Truth — Asha Degree Video Assembler")
    print("=" * 62)

    # Verify FFmpeg/ffprobe are available
    ok, _ = run(["ffmpeg", "-version"])
    if not ok:
        print("\nERROR: FFmpeg not found on PATH.")
        print("Install: winget install Gyan.FFmpeg  (restart terminal after)")
        sys.exit(1)
    print("FFmpeg: OK")

    FOOTAGE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Parse shot list ─────────────────────────────────────────────────────
    print(f"\n[1/4] Parsing shot list...")
    shots = parse_shot_list(SHOT_LIST)
    total_dur = sum(s["duration"] for s in shots)
    print(f"      {len(shots)} shots · estimated runtime {fmt_duration(total_dur)}")
    print()
    print(f"  {'#':>2}  {'TS':>5}  {'DUR':>6}  {'OVERLAY'}")
    print(f"  {'─'*2}  {'─'*5}  {'─'*6}  {'─'*40}")
    for s in shots:
        ov = s["overlay"] or "—"
        print(f"  {s['num']:>2}  {s['ts']:>5}  {s['duration']:>5.1f}s  {ov[:50]}")

    # ── 2. Download footage ────────────────────────────────────────────────────
    print(f"\n[2/4] Downloading footage from Pexels...")
    t0 = time.time()
    for shot in shots:
        raw = FOOTAGE_DIR / f"shot_{shot['num']:02d}_raw.mp4"
        if raw.exists() and raw.stat().st_size > 10_000:
            print(f"  Shot {shot['num']:02d}: cached ✓")
            continue
        first_term = shot["terms"][0] if shot["terms"] else "(no terms)"
        print(f"  Shot {shot['num']:02d} [{shot['ts']}] → '{first_term}'")
        success = download_pexels(shot["terms"], raw)
        if not success:
            print(f"    !! No footage found — placeholder will be used")
            make_placeholder(raw, shot["duration"] + 5)
    print(f"  Downloads complete in {time.time()-t0:.0f}s")

    # ── 3. Process clips ───────────────────────────────────────────────────────
    print(f"\n[3/4] Processing clips (trim · scale · overlay)...")
    t0 = time.time()
    processed: list[Path] = []
    for shot in shots:
        raw  = FOOTAGE_DIR   / f"shot_{shot['num']:02d}_raw.mp4"
        proc = PROCESSED_DIR / f"shot_{shot['num']:02d}_processed.mp4"
        if proc.exists() and proc.stat().st_size > 10_000:
            print(f"  Shot {shot['num']:02d}: cached ✓")
        else:
            overlay_label = f" + '{shot['overlay']}'" if shot["overlay"] else ""
            print(f"  Shot {shot['num']:02d}: {shot['duration']:.1f}s{overlay_label}")
            process_clip(raw, proc, shot["duration"], shot["overlay"])
        processed.append(proc)
    print(f"  Processing complete in {time.time()-t0:.0f}s")

    # ── 4. Assemble final video ────────────────────────────────────────────────
    print(f"\n[4/4] Assembling final video...")
    t0 = time.time()
    ok = assemble(processed, VOICEOVER, OUTPUT)

    if ok and OUTPUT.exists():
        size_mb   = OUTPUT.stat().st_size / 1_048_576
        final_dur = get_duration(OUTPUT)
        print(f"\n{'='*62}")
        print(f"  ✓  COMPLETE")
        print(f"  File    : {OUTPUT}")
        print(f"  Size    : {size_mb:.1f} MB")
        print(f"  Duration: {fmt_duration(final_dur)}")
        print(f"  Assembly: {time.time()-t0:.0f}s")
        print(f"{'='*62}")
    else:
        print("\n!! Assembly failed — check warnings above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
