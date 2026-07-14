"""Build the unrendered Jodi v4 FCPXML from the approved retimed plan."""
from __future__ import annotations
import copy,re,urllib.parse,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(r"C:\Youtube Automation Obsidian\Brody's Vault\2_IN_PRODUCTION\Jodi Huisentruit")
SOURCE=ROOT/"Assembly"/"Jodi_Huisentruit_Longform_Preview_v3.fcpxml";OUT=ROOT/"Assembly"/"Jodi_Huisentruit_Longform_Preview_v4.fcpxml";AUDIO=ROOT/"tts_At_ro_20260710_213842.mp3"
STARTS=[0,5.795,9.858,16.602,21.946,27.951,33.375,38.498,43.459,52.861,59.083,61.964,69.006,75.993,81.999,86.183,94.048,99.411,110.657,118.760,122.961,127.923,133.048,136.711,145.873,158.860,162.763,169.446,175.850,178.391,187.156,199.301,206.804,215.587,218.788,229.091,234.112,239.357,242.500,249.647,257.676,262.140,265.023,273.986,276.387,282.409,286.871,291.732,293.733,301.917,304.919,314.785,318.896,322.868,325.079]
MAP={1:1,2:13,3:4,4:15,5:16,6:10,7:7,8:28,9:2,10:8,11:9,12:12,13:17,14:19,15:21,16:22,17:3,18:14,19:29,20:24,21:25,22:6,23:5,24:26,25:31,26:32,27:33,28:34,29:40,30:37,31:35,32:11,33:36,34:39,35:38,36:18,37:43,38:50,39:42,40:41,41:20,43:45,44:49,45:48,46:47,47:46,48:53,49:52,50:27,51:54,52:56,53:55,54:57}
NAMES=["4:10 colleague call","Morning anchor absent","Parking lot beside car","Drag marks and belongings","Thirty years unanswered","KIMT role in Mason City","June 27 missed shift","Morning television begins early","Live-broadcast preparation","Urgency without explanation","Evidence boundary","Timeline evidence and official updates","Theories versus verified facts","Records establish times","Records cannot explain destination","Timeline and early call","Welfare-check request","7:13 dispatch record","Limits of dispatch record","Reported drag marks","Bent key and red heels","Remaining reported belongings","Reported-findings documentation","No person motive or destination established","Clearinghouse and official contacts","Investigators pursue leads","Winsted search","Search not from new tip","Nothing significant found","2017 GPS warrant","Vehicle connection and sealed affidavit","Warrant chronology","Material unavailable publicly","Connection does not establish guilt","Sealed affidavit is not public proof","Two investigative steps","Physical search and legal effort","No public resolution","Activity is not proof","Incomplete public picture","Activity is not explanation","No resolution","June 2026 active status","Limited meaning of active","Still seeking information","No promised answer","Central fact unchanged","Still missing","Clock parking lot belongings","Everything after remains unknown","Official contact information","Remember Jodi","Comment invitation","Cold Truth sign-off"]
def frac(v):return f"{int(round(v*1000))}/1000s"
def file_uri(p):return 'file:///'+urllib.parse.quote(str(p).replace('\\','/'),safe='/:')
tree=ET.parse(SOURCE);src=tree.getroot();old_refs={}
for n in src.findall('./library/event/project/sequence/spine/asset-clip'):
 if n.get('lane')!='-1' and re.match(r'^(\d+)',n.get('name','')):old_refs[int(re.match(r'^(\d+)',n.get('name')).group(1))]=n.get('ref')
root=ET.Element('fcpxml',{'version':'1.10'});resources=ET.SubElement(root,'resources')
for child in src.find('resources'):
 c=copy.deepcopy(child)
 if c.tag=='asset' and c.get('hasAudio')=='1':
  c.set('name','Mia narration - Script Final v2');c.set('src',file_uri(AUDIO));c.set('duration','325079/1000s')
 resources.append(c)
audio_ref=next(a.get('id') for a in resources.findall('asset') if a.get('hasAudio')=='1')
lib=ET.SubElement(root,'library');event=ET.SubElement(lib,'event',{'name':'Cold Truth - Jodi Huisentruit'});project=ET.SubElement(event,'project',{'name':'Jodi Huisentruit - Long-form Preview v4 (Unrendered)'});sequence=ET.SubElement(project,'sequence',{'format':'r1','duration':'325079/1000s','tcStart':'0s','tcFormat':'NDF','audioLayout':'stereo','audioRate':'48k'});spine=ET.SubElement(sequence,'spine')
for beat in range(1,55):
 attrs={'name':f'{beat:02d} {NAMES[beat-1]}','offset':frac(STARTS[beat-1]),'duration':frac(STARTS[beat]-STARTS[beat-1])}
 if beat==42:
  node=ET.SubElement(spine,'gap',attrs);ET.SubElement(node,'marker',{'start':'0s','duration':'0s','value':'Intentional static case card: There is no resolution to offer.'})
 else:
  old=MAP[beat];attrs.update({'ref':old_refs[old],'start':'0s'});node=ET.SubElement(spine,'asset-clip',attrs);ET.SubElement(node,'marker',{'start':'0s','duration':'0s','value':f'Retimed subject match from approved v3 beat {old}.'})
ET.SubElement(spine,'asset-clip',{'name':'Mia narration - Script Final v2','ref':audio_ref,'offset':'0s','start':'0s','duration':'325079/1000s','lane':'-1'})
ET.indent(root,space='  ');ET.ElementTree(root).write(OUT,encoding='utf-8',xml_declaration=True)
print(f'created={OUT}; moving_beats={len(MAP)}; unique_refs={len(set(old_refs[v] for v in MAP.values()))}; case_cards=1')
