"""Direct pilot evidence checks. No generation, sourcing, render or upload calls.

All record paths are workspace-relative. Reports bind bytes, not filenames alone.
These checks do not decide whether rights, a human decision or creative QA are true;
the named operator must preserve the actual evidence and decision in each receipt.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


class EvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def local(root, name):
    require(isinstance(name, str) and bool(name.strip()), "Missing path")
    relative = Path(name)
    require(not relative.is_absolute() and ".." not in relative.parts, "Expected workspace-relative path")
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), "Path escapes workspace")
    require(path.is_file() and path.stat().st_size > 0, f"Missing/empty file: {name}")
    return path


def describe(root, name):
    path = local(root, name)
    return {"path": path.relative_to(root.resolve()).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


def bound(root, record):
    require(isinstance(record, dict), "Missing file binding")
    actual = describe(root, record.get("path"))
    require(actual == record, f"Stale or noncanonical file binding: {record.get('path')}")
    return actual


def decision(record):
    require(isinstance(record, dict) and record.get("human_approved") is True, "Human decision required")
    for key in ("approved_by", "user_quote", "scope"):
        require(isinstance(record.get(key), str) and bool(record[key].strip()), f"Missing human decision {key}")
    timestamp = record.get("approved_on") or record.get("approved_at")
    require(isinstance(timestamp, str) and bool(timestamp.strip()), "Missing human decision date")
    try:
        datetime.fromisoformat(timestamp)
    except ValueError:
        raise EvidenceError("Invalid human decision date") from None


def narration_text(path):
    """Extract only marked narration paragraphs. Reject unrecognized editorial syntax."""
    text = Path(path).read_text(encoding="utf-8-sig")
    require(text.count("<!-- NARRATION_START -->") == 1 and text.count("<!-- NARRATION_END -->") == 1,
            "Exactly one narration region required")
    region = text.split("<!-- NARRATION_START -->")[1].split("<!-- NARRATION_END -->")[0]
    region = re.sub(r"(?m)^<!-- P\d+ -->\s*\n", "", region)
    paragraphs = []
    for block in re.split(r"\n\s*\n", region.strip()):
        block = block.strip()
        if block.startswith("#") or re.fullmatch(r"<!-- P\d+ -->", block) or re.fullmatch(r"\[B-ROLL: .*\]", block):
            continue
        require(not any(token in block for token in ("<!--", "-->", "[[", "]]", "[B-ROLL:")),
                "Unrecognized narration markup")
        paragraphs.append(block)
    require(bool(paragraphs), "Empty narration")
    return "\n\n".join(paragraphs) + "\n"


def approval(root, approval_path):
    record = read(local(root, approval_path))
    require(record.get("schema_version") == "cold_truth.paired_script_approval.v1", "Wrong approval schema")
    decision(record)
    require(record.get("target_format") in ("youtube-longform", "shorts"), "Unknown target format")
    packet = read(local(root, bound(root, record["review_packet"])["path"]))
    require(record.get("review_id") == packet.get("review_id"), "Review ID mismatch")
    require(record.get("case_id") == packet.get("case_id") and record["target_format"] == packet.get("target_format"),
            "Case/format mismatch")
    for key in ("script", "reverse_outline"):
        require(record[key] == packet[key], f"Review binding mismatch: {key}")
        bound(root, record[key])
    for item in packet["supporting_inputs"]:
        bound(root, item)
    bound(root, record["final_script"])
    bound(root, record["narration_text"])
    draft_text = narration_text(local(root, record["script"]["path"]))
    require(draft_text == narration_text(local(root, record["final_script"]["path"])), "Approved narration changed")
    require(draft_text.encode("utf-8") == local(root, record["narration_text"]["path"]).read_bytes(),
            "Narration extraction changed")
    return record


def finite(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise EvidenceError("Invalid duration") from None
    require(result.is_finite() and result > 0, "Duration must be finite and positive")
    return result


def probe_audio(path, executable=None):
    binary = executable or shutil.which("ffprobe")
    require(bool(binary), "FFprobe is unavailable")
    try:
        result = subprocess.run([str(binary), "-v", "error", "-select_streams", "a:0", "-show_entries",
                                 "stream=duration", "-of", "json", str(path)],
                                capture_output=True, text=True, check=True, timeout=30)
        streams = json.loads(result.stdout)["streams"]
        require(len(streams) == 1, "Exactly one selected audio stream required")
        return finite(streams[0]["duration"])
    except (subprocess.SubprocessError, OSError, ValueError, KeyError, TypeError) as exc:
        raise EvidenceError(f"Audio stream probe failed: {type(exc).__name__}") from exc


def exception_valid(root, item, request, kind):
    if item is None:
        return False
    bound(root, item)
    record = read(local(root, item["path"]))
    decision(record)
    require(record.get("exception_type") == kind and record.get("case_id") == request["case_id"]
            and record.get("case") == request["case_name"]
            and record.get("target_format") == request["target_format"], "Exception scope mismatch")
    require(bool(record.get("approved_at", "").strip()), "Exception timestamp required")
    try:
        require(datetime.fromisoformat(record["approved_at"]).tzinfo is not None, "Exception timestamp needs timezone")
    except ValueError:
        raise EvidenceError("Invalid exception timestamp") from None
    require(record.get("script") == request["script"] and record.get("audio") == request["audio"],
            "Exception must bind exact script/audio")
    require(bool(record.get("reason", "").strip()), "Exception reason required")
    if kind == "short-format":
        summary = bound(root, record["production_summary"])
        require("Short-Format" in local(root, summary["path"]).read_text(encoding="utf-8-sig"),
                "Production Summary must label Short-Format")
    return True


def audio_preflight(root, request_path, probe=probe_audio):
    request_binding = describe(root, request_path)
    request = read(local(root, request_path))
    bound(root, request["script_approval"])
    approved = approval(root, request["script_approval"]["path"])
    require(request["case_id"] == approved["case_id"] and request["target_format"] == approved["target_format"],
            "Audio case/format mismatch")
    require(request["script"] == approved["final_script"] and request["narration_text"] == approved["narration_text"],
            "Audio script mismatch")
    for key in ("script", "narration_text", "audio", "phase_2_scope", "generation_manifest", "audio_qa"):
        bound(root, request[key])
    scope = read(local(root, request["phase_2_scope"]["path"]))
    decision(scope)
    require(scope.get("case_id") == request["case_id"] and scope.get("target_format") == request["target_format"]
            and scope.get("script") == request["script"] and scope.get("narration_text") == request["narration_text"],
            "Phase 2 scope mismatch")
    require("narration" in scope.get("authorized_actions", []) and request["audio"]["path"] in scope.get("output_paths", []),
            "Audio outside authorized scope")
    qa = read(local(root, request["audio_qa"]["path"]))
    decision(qa)
    require(qa.get("audio") == request["audio"] and qa.get("script") == request["script"]
            and qa.get("full_listen_passed") is True, "Current audio needs full-listen QA")
    manifest = read(local(root, request["generation_manifest"]["path"]))
    events = [e for e in manifest.get("entries", []) if e.get("event_id") == request["generation_event_id"]]
    require(len(events) == 1, "Missing/duplicate generation event")
    event = events[0]
    require(event.get("case_id") == request["case_id"] and event.get("target_format") == request["target_format"]
            and event.get("script") == request["script"] and event.get("narration_text") == request["narration_text"]
            and event.get("phase_2_scope") == request["phase_2_scope"], "Generation provenance mismatch")
    require(request["audio"] in event.get("outputs", []) and bool(event.get("tool")) and bool(event.get("recorded_at_utc"))
            and event.get("settings") == scope.get("settings") and bool(event.get("settings")), "Incomplete generation provenance")
    duration = probe(local(root, request["audio"]["path"]))
    duration = finite(duration)
    # Never round before policy decisions. A stream duration, never container duration.
    kind = "short-format" if request["target_format"] == "youtube-longform" else "shorts-over-60"
    needs_exception = duration < 480 if kind == "short-format" else duration > 60
    valid_exception = exception_valid(root, request.get("exception"), request, kind)
    flags = []
    if needs_exception and not valid_exception:
        flags.append("LONGFORM_BELOW_480" if kind == "short-format" else "SHORTS_OVER_60")
    if request["target_format"] == "shorts" and duration < 30:
        flags.append("below_shorts_target")
    if request["target_format"] == "youtube-longform" and 480 <= duration < 495:
        flags.append("below_preferred_working_range")
    if request["target_format"] == "youtube-longform" and duration > 630:
        flags.append("above_preferred_working_range")
    allowed = not needs_exception or valid_exception
    if kind == "short-format":
        status = ("pass_with_short_format_exception" if valid_exception else "blocked_under_8_minimum") if needs_exception else (
            "pass_preferred_range" if 495 <= duration <= 630 else "pass_minimum_with_range_flag")
    else:
        status = ("pass_with_shorts_over_60_exception" if valid_exception else "blocked_over_shorts_maximum") if needs_exception else (
            "pass_shorts_range" if duration >= 30 else "pass_below_shorts_target")
    # Recheck after external probing; never issue a pass for inputs changed during it.
    require(request_binding == describe(root, request_path), "Request changed during probe")
    bound(root, request["script_approval"])
    approval(root, request["script_approval"]["path"])
    for key in ("script", "narration_text", "audio", "phase_2_scope", "generation_manifest", "audio_qa"):
        bound(root, request[key])
    if request.get("exception"):
        bound(root, request["exception"])
    return {"schema_version": "cold_truth.direct_audio_preflight.v1", "case_id": request["case_id"],
            "target_format": request["target_format"], "request": request_binding,
            "narration_file": request["audio"]["path"], "narration_duration_seconds": float(duration),
            "duration_exact_decimal": str(duration), "duration_source": "ffprobe_audio_stream",
            "word_count_used_for_duration": False, "assembly_allowed": allowed,
            "status": status, "flags": flags,
            "validated_exception": request.get("exception") if valid_exception else None,
            "bindings": {k: request[k] for k in ("script_approval", "script", "narration_text", "audio", "phase_2_scope", "generation_manifest", "audio_qa")},
            "scope": "Audio gate only; assets/alignment and applicable assembly authority also required"}


def assets(root, registry_path):
    registry = read(local(root, registry_path))
    require(registry.get("synthetic") is False, "Real-file registry must declare synthetic false")
    pools = {}
    counts = {}
    for track, allowed in (("youtube-longform", {"pexels_broll", "case_graphic"}), ("shorts", {"orbital_gameplay"})):
        entries = registry.get(track)
        require(isinstance(entries, list) and bool(entries), f"Empty {track} pool")
        identities = {key: set() for key in ("asset_id", "source_identity", "path", "sha256")}
        classes = set()
        for entry in entries:
            require(entry.get("asset_class") in allowed, "Prohibited visual class")
            classes.add(entry["asset_class"])
            media = bound(root, entry["file"])
            evidence = bound(root, entry["license_evidence"])
            review = read(local(root, bound(root, entry["rights_review"])["path"]))
            decision(review)
            require(review.get("asset") == media and review.get("license_evidence") == evidence
                    and review.get("source_identity") == entry.get("source_identity")
                    and review.get("permitted_track") == track and review.get("commercial_use_reviewed") is True,
                    "Rights review mismatch")
            require(isinstance(review.get("credits"), str) and bool(review["credits"].strip()),
                    "Credits or explicit no-attribution rationale required")
            for key in identities:
                value = media[key] if key in ("path", "sha256") else entry.get(key)
                require(isinstance(value, str) and bool(value.strip()), "Missing asset identity")
                value = value.strip().casefold()
                require(value not in identities[key], f"Duplicate {track} asset {key}")
                identities[key].add(value)
        if track == "youtube-longform":
            require("pexels_broll" in classes, "Required downloaded Pexels clips absent")
        pools[track] = identities
        counts[track] = len(entries)
    for key in pools["youtube-longform"]:
        require(not pools["youtube-longform"][key] & pools["shorts"][key], f"Cross-track collision: {key}")
    # Physical aliases such as hardlinks are sharing even with different names.
    for lf in registry["youtube-longform"]:
        for sh in registry["shorts"]:
            require(not local(root, lf["file"]["path"]).samefile(local(root, sh["file"]["path"])), "Shared physical file")
    return {"status": "PASS_FILE_RIGHTS_ISOLATION", "registry": describe(root, registry_path),
            "counts": counts, "media_content_or_legal_validity_certified": False}


def words(text):
    return re.findall(r"\w+(?:['’]\w+)*", text.casefold())


def alignment(root, alignment_path, preflight):
    record = read(local(root, alignment_path))
    require(preflight.get("assembly_allowed") is True, "Audio preflight blocked")
    for key in ("audio", "script", "narration_text"):
        require(record.get(key) == preflight["bindings"][key], "Stale alignment")
        bound(root, record[key])
    decision(record.get("timing_review"))
    require(record["timing_review"].get("full_listen_passed") is True, "Timing playback review required")
    require(bool(record.get("tool")) and bool(record.get("recorded_at_utc")), "Alignment provenance missing")
    duration = finite(preflight["duration_exact_decimal"])
    previous = Decimal(0)
    segments = record.get("segments", [])
    require(isinstance(segments, list) and bool(segments), "No alignment segments")
    for segment in segments:
        try:
            start, end = Decimal(str(segment["start"])), finite(segment["end"])
        except (InvalidOperation, KeyError):
            raise EvidenceError("Invalid alignment time") from None
        require(start.is_finite() and previous <= start < end <= duration, "Invalid/overlapping alignment times")
        require(end - start <= 6 and bool(words(segment.get("text", ""))), "Caption must contain text and last at most six seconds")
        previous = end
    expected = local(root, record["narration_text"]["path"]).read_text(encoding="utf-8")
    require(words(" ".join(s["text"] for s in segments)) == words(expected), "Alignment omits/adds/reorders spoken words")
    return record


def srt(record):
    def stamp(value):
        milliseconds = int(Decimal(str(value)) * 1000)
        seconds, ms = divmod(milliseconds, 1000)
        minutes, sec = divmod(seconds, 60)
        hours, minute = divmod(minutes, 60)
        return f"{hours:02}:{minute:02}:{sec:02},{ms:03}"
    for segment in record["segments"]:
        require(stamp(segment["start"]) != stamp(segment["end"]), "Caption collapses at millisecond resolution")
    return "\n\n".join(f"{i}\n{stamp(s['start'])} --> {stamp(s['end'])}\n{s['text']}"
                         for i, s in enumerate(record["segments"], 1)) + "\n"


def new_output(root, path):
    require(path.resolve().is_relative_to(root.resolve()), "Output escapes workspace")
    return path.open("x", encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="New JSON report; never overwrites")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("approval", "audio", "assets"):
        commands.add_parser(name).add_argument("record")
    align = commands.add_parser("alignment")
    align.add_argument("record")
    align.add_argument("audio_request")
    align.add_argument("--srt-output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "approval":
            result = approval(root, args.record)
            result = {"status": "PASS_PAIRED_SCRIPT_BINDINGS", "approval": describe(root, args.record),
                      "final_script": result["final_script"], "phase_2_authorized": False}
        elif args.command == "audio":
            result = audio_preflight(root, args.record)
        elif args.command == "assets":
            result = assets(root, args.record)
        else:
            preflight = audio_preflight(root, args.audio_request)
            record = alignment(root, args.record, preflight)
            result = {"status": "PASS_ALIGNMENT_CONTRACT", "alignment": describe(root, args.record), "audio_preflight": preflight}
            if args.srt_output:
                captions = srt(record)
                with new_output(root, args.srt_output) as handle:
                    handle.write(captions)
        result["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
        if args.output:
            with new_output(root, args.output) as handle:
                json.dump(result, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result.get("assembly_allowed") is False:
            raise SystemExit(1)
    except (EvidenceError, KeyError, TypeError, OSError, ValueError) as exc:
        parser.exit(1, f"BLOCKED: {exc}\n")


if __name__ == "__main__":
    main()
