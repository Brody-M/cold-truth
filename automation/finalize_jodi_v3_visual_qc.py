"""Apply human visual QC decisions to Jodi v3 Pexels candidates and rebuild its preview."""
from __future__ import annotations
import json, re, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(r"C:\Youtube Automation Obsidian\Brody's Vault\2_IN_PRODUCTION\Jodi Huisentruit")
LEDGER=ROOT/"Assembly"/"Pexels_Sourcing_v3.json"; SOURCE=ROOT/"Assembly"/"Jodi_Huisentruit_Longform_Preview_v2.fcpxml"
OUT=ROOT/"Assembly"/"Jodi_Huisentruit_Longform_Preview_v3.fcpxml"; TIMELINE=ROOT/"YouTube_Visual_Timeline_v3.md"
ALIGN=ROOT/"Assembly"/"WhisperX"/"tts_At_ro_20260709_192446.json"
REJECT={
 3:"Office call-center footage is not a generic emergency-dispatch visual.",
 4:"Snowy residential aerial is not the approved abstract pavement treatment and conflicts with the June setting.",
 8:"Aerial footage exposes identifiable private residences.",
23:"Firefighter footage is not a generic welfare-check or dispatch visual.",
24:"Police-light reflection conflicts with the approved no-police-lights treatment.",
25:"Keyboard paperwork does not safely illustrate the reported personal-items line.",
30:"Airport departure board is not a missing-person clearinghouse record.",
36:"A person at a workplace does not illustrate the public-record access limit.",
48:"Public atrium footage does not illustrate investigators still asking for information.",
49:"Fingerprint/evidence imagery could imply case-specific evidence and is excluded.",
51:"Highway aerial does not match the quiet current-status / still-missing beat."
}
def sec(v):
    if v=='0s': return 0.0
    a,b=re.match(r'^(\d+)/(\d+)s$',v).groups(); return int(a)/int(b)
def uri(p): return 'file:///'+urllib.parse.quote(str(p).replace('\\','/'),safe='/:')
ledger=json.loads(LEDGER.read_text()); records=ledger['assets']
for r in records:
    if r['beat'] in REJECT and r['status']=='matched':
        r['status']='unmatched_after_visual_qc'; r['reason']=REJECT[r['beat']]
LEDGER.write_text(json.dumps(ledger,indent=2),encoding='utf-8')
alignment=json.loads(ALIGN.read_text())['segments']
tree=ET.parse(SOURCE); src=tree.getroot(); resources=src.find('resources'); audio=next(a for a in resources.findall('asset') if a.get('hasAudio')=='1')
nodes=[n for n in list(src.find('./library/event/project/sequence/spine')) if n.tag in {'asset-clip','gap'} and n.get('lane')!='-1']
selected={r['beat']:r for r in records if r['status']=='matched'}
root=ET.Element('fcpxml',{'version':'1.10'}); outres=ET.SubElement(root,'resources'); ET.SubElement(outres,'format',{'id':'r1','name':'YouTube 1080p30','frameDuration':'1/30s','width':'1920','height':'1080','colorSpace':'1-1-1 (Rec. 709)'})
refs={}; rid=2
for beat,r in selected.items():
    ref=f'r{rid}';rid+=1;refs[beat]=ref
    ET.SubElement(outres,'asset',{'id':ref,'name':Path(r['local_path']).stem,'src':uri(Path(r['local_path'])),'start':'0s','duration':f"{int(r['source_duration_seconds'])}s",'hasVideo':'1','format':'r1'})
audio_ref=f'r{rid}'; ET.SubElement(outres,'asset',{'id':audio_ref,'name':audio.get('name'),'src':audio.get('src'),'start':'0s','duration':audio.get('duration'),'hasAudio':'1','audioSources':'1','audioChannels':'2','audioRate':'44100'})
lib=ET.SubElement(root,'library');event=ET.SubElement(lib,'event',{'name':'Cold Truth - Jodi Huisentruit'});project=ET.SubElement(event,'project',{'name':'Jodi Huisentruit - Long-form Preview v3 (Unrendered, QC gaps flagged)'});sequence=ET.SubElement(project,'sequence',{'format':'r1','duration':'326766/1000s','tcStart':'0s','tcFormat':'NDF','audioLayout':'stereo','audioRate':'48k'});spine=ET.SubElement(sequence,'spine')
lines=['# Jodi Huisentruit — Long-form Visual Timeline v3','','**Status:** Expanded Pexels sourcing, visually reviewed; unrendered preview. Beats without a safe, content-specific match are explicit gaps, not substitutions.','','| Beat | WhisperX-aligned time | Exact spoken content | 3 Pexels search phrases | Result |','|---:|---|---|---|---|']
for beat,node in enumerate(nodes,1):
    off,dur=sec(node.get('offset')),sec(node.get('duration'));end=off+dur
    cue=' '.join(s['text'].strip() for s in alignment if s['end']>off and s['start']<end)
    rec=next(r for r in records if r['beat']==beat);attrs={'offset':node.get('offset'),'duration':node.get('duration')}
    if beat in refs:
        attrs.update({'name':node.get('name'),'ref':refs[beat],'start':'0s'});new=ET.SubElement(spine,'asset-clip',attrs);result=f"Pexels {rec['pexels_video_id']} — `{Path(rec['local_path']).name}`"
    else:
        reason=rec.get('reason','Approved static case-card placeholder');attrs['name']=f"UNMATCHED / CASE CARD — {node.get('name')}";new=ET.SubElement(spine,'gap',attrs);ET.SubElement(new,'marker',{'start':'0s','duration':'0s','value':reason});result=f"**FLAGGED:** {reason}"
    for mark in node.findall('marker'):ET.SubElement(new,'marker',mark.attrib)
    phrases='; '.join(rec.get('queries',[])) or '—';lines.append(f'| {beat} | {off:06.3f}–{end:06.3f} | {cue} | {phrases} | {result} |')
ET.SubElement(spine,'asset-clip',{'name':audio.get('name'),'ref':audio_ref,'offset':'0s','start':'0s','duration':'326766/1000s','lane':'-1'})
ET.indent(root,space='  ');ET.ElementTree(root).write(OUT,encoding='utf-8',xml_declaration=True);TIMELINE.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'matched':len(selected),'flagged':len(records)-len(selected),'preview':str(OUT)},indent=2))
