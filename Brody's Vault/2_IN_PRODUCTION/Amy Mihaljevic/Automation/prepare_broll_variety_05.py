"""Last finite four-clip variety batch; free sources and strict resource bounds."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlparse
import json,hashlib,urllib.request,subprocess
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;R=H.parents[3];C=H.parent;Q=C/'Visuals/Longform/revision_05/qc_variety';O=H/'broll_revision_05_variety_qc.json'
def desc(p):return {'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def save(d):O.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
if __name__=='__main__':
 assert not O.exists();selection=H/'pexels_broll_revision_05_variety_selected.json';s=json.loads(selection.read_text(encoding='utf-8'));assert len(s['entries'])==4;Q.mkdir(parents=True,exist_ok=True)
 d={'schema_version':'cold_truth.variety_stock_qc.v1','started_at_utc':datetime.now(timezone.utc).isoformat(),'selection':desc(selection),'processor':desc(Path(__file__)),'entries':[],'paid_spending':0,'human_use_approved':False,'assembly_allowed':False,'status':'IN_PROGRESS'};save(d)
 sheet=Image.new('RGB',(1440,1320),'#121820');font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',22)
 for i,e in enumerate(s['entries']):
  f=e['selected_file'];u=f['link'];p=R/e['output_path'];assert p.resolve().is_relative_to((C/'Visuals/Longform/revision_05/assets').resolve()) and not p.exists();assert urlparse(u).scheme=='https' and urlparse(u).hostname=='videos.pexels.com'
  try:
   with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'ColdTruth-free-stock-revision/1.0'}),timeout=45) as response:
    n=int(response.headers['Content-Length']);assert 0<n<60*1024**2 and urlparse(response.url).hostname=='videos.pexels.com'
    prior=sum(x.stat().st_size for x in (C/'Visuals/Longform/revision_05/assets').glob('*.mp4'))+sum(x.stat().st_size for x in (C/'Visuals/Longform/assets').glob('*revision05*mp4'));assert prior+n<s['combined_all_revision_stock_bytes_cap'];count=0
    with p.open('xb') as output:
     while block:=response.read(1024**2):count+=len(block);assert count<=n;output.write(block)
   assert count==n
   meta=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,check=True).stdout);v=next(x for x in meta['streams'] if x['codec_type']=='video');duration=float(meta['format']['duration'])
   decode_cmd=['ffmpeg','-v','error','-nostdin','-threads','2','-i',str(p),'-map','0:v:0','-an','-f','null','-'];dec=subprocess.run(decode_cmd,capture_output=True,timeout=180);log=Q/f'{e["provider_id"]}_decode.log';log.write_bytes(dec.stderr);assert dec.returncode==0 and not dec.stderr
   frames=[]
   for j,fraction in enumerate((.1,.5,.9)):
    frame=Q/f'{e["provider_id"]}_{j+1}.jpg';cmd=['ffmpeg','-v','error','-nostdin','-n','-ss',str(duration*fraction),'-i',str(p),'-frames:v','1','-q:v','2',str(frame)];subprocess.run(cmd,capture_output=True,check=True,timeout=60);im=Image.open(frame);im.thumbnail((480,270));sheet.paste(im,(480*j+(480-im.width)//2,330*i+(270-im.height)//2));frames.append({'frame':desc(frame),'at_seconds':duration*fraction,'command':cmd})
   ImageDraw.Draw(sheet).text((10,330*i+275),f'{e["provider_id"]} | {duration:.2f}s | {v["width"]}x{v["height"]}',font=font,fill='white')
   d['entries'].append({**e,'file':desc(p),'probe':meta,'duration_seconds':duration,'width':v['width'],'height':v['height'],'full_decode_pass':True,'decode_command':decode_cmd,'decode_log':desc(log),'frames':frames,'status':'TECHNICAL_PASS_CONTENT_REVIEW_PENDING'});save(d);print(e['provider_id'],flush=True)
  except Exception as error:d['status']='STOPPED_NO_AUTOMATIC_RETRY';d['error']=str(error);d['failed_source']=e['provider_id'];save(d);raise
 photo=Q/'contact_sheet.jpg';sheet.save(photo,quality=92);d.update(contact_sheet=desc(photo),status='TECHNICAL_QC_COMPLETE_CONTENT_REVIEW_PENDING',completed_at_utc=datetime.now(timezone.utc).isoformat());save(d)
