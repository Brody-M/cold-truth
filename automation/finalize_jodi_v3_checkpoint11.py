"""Accept reviewed second-pass footage or genuine thematic reuses and rebuild v3."""
from __future__ import annotations
import json,re,urllib.parse,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(r"C:\Youtube Automation Obsidian\Brody's Vault\2_IN_PRODUCTION\Jodi Huisentruit")
FIRST=ROOT/"Assembly"/"Pexels_Sourcing_v3.json";SECOND=ROOT/"Assembly"/"Pexels_Sourcing_v3_second_pass.json";SOURCE=ROOT/"Assembly"/"Jodi_Huisentruit_Longform_Preview_v2.fcpxml";ALIGN=ROOT/"Assembly"/"WhisperX"/"tts_At_ro_20260709_192446.json";OUT=ROOT/"Assembly"/"Jodi_Huisentruit_Longform_Preview_v3.fcpxml";TIMELINE=ROOT/"YouTube_Visual_Timeline_v3.md"
ACCEPT={3:"Second-pass generic telephone/desk visual supports dispatch without agency branding.",4:"Second-pass wet-asphalt abstract supports the reported drag-marks line without reenactment.",8:"Second-pass after-hours work desk supports the active-investigation status beat.",24:"Second-pass wet pavement is a safe abstract parking-lot cutaway.",25:"Second-pass generic personal belongings safely support the item-list line without recreating evidence.",36:"Second-pass locked card-catalog/record drawers support the public-access limit.",48:"Second-pass office information desk supports the continuing information-request beat.",49:"Second-pass closed archival files support the distinction between active and solved."}
REUSE={23:(14,"Reuse beat 14: both lines concern dispatch/welfare-check action; 51.265 seconds apart."),30:(54,"Reuse beat 54: both lines direct viewers to official information/contact channels; 131.500 seconds apart."),51:(46,"Reuse beat 46: both are quiet current-status/missing-person beats; 21.045 seconds apart.")}
def sec(v):
 if v=='0s':return 0.0
 a,b=re.match(r'^(\d+)/(\d+)s$',v).groups();return int(a)/int(b)
def uri(p):return 'file:///'+urllib.parse.quote(str(p).replace('\\','/'),safe='/:')
first=json.loads(FIRST.read_text());records=first['assets'];by={r['beat']:r for r in records};second={r['beat']:r for r in json.loads(SECOND.read_text())['assets']}
for beat,note in ACCEPT.items():
 s=second[beat];r=by[beat];r.update({'status':'matched_second_pass_visual_qc','selected_query':s['selected_query'],'pexels_video_id':s['pexels_video_id'],'local_path':s['local_path'],'bytes':s['bytes'],'source_duration_seconds':s['duration'],'file_width':s['width'],'file_height':s['height'],'creator':s['creator'],'pexels_page':s['page'],'visual_qc_note':note,'second_pass_queries':s['queries']})
for beat,(source,note) in REUSE.items():
 r=by[beat];r.update({'status':'reused_existing_visual_qc','reuse_beat':source,'visual_qc_note':note})
FIRST.write_text(json.dumps(first,indent=2),encoding='utf-8')
align=json.loads(ALIGN.read_text())['segments'];tree=ET.parse(SOURCE);src=tree.getroot();res=src.find('resources');audio=next(a for a in res.findall('asset') if a.get('hasAudio')=='1');nodes=[n for n in list(src.find('./library/event/project/sequence/spine')) if n.tag in {'asset-clip','gap'} and n.get('lane')!='-1']
def source_for(beat):
 r=by[beat]
 return by[r['reuse_beat']] if r['status']=='reused_existing_visual_qc' else r
root=ET.Element('fcpxml',{'version':'1.10'});outres=ET.SubElement(root,'resources');ET.SubElement(outres,'format',{'id':'r1','name':'YouTube 1080p30','frameDuration':'1/30s','width':'1920','height':'1080','colorSpace':'1-1-1 (Rec. 709)'})
refs={};unique={};rid=2
for beat,node in enumerate(nodes,1):
 r=by[beat]
 if r['status']=='case_card_placeholder':continue
 source=source_for(beat);key=source['local_path']
 if key not in unique:
  ref=f'r{rid}';rid+=1;unique[key]=ref;ET.SubElement(outres,'asset',{'id':ref,'name':Path(key).stem,'src':uri(Path(key)),'start':'0s','duration':f"{int(source['source_duration_seconds'])}s",'hasVideo':'1','format':'r1'})
 refs[beat]=unique[key]
audio_ref=f'r{rid}';ET.SubElement(outres,'asset',{'id':audio_ref,'name':audio.get('name'),'src':audio.get('src'),'start':'0s','duration':audio.get('duration'),'hasAudio':'1','audioSources':'1','audioChannels':'2','audioRate':'44100'})
lib=ET.SubElement(root,'library');event=ET.SubElement(lib,'event',{'name':'Cold Truth - Jodi Huisentruit'});project=ET.SubElement(event,'project',{'name':'Jodi Huisentruit - Long-form Preview v3 (Unrendered, Checkpoint 11)'});seq=ET.SubElement(project,'sequence',{'format':'r1','duration':'326766/1000s','tcStart':'0s','tcFormat':'NDF','audioLayout':'stereo','audioRate':'48k'});spine=ET.SubElement(seq,'spine')
lines=['# Jodi Huisentruit — Long-form Visual Timeline v3','','**Status:** Checkpoint 11 resolved. All 56 moving beats have an approved new or genuinely matching reused visual; beat 44 is the sole intentional static case card. Unrendered.','','| Beat | WhisperX-aligned time | Exact spoken content | Search / resolution | Final visual status |','|---:|---|---|---|---|']
for beat,node in enumerate(nodes,1):
 r=by[beat];off,dur=sec(node.get('offset')),sec(node.get('duration'));end=off+dur;cue=' '.join(s['text'].strip() for s in align if s['end']>off and s['start']<end);attrs={'offset':node.get('offset'),'duration':node.get('duration')}
 if beat in refs:
  attrs.update({'name':node.get('name'),'ref':refs[beat],'start':'0s'});new=ET.SubElement(spine,'asset-clip',attrs)
  if r['status']=='reused_existing_visual_qc':result=f"**Reused beat {r['reuse_beat']}:** {r['visual_qc_note']}";queries='Second pass found no safe match; existing thematic reuse reviewed.'
  elif r['status']=='matched_second_pass_visual_qc':result=f"**New Pexels {r['pexels_video_id']}:** {r['visual_qc_note']}";queries='; '.join(r['second_pass_queries'])
  else:result=f"Pexels {r['pexels_video_id']} — selected after first-pass QC";queries='; '.join(r.get('queries',[]))
 else:
  reason='Approved intentional “There is no resolution to offer” case card.';attrs['name']=f"CASE CARD — {node.get('name')}";new=ET.SubElement(spine,'gap',attrs);ET.SubElement(new,'marker',{'start':'0s','duration':'0s','value':reason});result='**Static case card**';queries='—'
 for m in node.findall('marker'):ET.SubElement(new,'marker',m.attrib)
 lines.append(f'| {beat} | {off:06.3f}–{end:06.3f} | {cue} | {queries} | {result} |')
ET.SubElement(spine,'asset-clip',{'name':audio.get('name'),'ref':audio_ref,'offset':'0s','start':'0s','duration':'326766/1000s','lane':'-1'});ET.indent(root,space='  ');ET.ElementTree(root).write(OUT,encoding='utf-8',xml_declaration=True);TIMELINE.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'unique_clips':len(unique),'second_pass_new':len(ACCEPT),'genuine_reuses':len(REUSE),'case_cards':1,'preview':str(OUT)},indent=2))
