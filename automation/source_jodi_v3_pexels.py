"""Source distinct Pexels candidates for the approved Jodi v2 visual beats.

Reads PEXELS_API_KEY only from the process environment. It never writes secrets.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

ROOT = Path(r"C:\Youtube Automation Obsidian\Brody's Vault\2_IN_PRODUCTION\Jodi Huisentruit")
SOURCE_XML = ROOT / "Assembly" / "Jodi_Huisentruit_Longform_Preview_v2.fcpxml"
OUT_DIR = ROOT / "footage_v3"
LEDGER = ROOT / "Assembly" / "Pexels_Sourcing_v3.json"
TIMELINE = ROOT / "YouTube_Visual_Timeline_v3.md"
OUT_XML = ROOT / "Assembly" / "Jodi_Huisentruit_Longform_Preview_v3.fcpxml"

# Three distinct, safe, landscape-oriented Pexels searches for every moving beat.
Q = {
 1:["analog alarm clock before sunrise","early morning desk clock dark","telephone beside clock dawn"],
 2:["empty television studio morning","broadcast control room empty","newsroom monitors before broadcast"],
 3:["emergency dispatch desk keyboard","operator headset computer desk","emergency call center empty"],
 4:["wet parking lot streetlights","rainy asphalt close up night","empty pavement dawn rain"],
 5:["case file papers desk","manila folder documents closeup","evidence list paperwork"],
 6:["personal items on desk flat lay","keys earrings desk closeup","women accessories desk still life"],
 7:["calendar june close up","date marked calendar desk","analog clock calendar morning"],
 8:["quiet neighborhood dusk empty","streetlights residential evening","empty street blue hour"],
 9:["archival documents desk","paper records closeup dark","open file unanswered questions"],
10:["empty television newsroom","broadcast studio empty desk","control room monitors blue light"],
11:["calendar date close up","morning clock office desk","empty workplace sunrise"],
12:["timeline documents desk","case notes table close up","investigation paperwork hands"],
13:["empty office chair morning","unoccupied desk lamp","quiet workplace before dawn"],
14:["dispatch workstation keyboard","emergency communications office","headset desk computer"],
15:["documents evidence folder","file papers desk close up","case record tabletop"],
16:["foggy lake morning","misty water quiet","unknown mystery landscape fog"],
17:["closed case file desk","documents shadow light","paperwork unanswered questions"],
18:["investigation timeline notes","public records file","document archive close up"],
19:["clock and paperwork desk","timeline clock close up","documents beside clock"],
20:["organized case documents","paper notes investigation","file folder desktop"],
21:["fog over lake still","empty road fog dawn","quiet unknown landscape"],
22:["phone on empty desk","early morning office empty","clock on desk dawn"],
23:["emergency dispatch computer","headset workstation office","generic call center desk"],
24:["wet pavement rain night","parking lot rain reflections","dark asphalt close up"],
25:["keys and papers desk","red shoes still life","personal belongings flat lay"],
26:["official records documents","case file close up","paperwork desk neutral"],
27:["empty road dawn fog","quiet parking lot morning","lonely street sunrise"],
28:["empty newsroom desk","office monitors no people","workplace before sunrise"],
29:["dispatch keyboard hands","emergency operator desk","communications workstation"],
30:["public information board","community bulletin board papers","missing person notice board generic"],
31:["contact information paperwork","phone and documents desk","public service notice board"],
32:["detective notes desk","investigation files closeup","paper records search"],
33:["rural winter tree line","empty field winter","country road cold weather"],
34:["winter documents desk","search report paperwork","rural map on desk"],
35:["sealed public record file","restricted documents folder","closed archive box"],
36:["locked filing cabinet","private records drawer","archive files shadow"],
37:["legal documents close up","court papers desk","warrant paperwork generic"],
38:["sealed envelope desk","confidential file folder","locked archive document"],
39:["legal papers neutral desk","closed file no conclusion","court documents shadow"],
40:["foggy lake unresolved","empty archive hallway","closed file desk"],
41:["investigation papers desk","detective notebook close up","case file ongoing"],
42:["legal documents restraint","paperwork quiet desk","closed folder evidence"],
43:["documents and magnifying glass","case file desk neutral","paper records close up"],
45:["anniversary calendar pages","clock time passing desk","june calendar close up"],
46:["quiet neighborhood porch light","street at dusk empty","residential evening lights"],
47:["foggy lake dusk","empty road twilight","quiet landscape unanswered"],
48:["public records information desk","notice board contact information","paper files community office"],
49:["case file open desk","documents not solved","investigation notes neutral"],
50:["fog lake morning","quiet water mist","empty landscape dawn"],
51:["quiet neighborhood evening","empty residential street dusk","porch light twilight"],
52:["clock keys papers desk","parking lot rain abstract","timeline evidence documents"],
53:["foggy landscape unknown","empty road mist","quiet lake fog"],
54:["information desk paperwork","contact phone documents","public service office notice"],
55:["phone beside documents desk","tip line telephone office","contact information paperwork"],
56:["quiet porch light dusk","empty neighborhood evening","memorial candle window"],
57:["foggy lake sunrise","quiet road first light","dark paper texture landscape"],
}

def sec(value: str) -> float:
    if value == "0s": return 0.0
    a, b = re.match(r"^(\d+)/(\d+)s$", value).groups()
    return int(a) / int(b)

def fmt(value: float) -> str:
    return f"{int(round(value * 1000))}/1000s"

def uri(path: Path) -> str:
    return "file:///" + urllib.parse.quote(str(path).replace("\\", "/"), safe="/:" )

def choose_file(video: dict, needed: float) -> dict | None:
    if video.get("duration", 0) < needed: return None
    files = [f for f in video.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("width", 0) >= 1280 and f.get("height", 0) >= 720]
    if not files: return None
    # Smallest qualifying HD file limits storage while retaining 16:9 edit quality.
    return sorted(files, key=lambda f: (f["width"] * f["height"], f.get("fps", 30)))[0]

def search(session: requests.Session, phrase: str) -> list[dict]:
    response = session.get("https://api.pexels.com/videos/search", params={"query": phrase, "orientation": "landscape", "per_page": 10}, timeout=45)
    response.raise_for_status()
    return response.json().get("videos", [])

def main() -> None:
    key = os.environ.get("PEXELS_API_KEY")
    if not key: raise RuntimeError("PEXELS_API_KEY is required in the process environment.")
    tree = ET.parse(SOURCE_XML)
    root = tree.getroot()
    resources = root.find("resources")
    audio = next(a for a in resources.findall("asset") if a.get("hasAudio") == "1")
    spine = root.find("./library/event/project/sequence/spine")
    nodes = [n for n in list(spine) if n.tag in {"asset-clip", "gap"} and n.get("lane") != "-1"]
    OUT_DIR.mkdir(exist_ok=True)
    session = requests.Session(); session.headers["Authorization"] = key
    used_ids: set[int] = set(); ledger: list[dict] = []; selected: dict[int, dict] = {}
    for ordinal, node in enumerate(nodes, 1):
        duration = sec(node.get("duration")); offset = sec(node.get("offset")); name = node.get("name", "")
        if node.tag == "gap":
            ledger.append({"beat": ordinal, "name": name, "offset_seconds": offset, "duration_seconds": duration, "status": "case_card_placeholder", "queries": []})
            continue
        phrases = Q[ordinal]
        candidates: list[tuple[str, dict, dict]] = []
        for phrase in phrases:
            try:
                videos = search(session, phrase)
            except requests.RequestException as exc:
                ledger.append({"beat": ordinal, "name": name, "offset_seconds": offset, "duration_seconds": duration, "status": "unmatched", "queries": phrases, "reason": f"Pexels search failed: {exc.__class__.__name__}"})
                videos = []; candidates = []; break
            for video in videos:
                file = choose_file(video, duration)
                if file and video["id"] not in used_ids:
                    candidates.append((phrase, video, file))
        if not candidates:
            if not any(r.get("beat") == ordinal for r in ledger):
                ledger.append({"beat": ordinal, "name": name, "offset_seconds": offset, "duration_seconds": duration, "status": "unmatched", "queries": phrases, "reason": "No unique HD landscape Pexels candidate at or above required duration."})
            continue
        phrase, video, file = candidates[0]
        suffix = Path(urllib.parse.urlparse(file["link"]).path).suffix or ".mp4"
        local = OUT_DIR / f"beat-{ordinal:02d}-pexels-{video['id']}{suffix}"
        try:
            with session.get(file["link"], stream=True, timeout=120) as response:
                response.raise_for_status()
                with local.open("wb") as handle:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk: handle.write(chunk)
            if local.stat().st_size == 0: raise RuntimeError("Downloaded file is empty")
        except Exception as exc:
            local.unlink(missing_ok=True)
            ledger.append({"beat": ordinal, "name": name, "offset_seconds": offset, "duration_seconds": duration, "status": "unmatched", "queries": phrases, "reason": f"Download failed: {exc.__class__.__name__}"})
            continue
        used_ids.add(video["id"])
        record = {"beat": ordinal, "name": name, "offset_seconds": offset, "duration_seconds": duration, "status": "matched", "queries": phrases, "selected_query": phrase, "pexels_video_id": video["id"], "pexels_page": video.get("url"), "creator": video.get("user", {}).get("name"), "source_duration_seconds": video.get("duration"), "source_width": video.get("width"), "source_height": video.get("height"), "file_width": file.get("width"), "file_height": file.get("height"), "local_path": str(local), "bytes": local.stat().st_size}
        ledger.append(record); selected[ordinal] = record
        time.sleep(0.15)
    LEDGER.write_text(json.dumps({"source":"Pexels API", "searches_per_moving_beat":3, "assets":ledger}, indent=2), encoding="utf-8")
    # Build a v3 editable preview: only matched new clips plus explicit gaps for the case card/unmatched beats.
    out_root = ET.Element("fcpxml", {"version":"1.10"}); out_res = ET.SubElement(out_root, "resources")
    ET.SubElement(out_res, "format", {"id":"r1","name":"YouTube 1080p30","frameDuration":"1/30s","width":"1920","height":"1080","colorSpace":"1-1-1 (Rec. 709)"})
    ref_for: dict[int,str] = {}; rid = 2
    for beat, record in selected.items():
        ref = f"r{rid}"; rid += 1; ref_for[beat] = ref
        ET.SubElement(out_res, "asset", {"id":ref,"name":Path(record["local_path"]).stem,"src":uri(Path(record["local_path"])),"start":"0s","duration":fmt(float(record["source_duration_seconds"])),"hasVideo":"1","format":"r1"})
    audio_ref = f"r{rid}"
    ET.SubElement(out_res, "asset", {"id":audio_ref,"name":audio.get("name"),"src":audio.get("src"),"start":"0s","duration":audio.get("duration"),"hasAudio":"1","audioSources":"1","audioChannels":"2","audioRate":"44100"})
    library=ET.SubElement(out_root,"library"); event=ET.SubElement(library,"event",{"name":"Cold Truth - Jodi Huisentruit"}); project=ET.SubElement(event,"project",{"name":"Jodi Huisentruit - Long-form Preview v3 (Unrendered)"}); sequence=ET.SubElement(project,"sequence",{"format":"r1","duration":"326766/1000s","tcStart":"0s","tcFormat":"NDF","audioLayout":"stereo","audioRate":"48k"}); out_spine=ET.SubElement(sequence,"spine")
    for ordinal, node in enumerate(nodes, 1):
        attrs={"name":node.get("name"),"offset":node.get("offset"),"duration":node.get("duration")}
        if ordinal in ref_for:
            attrs.update({"ref":ref_for[ordinal],"start":"0s"}); new=ET.SubElement(out_spine,"asset-clip",attrs)
        else:
            reason=next(r.get("reason", "case-card placeholder") for r in ledger if r["beat"]==ordinal)
            attrs["name"] = f"UNMATCHED / CASE CARD — {node.get('name')}"; new=ET.SubElement(out_spine,"gap",attrs); ET.SubElement(new,"marker",{"start":"0s","duration":"0s","value":reason})
        for marker in node.findall("marker"):
            ET.SubElement(new,"marker",marker.attrib)
    ET.SubElement(out_spine,"asset-clip",{"name":audio.get("name"),"ref":audio_ref,"offset":"0s","start":"0s","duration":"326766/1000s","lane":"-1"})
    ET.indent(out_root, space="  "); ET.ElementTree(out_root).write(OUT_XML, encoding="utf-8", xml_declaration=True)
    lines=["# Jodi Huisentruit — Long-form Visual Timeline v3","","**Status:** Expanded Pexels sourcing pass; unrendered preview.","","| Beat | Time | Exact narration cue | Pexels search phrases | Result |","|---:|---|---|---|---|"]
    for record in ledger:
        start=record["offset_seconds"]; end=start+record["duration_seconds"]; phrases="; ".join(record["queries"]) if record["queries"] else "—"
        result=(f"Pexels {record['pexels_video_id']} — `{Path(record['local_path']).name}`" if record["status"]=="matched" else f"**{record['status']}** — {record.get('reason','explicit case card')}")
        lines.append(f"| {record['beat']} | {start:06.3f}–{end:06.3f} | {record['name']} | {phrases} | {result} |")
    TIMELINE.write_text("\n".join(lines)+"\n",encoding="utf-8")
    matched=sum(1 for r in ledger if r["status"]=="matched"); unmatched=sum(1 for r in ledger if r["status"]=="unmatched")
    print(json.dumps({"matched_new_clips":matched,"unmatched_beats":unmatched,"case_cards":sum(1 for r in ledger if r["status"]=="case_card_placeholder"),"ledger":str(LEDGER),"preview":str(OUT_XML)},indent=2))

if __name__ == "__main__": main()
