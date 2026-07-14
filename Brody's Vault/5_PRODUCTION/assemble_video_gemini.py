#!/usr/bin/env python3
"""
Cold Truth — Asha Degree Video Assembler (Gemini Veo Edition)
==============================================================
Generates AI video clips per shot via Gemini Veo, processes them,
concatenates, and layers the voiceover.

Usage:
    python assemble_video_gemini.py           # fresh run
    python assemble_video_gemini.py --resume  # retry previously-failed shots

Outputs:
    gemini_debug.jsonl   — one JSON line per API request (full audit trail)
    failed_shots.json    — shots that could not be generated (with reason)
    gemini_run.log       — redirect stdout here for persistent logging
"""

import argparse
import base64
import datetime
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

# ── UTF-8 stdout/stderr on Windows ────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── API key ────────────────────────────────────────────────────────────────────
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_KEY:
    print("ERROR: GEMINI_API_KEY environment variable not set.")
    print("  Bash:       export GEMINI_API_KEY='...'")
    print("  PowerShell: $env:GEMINI_API_KEY = '...'")
    sys.exit(1)

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Only one model. Each fallback attempt burns quota — don't cascade.
GEMINI_MODELS = [
    "veo-3.1-generate-preview",
]

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE          = Path(r"C:\Youtube Automation Obsidian\Brody's Vault\5_PRODUCTION")
SHOT_LIST     = BASE / "Asha_Degree_Shot_List.md"
VOICEOVER     = BASE / "Asha_Degree_voiceover.mp3"
FOOTAGE_DIR   = BASE / "gemini_footage"
PROCESSED_DIR = BASE / "processed_gemini"
CONCAT_OUT    = BASE / "Asha_Degree_concat_gemini.mp4"
OUTPUT        = BASE / "Asha_Degree_FINAL_v2.mp4"
FAILED_SHOTS_FILE = BASE / "failed_shots.json"
DEBUG_LOG_FILE    = BASE / "gemini_debug.jsonl"

# ── Video settings ─────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1920, 1080
FPS           = 30
FONT_FILE     = r"C\:/Windows/Fonts/arialbd.ttf"

# ── API / rate-limit settings ──────────────────────────────────────────────────
POLL_INTERVAL          = 12    # seconds between operation status polls
POLL_TIMEOUT           = 600   # max seconds to wait for one clip (10 min)
COOLDOWN_BETWEEN_SHOTS  = 10    # seconds between each API call
MAX_RETRIES_429         = 3     # retries: 30s → 60s → 120s → give up
BACKOFF_BASE_SECS       = 30    # first retry wait (doubles each time)
BACKOFF_MAX_SECS        = 120   # cap at 120s
QUOTA_EXHAUSTED_PAUSE   = 120   # if first shot is immediately 429, wait 2 min

# Clips below this size are treated as black placeholders, not real footage.
# A genuine Veo clip is several MB; a black placeholder from make_placeholder
# at libx264 ultrafast is typically < 20 KB even for a 6-second clip.
MIN_VALID_CLIP_BYTES = 300_000  # 300 KB


# ══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════════════

def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def log_request(
    shot_num: int,
    model: str,
    payload_summary: dict,
    status_code,
    success: bool,
    response_body: str = "",
    notes: str = "",
) -> None:
    """
    Write one JSON line to gemini_debug.jsonl AND print a one-line summary.
    On failure, also print the first 200 chars of the response body.
    """
    entry = {
        "ts":      datetime.datetime.now().isoformat(timespec="seconds"),
        "shot":    shot_num,
        "model":   model,
        "payload": payload_summary,
        "status":  status_code,
        "ok":      success,
    }
    if response_body:
        entry["response"] = response_body[:400]
    if notes:
        entry["notes"] = notes

    with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")

    status_str = f"HTTP {status_code}" if status_code is not None else "NET_ERR"
    ok_str     = "OK  " if success else "FAIL"
    note_str   = f"  [{notes}]" if notes else ""
    print(f"    [{_ts()}] Shot {shot_num:02d} | {model} | {status_str} | {ok_str}{note_str}")
    if not success and response_body:
        print(f"             Response: {response_body[:200]}")


# ══════════════════════════════════════════════════════════════════════════════
# FAILED-SHOTS REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

def load_failed_shots() -> dict:
    """Return {shot_num_str: {reason, ts}} from failed_shots.json, or {}."""
    if FAILED_SHOTS_FILE.exists():
        try:
            return json.loads(FAILED_SHOTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_failed_shot(shot_num: int, reason: str) -> None:
    data = load_failed_shots()
    data[str(shot_num)] = {
        "reason": reason,
        "ts":     datetime.datetime.now().isoformat(timespec="seconds"),
    }
    FAILED_SHOTS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"    -> Logged to failed_shots.json: shot {shot_num} ({reason[:80]})")


def clear_failed_shot(shot_num: int) -> None:
    data = load_failed_shots()
    if str(shot_num) in data:
        data.pop(str(shot_num))
        FAILED_SHOTS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ══════════════════════════════════════════════════════════════════════════════
# SUBPROCESS / FFMPEG HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def run(cmd: list, label: str = "", cwd: str | None = None) -> tuple[bool, str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    except FileNotFoundError:
        return False, f"command not found: {cmd[0]}"
    if result.returncode != 0 and label:
        print(f"    [WARN] {label}:\n{result.stderr[-500:].strip()}")
    return result.returncode == 0, result.stderr


def get_duration(path: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "json", str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def ts_to_sec(ts: str) -> float:
    m, s = ts.split(":")
    return int(m) * 60 + int(s)


def fmt_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


# ══════════════════════════════════════════════════════════════════════════════
# CLIP VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def is_valid_clip(path: Path) -> bool:
    """
    Return True only if the clip is likely a real generated video, not a
    black placeholder.

    Criteria:
      1. File exists
      2. Size >= MIN_VALID_CLIP_BYTES (300 KB)
         A genuine Veo clip is several MB. A black placeholder from
         make_placeholder() at libx264 ultrafast is < 20 KB for 6 seconds.
      3. ffprobe can find a video stream with duration > 0.5s
    """
    if not path.exists():
        return False

    size = path.stat().st_size
    if size < MIN_VALID_CLIP_BYTES:
        print(f"    !! {path.name}: {size:,} bytes < {MIN_VALID_CLIP_BYTES:,} — placeholder")
        return False

    cmd = ["ffprobe", "-v", "error",
           "-select_streams", "v:0",
           "-show_entries", "stream=width,height",
           "-show_entries", "format=duration",
           "-of", "json", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        info    = json.loads(result.stdout)
        dur     = float(info.get("format", {}).get("duration", 0))
        streams = info.get("streams", [])
        if not streams:
            print(f"    !! {path.name}: no video stream found")
            return False
        if dur < 0.5:
            print(f"    !! {path.name}: duration {dur:.2f}s < 0.5s")
            return False
    except Exception as e:
        print(f"    !! {path.name}: ffprobe parse error — {e}")
        return False

    return True


# ══════════════════════════════════════════════════════════════════════════════
# TEXT / OVERLAY HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def sanitize_overlay(text: str) -> str:
    text = text.strip("`")
    text = text.replace("—", " - ").replace("–", " - ")
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    return text.strip()


def ffmpeg_escape_path(path: Path) -> str:
    s = str(path).replace("\\", "/")
    s = re.sub(r"^([A-Za-z]):", r"\1\\:", s)
    return s


def write_overlay_textfile(text: str, shot_num: int) -> Path:
    tmp_dir = Path(tempfile.gettempdir()) / "coldtruth_overlays"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    txt_path = tmp_dir / f"shot_{shot_num:02d}_overlay.txt"
    txt_path.write_text(text, encoding="utf-8")
    return txt_path


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

        shots.append({"num": num, "ts": ts, "visual": visual,
                       "terms": terms[:3], "overlay": overlay})

    vo_dur = get_duration(VOICEOVER)
    for i, shot in enumerate(shots):
        start = ts_to_sec(shot["ts"])
        end   = ts_to_sec(shots[i + 1]["ts"]) if i + 1 < len(shots) else vo_dur
        shot["start"]    = start
        shot["duration"] = max(round(end - start, 2), 1.5)

    return shots


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT + PAYLOAD
# ══════════════════════════════════════════════════════════════════════════════

def build_prompt(shot: dict) -> str:
    base = shot["visual"] or (shot["terms"][0] if shot["terms"] else "documentary footage")
    return (
        f"Cinematic documentary footage: {base}. "
        "Shot on cinema-grade camera. Shallow depth of field. "
        "Moody, dramatic lighting. High quality, 4K. No text or titles."
    )


def build_payload(model: str, prompt: str) -> dict:
    """
    Build and runtime-validate the request payload.

    durationSeconds notes (hard-won):
      - String "8"  → HTTP 400 "must be a number"
      - Integer 5   → HTTP 400 "out of bounds"
      - Integer 8   → untested but probably fine (max of valid range)
      - Omitted     → API uses its default (~8s) — SAFEST choice

    aspectRatio must be a string ("16:9"), not a tuple or number.
    """
    payload = {
        "instances":  [{"prompt": prompt}],
        "parameters": {"aspectRatio": "16:9"},
        # durationSeconds intentionally omitted — see notes above
    }
    assert isinstance(payload["instances"][0]["prompt"], str), \
        "BUG: prompt must be str"
    assert isinstance(payload["parameters"]["aspectRatio"], str), \
        "BUG: aspectRatio must be str"
    return payload


def _payload_summary(payload: dict) -> dict:
    """Compact version safe to include in log lines."""
    prompt = payload["instances"][0]["prompt"]
    return {
        "prompt_chars": len(prompt),
        "prompt_head":  prompt[:60],
        "parameters":   payload["parameters"],
    }


# ══════════════════════════════════════════════════════════════════════════════
# GEMINI API — VIDEO EXTRACTION + POLLING
# ══════════════════════════════════════════════════════════════════════════════

def _api_headers() -> dict:
    return {"x-goog-api-key": GEMINI_KEY, "Content-Type": "application/json"}


def _extract_video(data: dict, output_path: Path) -> bool:
    """
    Pull video bytes from a completed operation response.

    Known response shapes:
      Shape 1 (current docs):
        response.generateVideoResponse.generatedSamples[].video.{uri | bytesBase64Encoded}
      Shape 2 (fallback):
        candidates[].content.parts[].{inlineData | fileData}
    """
    # Shape 1
    gvr = data.get("generateVideoResponse", data)
    for sample in gvr.get("generatedSamples", []):
        video = sample.get("video", {})
        b64   = video.get("bytesBase64Encoded")
        uri   = video.get("uri")
        if b64:
            output_path.write_bytes(base64.b64decode(b64))
            print(f"    Saved {output_path.stat().st_size / 1_048_576:.1f} MB (base64)")
            return True
        if uri:
            r = requests.get(uri, headers={"x-goog-api-key": GEMINI_KEY}, timeout=180)
            output_path.write_bytes(r.content)
            print(f"    Downloaded {len(r.content) / 1_048_576:.1f} MB from URI")
            return True

    # Shape 2
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            if "inlineData" in part:
                output_path.write_bytes(base64.b64decode(part["inlineData"]["data"]))
                print(f"    Saved (inlineData)")
                return True
            if "fileData" in part:
                uri = part["fileData"].get("fileUri", "")
                if uri:
                    r = requests.get(uri, timeout=180)
                    output_path.write_bytes(r.content)
                    print(f"    Downloaded (fileData)")
                    return True

    print(f"    !! Could not extract video. Top-level keys: {list(data.keys())}")
    if data:
        print(f"    !! Full response (first 500): {json.dumps(data)[:500]}")
    return False


def _poll_operation(op_name: str, output_path: Path) -> bool:
    """Poll a long-running operation until done, timed-out, or errored."""
    poll_url = (f"{GEMINI_BASE}/{op_name}"
                if not op_name.startswith("http") else op_name)
    start = time.time()

    while time.time() - start < POLL_TIMEOUT:
        try:
            r = requests.get(poll_url, headers=_api_headers(), timeout=20)
        except requests.RequestException as e:
            print(f"\n    Poll network error: {e}")
            time.sleep(POLL_INTERVAL)
            continue

        if r.status_code != 200:
            print(f"\n    Poll HTTP {r.status_code}: {r.text[:300]}")
            return False

        data    = r.json()
        elapsed = int(time.time() - start)
        print(f"    Generating... {elapsed}s", end="\r", flush=True)

        if data.get("done"):
            print()  # clear the \r line
            if "error" in data:
                print(f"    !! Operation error: {data['error']}")
                return False
            return _extract_video(data.get("response", data), output_path)

        time.sleep(POLL_INTERVAL)

    print(f"\n    !! Timed out after {POLL_TIMEOUT}s")
    return False


# ══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATION FUNCTION  (one shot at a time — serial queue)
# ══════════════════════════════════════════════════════════════════════════════

def generate_one_shot(shot: dict, output_path: Path) -> tuple[bool, str]:
    """
    Generate a single video clip via Gemini Veo.

    Returns (success, reason) where reason is one of:
      "ok"               — clip generated and validated
      "400_invalid"      — API rejected the request; do not retry this model
      "429_exhausted"    — rate-limited; all backoff retries consumed
      "all_failed"       — every model returned a non-retryable error
      "invalid_clip"     — API returned a file but it failed size/stream validation
      "network_error"    — all models had connection failures
    """
    prompt   = build_prompt(shot)
    shot_num = shot["num"]
    any_network_error = False

    for model in GEMINI_MODELS:
        url     = f"{GEMINI_BASE}/models/{model}:predictLongRunning"
        payload = build_payload(model, prompt)
        summary = _payload_summary(payload)

        # Pre-request announcement
        print(f"\n    Model:   {model}")
        print(f"    URL:     {url}")
        print(f"    Payload: prompt={summary['prompt_chars']} chars"
              f" | params={payload['parameters']}")

        retries_429 = 0

        while True:  # inner retry loop for 429 backoff

            # ── Make the request ──────────────────────────────────────────────
            try:
                r = requests.post(
                    url, headers=_api_headers(), json=payload, timeout=30
                )
            except requests.RequestException as exc:
                log_request(shot_num, model, summary, None, False,
                            str(exc), notes="network_error")
                any_network_error = True
                break  # try next model

            # ── 200 OK ────────────────────────────────────────────────────────
            if r.status_code == 200:
                log_request(shot_num, model, summary, 200, True)
                data = r.json()
                op   = data.get("name")

                polled = (_poll_operation(op, output_path)
                          if op else _extract_video(data, output_path))

                if not polled:
                    break  # extraction/poll failed — try next model

                if is_valid_clip(output_path):
                    clear_failed_shot(shot_num)
                    return True, "ok"
                else:
                    # Received a response but clip is black/corrupt
                    if output_path.exists():
                        output_path.unlink()
                    log_request(shot_num, model, summary, 200, False,
                                notes="invalid_clip_post_validation")
                    save_failed_shot(shot_num, "invalid_clip")
                    return False, "invalid_clip"

            # ── 400 Bad Request ───────────────────────────────────────────────
            elif r.status_code == 400:
                try:
                    msg = r.json().get("error", {}).get("message", r.text[:400])
                except Exception:
                    msg = r.text[:400]
                log_request(shot_num, model, summary, 400, False, msg,
                            notes="400_no_retry")
                print(f"    400 BadRequest: {msg}")
                print(f"    Not retrying this model (payload rejected).")
                save_failed_shot(shot_num, f"400:{msg[:120]}")
                break  # move to next model

            # ── 429 Too Many Requests ─────────────────────────────────────────
            elif r.status_code == 429:
                retries_429 += 1
                if retries_429 > MAX_RETRIES_429:
                    log_request(shot_num, model, summary, 429, False,
                                notes=f"429_exhausted_{MAX_RETRIES_429}_retries")
                    print(f"    429 exhausted ({MAX_RETRIES_429} retries) — next model.")
                    save_failed_shot(shot_num, "429_exhausted")
                    break

                base_wait = min(BACKOFF_BASE_SECS * (2 ** (retries_429 - 1)),
                                BACKOFF_MAX_SECS)
                jitter    = random.uniform(-0.2 * base_wait, 0.2 * base_wait)
                wait      = max(10, int(base_wait + jitter))
                log_request(shot_num, model, summary, 429, False,
                            notes=f"backoff_{wait}s_attempt_{retries_429}")
                print(f"    429 Rate limited (attempt {retries_429}/{MAX_RETRIES_429})"
                      f" — backing off {wait}s...")
                time.sleep(wait)
                continue  # retry same model after backoff

            # ── Other errors ──────────────────────────────────────────────────
            else:
                try:
                    body = json.dumps(r.json())[:300]
                except Exception:
                    body = r.text[:300]
                log_request(shot_num, model, summary, r.status_code, False, body)
                print(f"    HTTP {r.status_code} — trying next model.")
                break

    if any_network_error:
        return False, "network_error"
    return False, "all_failed"


# ══════════════════════════════════════════════════════════════════════════════
# CLIP PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════

def make_placeholder(output_path: Path, duration: float) -> None:
    """Generate a solid-black placeholder clip. Intentionally tiny file size."""
    run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=black:s={WIDTH}x{HEIGHT}:r={FPS}",
        "-t", str(duration),
        "-c:v", "libx264", "-crf", "28", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", str(output_path),
    ], "make_placeholder")


def process_clip(raw: Path, out: Path, duration: float,
                 overlay: str | None) -> None:
    vf = [
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase",
        f"crop={WIDTH}:{HEIGHT}",
        f"fps={FPS}",
    ]

    if overlay:
        clean    = sanitize_overlay(overlay)
        shot_num = int(out.stem.split("_")[1])
        txt      = write_overlay_textfile(clean, shot_num)
        esc      = ffmpeg_escape_path(txt)
        fsize    = 52 if len(clean) <= 30 else (44 if len(clean) <= 45 else 36)
        t0, t1   = 0.5, max(duration - 0.5, 1.0)
        vf.append(
            f"drawtext=fontfile={FONT_FILE}"
            f":textfile={esc}"
            f":fontcolor=white:fontsize={fsize}"
            f":x=(w-text_w)/2:y=h-text_h-72"
            f":box=1:boxcolor=black@0.65:boxborderw=16"
            f":enable='between(t,{t0},{t1})'"
        )

    ok, _ = run([
        "ffmpeg", "-y", "-stream_loop", "-1",
        "-i", str(raw),
        "-t", str(duration),
        "-vf", ",".join(vf),
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-an",
        str(out),
    ], f"process {raw.stem}")

    if not ok:
        print("    !! Processing failed — placeholder used")
        make_placeholder(out, duration)


# ══════════════════════════════════════════════════════════════════════════════
# FINAL ASSEMBLER
# ══════════════════════════════════════════════════════════════════════════════

def assemble(clips: list[Path], voiceover: Path, output: Path) -> bool:
    concat_path = PROCESSED_DIR / "concat_list.txt"
    with open(concat_path, "w", encoding="utf-8") as fh:
        for clip in clips:
            fh.write(f"file {clip.name}\n")

    print("  Concatenating...")
    ok, _ = run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_path), "-c", "copy", str(CONCAT_OUT)],
        "concat (copy)", cwd=str(PROCESSED_DIR),
    )
    if not ok:
        print("  Retrying with re-encode...")
        ok, _ = run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(concat_path),
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
    concat_path.unlink(missing_ok=True)
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Cold Truth — Gemini Veo assembler")
    parser.add_argument(
        "--resume", action="store_true",
        help="Re-attempt shots listed in failed_shots.json (normally they are skipped).",
    )
    args = parser.parse_args()

    mode = "RESUME" if args.resume else "NORMAL"
    print("=" * 62)
    print("  Cold Truth — Asha Degree Assembler (Gemini Veo)")
    print(f"  Mode: {mode}")
    print(f"  Debug log:    {DEBUG_LOG_FILE.name}")
    print(f"  Failed shots: {FAILED_SHOTS_FILE.name}")
    print("=" * 62)

    # ── Preflight ──────────────────────────────────────────────────────────────
    ok, _ = run(["ffmpeg", "-version"])
    if not ok:
        print("\nERROR: FFmpeg not found.")
        print("  Install with: winget install Gyan.FFmpeg")
        sys.exit(1)
    print("FFmpeg: OK")

    FOOTAGE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Parse shot list ─────────────────────────────────────────────────────
    print(f"\n[1/4] Parsing shot list...")
    shots    = parse_shot_list(SHOT_LIST)
    total_vo = get_duration(VOICEOVER)
    print(f"      {len(shots)} shots | voiceover {fmt_duration(total_vo)}\n")
    print(f"  {'#':>2}  {'TS':>5}  {'DUR':>6}  VISUAL")
    print(f"  {'--'}  {'-----'}  {'------'}  {'-' * 50}")
    for s in shots:
        print(f"  {s['num']:>2}  {s['ts']:>5}  {s['duration']:>5.1f}s  {s['visual'][:52]}")

    # ── 2. Generate footage (serial — one shot at a time) ──────────────────────
    print(f"\n[2/4] Generating {len(shots)} clips — serial queue, "
          f"{COOLDOWN_BETWEEN_SHOTS}s cooldown between shots")
    print(f"      Models (in priority order): {', '.join(GEMINI_MODELS)}")

    failed_registry    = load_failed_shots()
    generation_results  = {}   # shot_num -> "ok"|"cached"|"skipped:..."|reason
    t0                  = time.time()
    first_request_made  = False   # track whether ANY request has gone out yet

    if failed_registry:
        print(f"\n  Previously failed shots: {list(failed_registry.keys())}")

    for shot in shots:
        num = shot["num"]
        raw = FOOTAGE_DIR / f"shot_{num:02d}_raw.mp4"

        # Already have a valid real clip — skip regardless of mode
        if raw.exists() and is_valid_clip(raw):
            print(f"\n  Shot {num:02d}: valid clip cached — skipping")
            generation_results[num] = "cached"
            continue

        # Previously failed AND not in resume mode — skip to conserve quota
        if str(num) in failed_registry and not args.resume:
            reason = failed_registry[str(num)].get("reason", "unknown")
            print(f"\n  Shot {num:02d}: previously failed ({reason[:60]})"
                  f" — skipping (run with --resume to retry)")
            generation_results[num] = f"skipped:{reason}"
            continue

        # Delete any stale placeholder before generating
        if raw.exists() and not is_valid_clip(raw):
            print(f"\n  Shot {num:02d}: removing stale placeholder before regenerating")
            raw.unlink()

        print(f"\n  Shot {num:02d} [{shot['ts']}] {shot['duration']:.1f}s"
              f" — {shot['visual'][:55]}")

        success, reason = generate_one_shot(shot, raw)
        generation_results[num] = reason

        # If the very first real request hit 429, quota is almost certainly
        # exhausted from previous runs. Pause before continuing.
        if not first_request_made and reason in ("429_exhausted", "all_failed"):
            print(f"\n  !! First request returned 429 — quota likely exhausted.")
            print(f"  !! Pausing {QUOTA_EXHAUSTED_PAUSE}s before next shot...")
            time.sleep(QUOTA_EXHAUSTED_PAUSE)
        first_request_made = True

        if not success:
            print(f"    Generation failed ({reason}) — black placeholder written")
            make_placeholder(raw, 6.0)
        else:
            print(f"    Shot {num:02d} generated OK")

        # Cooldown — avoids hammering the API between shots
        if num < shots[-1]["num"]:
            print(f"    Cooldown {COOLDOWN_BETWEEN_SHOTS}s...")
            time.sleep(COOLDOWN_BETWEEN_SHOTS)

    elapsed    = (time.time() - t0) / 60
    n_ok       = sum(1 for v in generation_results.values() if v in ("ok", "cached"))
    n_failed   = sum(1 for v in generation_results.values()
                     if v not in ("ok", "cached", ) and not v.startswith("skipped"))
    n_skipped  = sum(1 for v in generation_results.values() if v.startswith("skipped"))
    print(f"\n  Generation: {elapsed:.1f} min | "
          f"{n_ok} OK | {n_failed} failed | {n_skipped} skipped")

    # ── 3. Process clips ───────────────────────────────────────────────────────
    print(f"\n[3/4] Processing clips (scale · loop · overlay)...")
    t0        = time.time()
    processed: list[Path] = []

    for shot in shots:
        num  = shot["num"]
        raw  = FOOTAGE_DIR   / f"shot_{num:02d}_raw.mp4"
        proc = PROCESSED_DIR / f"shot_{num:02d}_processed.mp4"
        gen_result = generation_results.get(num, "unknown")

        # Use cached processed file only if it came from a real (non-placeholder) raw
        if (proc.exists()
                and proc.stat().st_size > 10_000
                and gen_result in ("ok", "cached")):
            print(f"  Shot {num:02d}: processed cached")
        else:
            ov_note = " + overlay" if shot["overlay"] else ""
            print(f"  Shot {num:02d}: {shot['duration']:.1f}s{ov_note}"
                  f"  [{gen_result}]")
            process_clip(raw, proc, shot["duration"], shot["overlay"])

        processed.append(proc)

    print(f"  Processing: {time.time() - t0:.0f}s")

    # ── 4. Assemble ────────────────────────────────────────────────────────────
    print(f"\n[4/4] Assembling final video...")
    t0 = time.time()
    ok = assemble(processed, VOICEOVER, OUTPUT)

    if ok and OUTPUT.exists():
        size_mb   = OUTPUT.stat().st_size / 1_048_576
        final_dur = get_duration(OUTPUT)
        print(f"\n{'=' * 62}")
        print(f"  COMPLETE")
        print(f"  File:     {OUTPUT}")
        print(f"  Size:     {size_mb:.1f} MB")
        print(f"  Duration: {fmt_duration(final_dur)}")
        print(f"  Assembly: {time.time() - t0:.0f}s")
        print(f"\n  Shot-by-shot results:")
        for num in sorted(generation_results.keys()):
            marker = "OK" if generation_results[num] in ("ok", "cached") else "!!"
            print(f"    [{marker}] Shot {num:>2}: {generation_results[num]}")
        failed_now = load_failed_shots()
        if failed_now:
            print(f"\n  Shots still in failed_shots.json: {list(failed_now.keys())}")
            print(f"  Re-run with --resume to retry them.")
        print(f"{'=' * 62}")
    else:
        print("\n!! Assembly failed — check warnings above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
