"""Broadened Pexels resourcing for the eleven v3 QC gaps; no preview changes."""
from __future__ import annotations
import json, os, re, time
from pathlib import Path
import requests
import av
from PIL import Image, ImageDraw

ROOT=Path(r"C:\Youtube Automation Obsidian\Brody's Vault\2_IN_PRODUCTION\Jodi Huisentruit")
LEDGER=ROOT/"Assembly"/"Pexels_Sourcing_v3.json"; OUT=ROOT/"Assembly"/"Pexels_Sourcing_v3_second_pass.json"; DIR=ROOT/"footage_v3_second_pass"; CONTACT=ROOT/"Assembly"/"Pexels_Contact_Sheet_v3_second_pass.jpg"
TARGETS={
3:["At 7:13 that morning, dispatch sent a welfare check to her apartment complex.",["office desk telephone keyboard","generic call center headset","emergency radio desk"]],
4:["Public reporting described drag marks beside Jodi's car.",["wet asphalt close up","rain pavement abstract","empty parking lot rainfall"]],
8:["More than thirty years later, the investigation remains active.",["dark office desk lamp","closed case file table","empty streetlights evening"]],
23:["Later that morning, police were dispatched to her apartment complex for a welfare check.",["empty apartment hallway","telephone on office desk","intercom desk close up"]],
24:["Reporting later described drag marks and several personal items in the parking lot.",["dark wet pavement texture","rain puddle asphalt close up","empty parking lot ground"]],
25:["They included a red pair of heels, earrings, a blow dryer, hairspray, and a bent key for Jodi's Miata.",["keys personal belongings table","hairbrush and keys desk","women accessories flat lay"]],
30:["Iowa's Missing Person Information Clearinghouse still lists Jodi and directs anyone with information to Mason City Police or the Iowa Division of Criminal Investigation.",["community bulletin board notices","information flyer board office","public notice board papers"]],
36:["There is also a limit on what the public can review.",["locked filing cabinet close up","closed archive drawer","restricted documents folder"]],
48:["It does mean the case has not been closed and investigators are still asking for information.",["telephone message desk","contact information flyer","tip line phone office"]],
49:["Active is not the same as solved.",["closed case file desk","unanswered paperwork desk","empty folder table"]],
51:["For the people who knew Jodi, the central fact has not changed. She is still missing.",["empty street dusk no cars","lonely road fog","porch light night empty"]]
}
def pick(video,need):
    if video.get('duration',0)<need:return None
    fs=[f for f in video.get('video_files',[]) if f.get('file_type')=='video/mp4' and f.get('width',0)>=1280 and f.get('height',0)>=720]
    return sorted(fs,key=lambda f:f['width']*f['height'])[0] if fs else None
def main():
    key=os.environ.get('PEXELS_API_KEY');
    if not key:raise RuntimeError('PEXELS_API_KEY required')
    original=json.loads(LEDGER.read_text())['assets']; bybeat={r['beat']:r for r in original}; used={r['pexels_video_id'] for r in original if r.get('pexels_video_id')}
    session=requests.Session();session.headers['Authorization']=key;DIR.mkdir(exist_ok=True); results=[]
    for beat,(cue,phrases) in TARGETS.items():
        need=bybeat[beat]['duration_seconds']; found=[]
        for phrase in phrases:
            r=session.get('https://api.pexels.com/videos/search',params={'query':phrase,'orientation':'landscape','per_page':10},timeout=45);r.raise_for_status()
            for v in r.json().get('videos',[]):
                f=pick(v,need)
                if f and v['id'] not in used:found.append((phrase,v,f))
        if not found:
            results.append({'beat':beat,'cue':cue,'queries':phrases,'status':'still_unmatched','reason':'No new qualifying HD landscape candidate.'});continue
        phrase,v,f=found[0];path=DIR/f"beat-{beat:02d}-pexels-{v['id']}.mp4"
        with session.get(f['link'],stream=True,timeout=120) as response:
            response.raise_for_status()
            with path.open('wb') as h:
                for chunk in response.iter_content(1024*1024):
                    if chunk:h.write(chunk)
        if not path.exists() or path.stat().st_size==0:raise RuntimeError(f'empty download beat {beat}')
        used.add(v['id']);results.append({'beat':beat,'cue':cue,'queries':phrases,'status':'candidate_downloaded','selected_query':phrase,'pexels_video_id':v['id'],'local_path':str(path),'bytes':path.stat().st_size,'duration':v['duration'],'width':f['width'],'height':f['height'],'creator':v.get('user',{}).get('name'),'page':v.get('url')});time.sleep(.15)
    OUT.write_text(json.dumps({'source':'Pexels API broadened second pass','assets':results},indent=2))
    good=[r for r in results if r['status']=='candidate_downloaded'];sheet=Image.new('RGB',(1280,6*210),'#111');draw=ImageDraw.Draw(sheet)
    for n,item in enumerate(good):
        row,col=divmod(n,2);x,y=col*640,row*210;c=av.open(item['local_path']);frame=next(c.decode(video=0));c.close();im=frame.to_image().convert('RGB');im.thumbnail((620,180));sheet.paste(im,(x+10,y+22));draw.text((x+10,y+4),f"{item['beat']:02d} {item['cue'][:54]}",fill='white')
    sheet.save(CONTACT,quality=88)
    print(json.dumps({'candidates':len(good),'still_unmatched':len(results)-len(good),'ledger':str(OUT),'contact_sheet':str(CONTACT)},indent=2))
if __name__=='__main__':main()
