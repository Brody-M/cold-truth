"""Quarantined legacy stage helpers; canonical state belongs to orchestrator.py."""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "Brody's Vault"
VOICE_CONFIG = VAULT / "2_CHANNEL_SYSTEM" / "NARRATION_VOICE.md"
TARGET_FORMATS = ("youtube-longform", "shorts")
LONGFORM_RELEASE_MINIMUM_SECONDS = 480.0
LONGFORM_PREFERRED_MINIMUM_SECONDS = 495.0
LONGFORM_PREFERRED_MAXIMUM_SECONDS = 630.0
SHORTS_TARGET_MINIMUM_SECONDS = 30.0
SHORTS_MAXIMUM_SECONDS = 60.0

def safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "untitled"

class LegacyPipelineQuarantined(RuntimeError):
    """The legacy CLI attempted a canonical write or execution capability."""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _pipeline_manifest_entry(case: str, stage: str, payload: dict, handoff_path: Path) -> dict:
    return {
        "event_id": hashlib.sha256(f"{case}|{stage}|{_now()}".encode()).hexdigest()[:16],
        "schema_version": "1.0",
        "stage": stage,
        "timestamp": _now(),
        "tool": "automation/cold_truth_pipeline.py",
        "tool_calls": [{
            "tool": payload.get("provider", "local_stage_adapter"),
            "action": stage,
            "executed": payload.get("status") not in {"planned", "ready_for_skill", "required_after_generation"},
        }],
        "settings": {"arguments": sys.argv[1:]},
        "outputs": [{"path": str(handoff_path.resolve()), "sha256": _file_sha256(handoff_path), "size_bytes": handoff_path.stat().st_size}],
        "results": {
            "status": payload.get("status"),
            "provider": payload.get("provider"),
            "assembly_allowed": payload.get("assembly_allowed"),
            "publish": payload.get("publish", False),
        },
        "decisions": payload.get("flags", []),
        "verification": {"secrets_recorded": False, "publishing_enabled": False},
    }

def _isolated_root(path: Path | None) -> Path:
    if path is None:
        raise LegacyPipelineQuarantined("Legacy handoffs require an explicit isolated fixture root")
    root = path.expanduser().resolve()
    try:
        root.relative_to(ROOT)
    except ValueError:
        pass
    else:
        raise LegacyPipelineQuarantined("Legacy fixture root must be outside the Cold Truth workspace")
    return root

def _require_contained(path: Path, root: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise LegacyPipelineQuarantined(f"{label} must stay inside the isolated fixture root") from exc
    return resolved

def write_handoff(case: str, stage: str, payload: dict, *, isolated_root: Path | None = None, fixture_only: bool = False) -> Path:
    if fixture_only is not True:
        raise LegacyPipelineQuarantined("Legacy handoffs are fixture-only")
    root = _isolated_root(isolated_root)
    folder = root / safe_id(case) / "Automation"; folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{safe_id(stage)}.json"; path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    manifest_path = folder / "legacy_fixture_manifest.json"
    if manifest_path.exists():
        try: manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError: raise RuntimeError(f"Invalid existing pipeline manifest: {manifest_path}")
    else:
        manifest = {"case": case, "manifest_version": "legacy_fixture_quarantine.v1", "authoritative": False, "canonical_state_owner": "automation/orchestrator.py", "publishing_enabled": False, "entries": []}
    manifest["entries"].append(_pipeline_manifest_entry(case, stage, payload, path))
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path

def validate_script_approval(path: Path | None, *, case: str, script_file: Path | None = None) -> dict:
    if path is None:
        raise RuntimeError("External execution requires --script-approval bound to Human Checkpoint 1.")
    approval = json.loads(path.read_text(encoding="utf-8"))
    if approval.get("checkpoint") != "script" or approval.get("human_approved") is not True:
        raise RuntimeError("Script approval must be a Human Checkpoint 1 approval with human_approved=true.")
    approval_case = approval.get("case")
    approval_case_id = approval.get("case_id")
    if approval_case is None and approval_case_id is None:
        raise RuntimeError("Script approval must identify case or case_id.")
    if approval_case not in (None, case) or approval_case_id not in (None, safe_id(case)):
        raise RuntimeError("Script approval does not match the requested case.")
    for field in ("approved_by", "approved_at", "reason"):
        if not isinstance(approval.get(field), str) or not approval[field].strip():
            raise RuntimeError(f"Script approval field {field} is required.")
    if script_file is not None:
        digest = _file_sha256(script_file.resolve())
        approved_hashes = {approval.get("script_draft_sha256"), approval.get("script_final_sha256")}
        if digest not in approved_hashes:
            raise RuntimeError("Script approval hash does not match the narration text file.")
    return approval

def narration_voice_config() -> dict:
    text = VOICE_CONFIG.read_text(encoding="utf-8")

    def value(name: str) -> str:
        match = re.search(rf"^{re.escape(name)}:\s*['\"]?([^'\"\s]+)", text, re.MULTILINE)
        if not match:
            raise RuntimeError(f"No {name} found in {VOICE_CONFIG}")
        return match.group(1)

    return {
        "voice_id": value("voice_id"),
        "model_id": value("model_id"),
        "stability": float(value("stability")),
        "similarity_boost": float(value("similarity_boost")),
        "style": float(value("style")),
        "speed": float(value("speed")),
        "use_speaker_boost": value("use_speaker_boost").lower() == "true",
        "output_format": value("output_format"),
    }

def narration_voice_id() -> str:
    return narration_voice_config()["voice_id"]

def _ffprobe_path() -> str:
    configured = os.environ.get("FFPROBE_PATH")
    candidate = configured or shutil.which("ffprobe")
    if not candidate:
        raise RuntimeError("FFprobe is required for narration preflight. Set FFPROBE_PATH or add ffprobe to PATH.")
    return str(candidate)

def audio_duration_seconds(path: Path) -> float:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"Narration audio does not exist: {path}")
    command = [
        _ffprobe_path(), "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=duration:format=duration", "-of", "json", str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"FFprobe could not measure narration audio: {completed.stderr.strip()}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("FFprobe returned invalid JSON for narration audio.") from exc
    streams = payload.get("streams", [])
    if not streams:
        raise RuntimeError("FFprobe found no audio stream in the narration file.")
    candidates = [stream.get("duration") for stream in streams]
    candidates.append(payload.get("format", {}).get("duration"))
    for value in candidates:
        try:
            duration = float(value)
        except (TypeError, ValueError):
            continue
        if duration >= 0:
            return duration
    raise RuntimeError("FFprobe found no measurable audio duration in the narration file.")

def _approval_metadata(path: Path | None, *, case: str, target_format: str, exception_type: str) -> tuple[dict | None, list[str]]:
    if path is None:
        return None, ["explicit human approval metadata is required"]
    try:
        approval = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"approval metadata does not exist: {path}"]
    except json.JSONDecodeError:
        return None, [f"approval metadata is not valid JSON: {path}"]
    errors = []
    if approval.get("case") != case: errors.append("approval case does not match")
    if approval.get("target_format") != target_format: errors.append("approval target_format does not match")
    if approval.get("exception_type") != exception_type: errors.append("approval exception_type does not match")
    if approval.get("human_approved") is not True: errors.append("human_approved must be true")
    for field in ("approved_by", "approved_at", "reason"):
        if not isinstance(approval.get(field), str) or not approval[field].strip(): errors.append(f"{field} is required")
    return ({**approval, "metadata_path": str(path.resolve())} if not errors else None), errors

def narration_preflight(case: str, target_format: str, narration_file: Path, approval_metadata: Path | None = None) -> dict:
    if target_format not in TARGET_FORMATS:
        raise RuntimeError(f"target_format must be one of: {', '.join(TARGET_FORMATS)}")
    narration_file = narration_file.expanduser().resolve()
    duration = round(audio_duration_seconds(narration_file), 6)
    flags: list[str] = []
    approval = None
    approval_errors: list[str] = []

    if target_format == "youtube-longform":
        if duration < LONGFORM_RELEASE_MINIMUM_SECONDS:
            approval, approval_errors = _approval_metadata(
                approval_metadata, case=case, target_format=target_format, exception_type="short-format"
            )
            if approval:
                status, assembly_allowed = "pass_with_short_format_exception", True
                flags.append("under_8_minimum_human_exception")
            else:
                status, assembly_allowed = "blocked_under_8_minimum", False
                flags.extend(["under_8_minimum", *approval_errors])
        elif duration < LONGFORM_PREFERRED_MINIMUM_SECONDS:
            status, assembly_allowed = "pass_release_minimum", True
            flags.append("below_preferred_working_range")
        elif duration <= LONGFORM_PREFERRED_MAXIMUM_SECONDS:
            status, assembly_allowed = "pass_preferred_range", True
        else:
            status, assembly_allowed = "pass_editorial_review_recommended", True
            flags.append("above_preferred_working_range")
        rule = {
            "target_seconds": [480.0, 600.0],
            "preferred_seconds": [495.0, 630.0],
            "release_minimum_seconds": 480.0,
            "exception_type": "short-format",
        }
    else:
        if duration > SHORTS_MAXIMUM_SECONDS:
            approval, approval_errors = _approval_metadata(
                approval_metadata, case=case, target_format=target_format, exception_type="shorts-over-60"
            )
            if approval:
                status, assembly_allowed = "pass_with_shorts_over_60_exception", True
                flags.append("over_shorts_maximum_human_exception")
            else:
                status, assembly_allowed = "blocked_over_shorts_maximum", False
                flags.extend(["over_shorts_maximum", *approval_errors])
        elif duration < SHORTS_TARGET_MINIMUM_SECONDS:
            status, assembly_allowed = "pass_below_shorts_target", True
            flags.append("below_shorts_target")
        else:
            status, assembly_allowed = "pass_shorts_range", True
        rule = {
            "target_seconds": [30.0, 60.0],
            "maximum_seconds": 60.0,
            "exception_type": "shorts-over-60",
        }

    return {
        "status": status,
        "case": case,
        "target_format": target_format,
        "narration_file": str(narration_file),
        "narration_duration_seconds": duration,
        "duration_source": "ffprobe_audio_stream",
        "word_count_used_for_duration": False,
        "assembly_allowed": assembly_allowed,
        "flags": flags,
        "rule": rule,
        "approval_metadata": approval,
    }

def pexels_search(query: str, execute: bool) -> dict:
    if not execute: return {"status":"planned","provider":"Pexels","query":query,"orientation":"landscape","downloads":False}
    raise LegacyPipelineQuarantined("Pexels execution is quarantined; use a separately certified orchestrator adapter")

def elevenlabs_voice(text: str, output: Path, execute: bool) -> dict:
    if execute:
        raise LegacyPipelineQuarantined("ElevenLabs execution is quarantined; use a separately certified orchestrator adapter")
    config=narration_voice_config(); voice_id=config["voice_id"]
    planned={"status":"planned","provider":"ElevenLabs","voice_id":voice_id,"output":str(output),"characters":len(text),"model_id":config["model_id"],"voice_settings":{key:config[key] for key in ("stability","similarity_boost","style","speed","use_speaker_boost")},"output_format":config["output_format"]}
    return planned

def thumbnail_prompts(video_id: str, title: str, hook: str, *, isolated_root: Path | None = None) -> dict:
    folder=(_isolated_root(isolated_root)/"thumbnails"/safe_id(video_id)) if isolated_root is not None else Path("quarantined_fixture_preview")/"thumbnails"/safe_id(video_id); variants=[]
    for number,(text,scene) in enumerate(zip(["THE CLUE","WHAT HAPPENED","HIDDEN TRUTH"],["a rain-streaked evidence board with red string and a blurred silhouette","an empty suburban street at blue hour with distant police lights","a sealed case file beside a shadowed doorway"]),1):
        variants.append({"variant":number,"filename":f"variant-{number}.png","prompt":f"Use case: ads-marketing. Asset type: 16:9 YouTube true-crime thumbnail. Primary request: create {scene}. Topic: {title}. Hook: {hook}. Text (verbatim): '{text}'. Composition: cinematic subject right, large readable text left, bold high-contrast condensed sans-serif. Lighting/mood: tense, elegant documentary. Constraints: no real victim likeness, no gore, no crime-scene photos, no logos, no watermark, no extra text."})
    return {"status":"ready_for_image_generation","video_id":video_id,"output_folder":str(folder),"variants":variants,"publish":False,"video_render":False}

def sentences(script: str) -> list[str]:
    # Headings are editorial metadata, not narration.
    body=re.sub(r"(?m)^#{1,6}\s+.*$", "", script)
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+",re.sub(r"\s+"," ",body).strip()) if x.strip()]

def visual_plan(script: str, video_id: str) -> dict:
    elapsed=0; longform=[]; shorts=[]; backgrounds=["licensed_orbital_gameplay_reference"]
    for i,unit in enumerate(sentences(script),1):
        duration=max(4,min(12,round(len(unit.split())/2.4))); start,end=elapsed,elapsed+duration; words=re.findall(r"[A-Za-z]{5,}",unit.lower())[:4] or ["documentary","investigation"]
        longform.append({"segment":i,"start_seconds":start,"end_seconds":end,"narration":unit,"track":"youtube_longform","visual_type":"pexels_broll_or_case_graphic","pexels_query":" ".join(words+["documentary"]),"orientation":"landscape","asset_status":"search_reference_only","downloads":False})
        shorts.append({"segment":i,"start_seconds":start,"end_seconds":end,"narration":unit,"track":"shorts_vertical","visual_type":"gameplay_background_reference","background_reference":backgrounds[(i-1)%2],"overlay_text":unit[:90],"asset_status":"reference_only","shared_with_youtube":False}); elapsed=end
    return {"status":"planned","video_id":video_id,"runtime_estimate_seconds":elapsed,"runtime_estimate_is_not_duration_verification":True,"rules":{"youtube":"Pexels B-roll/case graphics only","shorts":"separately licensed Orbital gameplay only","shared_assets":False,"assembly_requires_audio_preflight":True,"video_render":False},"youtube_timeline":longform,"shorts_timeline":shorts}

def metadata_package(case: str,title: str,hook: str) -> dict:
    primary=title if len(title)<60 else title[:57].rstrip()+"..."
    tags=["true crime","true crime documentary","unsolved mystery","cold case","crime story","Cold Truth","documentary","crime investigation","mystery documentary","case timeline","female true crime audience","true crime YouTube","criminal investigation","missing clues","real cases"]
    description=f"{title} is examined in this calm, source-led Cold Truth episode. {hook} We follow the verified timeline, investigation, and remaining questions, clearly separating confirmed facts from unresolved details. This episode is presented respectfully and avoids graphic material.\n\nCold Truth covers carefully researched true-crime cases with context, chronology, and restraint. Sources and corrections should be reviewed against the final research brief before publishing.\n\nLocation: [verify] | Year: [verify]"
    return {"status":"draft_requires_fact_check","case":case,"titles":[primary,f"The Overlooked Clue in {primary}"[:59],f"Inside the Mystery of {primary}"[:59]],"description":description,"tags":tags,"thumbnail_text_options":["THE CLUE","HIDDEN TRUTH"],"recommended_settings":{"schedule":"Tuesday or Thursday, 10 AM-12 PM ET","category":"News & Politics","made_for_kids":False,"comments":True,"end_screen":True,"cards_at_percent":[20,60]},"publish":False}

def handoff_stage(case,stage,source): return {"status":"ready_for_skill","case":case,"stage":stage,"skill":{"ideas":"cold-truth-strategist","write":"cold-truth-writer","edit":"cold-truth-editor"}[stage],"source":source}
def upload_manifest(case,source): return {"status":"prepared_not_uploaded","case":case,"metadata_source":source,"requires":["rendered_video_path","approved_thumbnail_path","separately enabled future publishing mode","YouTube OAuth"],"publish_block":"Publishing mode is not implemented or authorized"}

def main():
    p=argparse.ArgumentParser(description="Quarantined Cold Truth legacy helpers; isolated fixtures only")
    p.add_argument("stage",choices=["ideas","write","edit","broll","voice","preflight","metadata","thumbnail","visuals","upload"]); p.add_argument("--case",required=True); p.add_argument("--source",default=""); p.add_argument("--query",default=""); p.add_argument("--text-file",type=Path); p.add_argument("--script-file",type=Path); p.add_argument("--narration-file",type=Path); p.add_argument("--approval-metadata",type=Path); p.add_argument("--script-approval",type=Path); p.add_argument("--target-format",choices=TARGET_FORMATS); p.add_argument("--video-id",default=""); p.add_argument("--title",default=""); p.add_argument("--hook",default=""); p.add_argument("--execute",action="store_true",help="Always rejected: provider execution is quarantined."); p.add_argument("--fixture-only",action="store_true"); p.add_argument("--isolated-run-root",type=Path); a=p.parse_args()
    if a.fixture_only is not True or a.isolated_run_root is None:
        raise SystemExit("Legacy pipeline is quarantined: require --fixture-only and --isolated-run-root outside the workspace")
    isolated_root = _isolated_root(a.isolated_run_root)
    if a.execute:
        raise SystemExit("Legacy pipeline execution is quarantined; --execute is forbidden")
    for label, candidate in (("text file", a.text_file), ("script file", a.script_file), ("narration file", a.narration_file), ("approval metadata", a.approval_metadata), ("script approval", a.script_approval)):
        if candidate is not None:
            _require_contained(candidate, isolated_root, label)
    if a.stage in {"ideas","write","edit"}: result=handoff_stage(a.case,a.stage,a.source)
    elif a.stage=="broll":
        if a.execute: validate_script_approval(a.script_approval,case=a.case)
        result=pexels_search(a.query or a.source,a.execute)
    elif a.stage=="voice":
        if not a.text_file: raise SystemExit("voice requires --text-file")
        if not a.target_format: raise SystemExit("voice requires --target-format")
        if a.execute: validate_script_approval(a.script_approval,case=a.case,script_file=a.text_file)
        output=isolated_root/safe_id(a.case)/"Voiceover.mp3"
        result={**elevenlabs_voice(a.text_file.read_text(encoding="utf-8"),output,a.execute),"target_format":a.target_format}
        if a.execute:
            preflight=narration_preflight(a.case,a.target_format,output,a.approval_metadata)
            write_handoff(a.case,"preflight",preflight,isolated_root=isolated_root,fixture_only=True); result["preflight"]=preflight
        else:
            result["preflight"]={"status":"required_after_generation","word_count_used_for_duration":False,"assembly_allowed":False}
    elif a.stage=="preflight":
        if not a.target_format: raise SystemExit("preflight requires --target-format")
        if not a.narration_file: raise SystemExit("preflight requires --narration-file")
        result=narration_preflight(a.case,a.target_format,a.narration_file,a.approval_metadata)
    elif a.stage=="thumbnail":
        if not (a.video_id and a.title and a.hook): raise SystemExit("thumbnail requires --video-id, --title, and --hook")
        result=thumbnail_prompts(a.video_id,a.title,a.hook,isolated_root=isolated_root); folder=Path(result["output_folder"]); folder.mkdir(parents=True,exist_ok=True); (folder/"thumbnail_prompts.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    elif a.stage=="visuals":
        if not (a.script_file and a.video_id): raise SystemExit("visuals requires --script-file and --video-id")
        result=visual_plan(a.script_file.read_text(encoding="utf-8"),a.video_id)
    elif a.stage=="metadata":
        if not (a.title and a.hook): raise SystemExit("metadata requires --title and --hook")
        result=metadata_package(a.case,a.title,a.hook)
    else: result=upload_manifest(a.case,a.source)
    path=write_handoff(a.case,a.stage,result,isolated_root=isolated_root,fixture_only=True); print(json.dumps({"result":result,"handoff":str(path)},indent=2))
    blocked = (a.stage=="preflight" and not result["assembly_allowed"]) or (a.stage=="voice" and a.execute and not result["preflight"]["assembly_allowed"])
    if blocked: raise SystemExit(2)
if __name__=="__main__": main()
