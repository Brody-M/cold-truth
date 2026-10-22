"""Provisional B-roll coverage and layout proofs, never an assembly-ready timeline."""
from pathlib import Path
from datetime import datetime, timezone
import collections
import hashlib
import json
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CASE=HERE.parent
VIS=CASE/'Visuals/Longform/revision_05'
PROOFS=VIS/'layout_proofs'
TIMING=CASE/'Audio/full_repair_05/remapped_word_timing_draft.json'
RECIPE=VIS/'candidate_render_recipe_05.json'

def desc(p):
    return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def probe(p):
    d=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,check=True).stdout)
    s=next(s for s in d['streams'] if s['codec_type']=='video')
    return float(d['format']['duration']),s['width'],s['height']

def union_length(ranges):
    intervals=[]
    for a,b in sorted(ranges):
        if intervals and a<=intervals[-1][1]:intervals[-1][1]=max(b,intervals[-1][1])
        else:intervals.append([a,b])
    return sum(b-a for a,b in intervals)

if __name__=='__main__':
    assert not RECIPE.exists()
    timing=json.loads(TIMING.read_text(encoding='utf-8'))
    registry=json.loads((HERE/'asset_registry.json').read_text(encoding='utf-8'))
    reviewed=json.loads((HERE/'broll_revision_05_content_review_combined.json').read_text(encoding='utf-8'))
    assets={}
    for e in registry['youtube-longform']:
        if e['asset_class']!='pexels_broll':continue
        ident=int(e['source_identity'].split(':')[-1]);p=ROOT/e['file']['path'];duration,w,h=probe(p)
        assets[ident]={**e,'range':[0,min(duration,14) if ident==5792246 else duration],
                       'width':w,'height':h,'crop':None,'human_use_approved':True,
                       'label':'Illustrative footage','actual_trim_crop_reviewed':False}
    for e in reviewed['entries']:
        if e['editorial_decision']=='EXCLUDE':continue
        assets[e['provider_id']]={'asset_id':e['asset_id'],'source_identity':e['source_identity'],
            'file':e['file'],'rights_review':e['candidate_review'],'license_evidence':e['license_evidence'],
            'range':e['permitted_source_range_seconds'],'width':e['actual_width'],'height':e['actual_height'],
            'crop':e['proposed_crop'],'human_use_approved':False,'content_note':e['content_note'],
            'label':'Illustrative textile work' if e['provider_id']==8527274 else 'Illustrative footage',
            'actual_trim_crop_reviewed':False}
    # Each paragraph has its own visual purpose; no nature footage outside the rural-discovery paragraph.
    playlists={
      1:[(6975995,1),(854698,1),(14160089,1)],
      2:[(14512668,1),(5792244,.7),(5792246,.8),(5835776,.8)],
      3:[(854698,1),(6975995,.6),(32835503,.6),(14160089,1)],
      4:[(14160089,1),(32835503,.8),(5835776,.5)],
      5:[(5792244,.7),(5792246,.8),(8371852,1)],
      6:[(8371858,1),(14160089,.8),(8371852,.8)],
      7:[(8888977,1),(17136728,1),(6550428,1)],
      8:[(15602507,1),(6577022,.7),(8371858,.7)],
      9:[(6550428,1),(7233562,.8),(8371852,1)],
      10:[(7233562,.8),(8527274,1),(8371858,1)],
      11:[(854698,.8),(8085793,1),(17136728,1)],
      12:[(8085793,1),(17136728,1),(5835776,.65),(8325857,.65)],
      13:[(8527274,1),(7233562,.75),(8371852,1)],
      14:[(8325857,1),(4267248,1),(8326170,.8),(3195394,.8)],
      15:[(8325856,1),(8381446,.8),(8371858,1),(8326170,.8)],
      16:[(8371852,1),(3195394,.8),(4267248,.8),(8371858,1)],
      17:[(8085793,1),(3195394,.8),(8371852,1),(8381446,.8)],
      18:[(854698,.7),(14160089,.8),(17136728,1),(8325856,.8)],
      19:[(14512668,1),(5792244,.8),(5835776,1)]}
    old=json.loads((CASE/'Visuals/Longform/review_cut_recipe_2026_10_21.json').read_text(encoding='utf-8'))
    claim_ids=collections.defaultdict(set)
    for s in old['shots']:claim_ids[s['paragraph_id']].add(s['claim_ids'])
    frames=math.ceil(timing['duration_seconds']*30);paragraphs=timing['paragraphs'];shots=[]
    source_cursor={i:e['range'][0] for i,e in assets.items()};source_intervals=collections.defaultdict(list)
    for n,p in enumerate(paragraphs):
        begin=0 if n==0 else round(p['start']*30)
        end=round(paragraphs[n+1]['start']*30) if n+1<len(paragraphs) else frames
        items=playlists[p['paragraph_id']];weight=sum(w for _,w in items);current=begin;cumulative=0
        for j,(ident,w) in enumerate(items):
            cumulative+=w;stop=end if j+1==len(items) else begin+round((end-begin)*cumulative/weight)
            length=(stop-current)/30;asset=assets[ident];low,high=asset['range']
            assert 0<length<=min(high-low,20), (ident,length,high-low)
            source_in=source_cursor[ident]
            if source_in+length>high:
                # Explicit source reuse is measured below, never hidden as looping.
                spare=high-low-length
                source_in=low+(min(spare,1.3*len(source_intervals[ident])) if spare>0 else 0)
            source_out=source_in+length;assert low<=source_in<source_out<=high+1e-8
            source_cursor[ident]=source_out
            overlap=sum(max(0,min(source_out,b)-max(source_in,a)) for a,b in source_intervals[ident])
            source_intervals[ident].append([source_in,source_out])
            shots.append({'shot_id':f'R05-{len(shots)+1:03}','paragraph_id':p['paragraph_id'],
                'start_frame':current,'end_frame_exclusive':stop,'start_seconds':current/30,'end_seconds':stop/30,
                'source_in_seconds':source_in,'source_out_seconds':source_out,'source_interval_overlaps_prior_use':overlap>0,
                'asset_id':asset['asset_id'],'source_identity':asset['source_identity'],'file':asset['file'],
                'proposed_crop':asset['crop'],'rights_review':asset['rights_review'],
                'human_use_approved':asset['human_use_approved'],'actual_trim_crop_reviewed':False,
                'illustrative_label':asset['label'],'source_audio':'disabled','source_speed':1,'source_looping':False,
                'claim_ids':sorted(claim_ids['P'+str(p['paragraph_id']).zfill(2)]),
                'narration_purpose':p['text'],'stock_is_actual_case_footage':False})
            current=stop
    assert shots[0]['start_frame']==0 and shots[-1]['end_frame_exclusive']==frames
    assert all(a['end_frame_exclusive']==b['start_frame'] for a,b in zip(shots,shots[1:]))
    assert all('orbital' not in s['source_identity'] for s in shots)
    shorts=registry['shorts'];assert not {s['source_identity'] for s in shots}&{s['source_identity'] for s in shorts}
    assert not {s['file']['sha256'] for s in shots}&{s['file']['sha256'] for s in shorts}
    use=collections.defaultdict(lambda:{'appearances':0,'seconds':0})
    for s in shots:
        i=int(s['source_identity'].split(':')[-1]);use[i]['appearances']+=1;use[i]['seconds']+=s['end_seconds']-s['start_seconds']
    for i,d in use.items():
        d['distinct_source_seconds']=union_length(source_intervals[i]);d['reused_source_seconds']=d['seconds']-d['distinct_source_seconds']
    overlays=[{'paragraph_id':4,'title':'October 27, 1989','detail':'After school'},
              {'paragraph_id':7,'title':'Following the leads','detail':'Illustrative records work'},
              {'paragraph_id':8,'title':'February 8, 1990','detail':'Rural Ashland County'},
              {'paragraph_id':9,'title':'Unrecovered belongings','detail':'Horse earring · black ankle boots · black binder'},
              {'paragraph_id':10,'title':'2016 · Public textile appeal','detail':'Illustrative textile footage'},
              {'paragraph_id':13,'title':'2021 · Renewed textile appeal','detail':'Reported hair association'},
              {'paragraph_id':14,'title':'2024 · Clothing DNA','detail':'Detected; too little for a profile'},
              {'paragraph_id':16,'title':'January 2026 · Separate hairs','detail':'No profile obtained in the reported test'},
              {'paragraph_id':18,'title':'Public appeal remains open','detail':'Source check: October 16, 2026'}]
    for overlay in overlays:
        chosen=next(s for s in shots if s['paragraph_id']==overlay['paragraph_id'] and (overlay['paragraph_id']!=4 or s['source_identity'].endswith(':32835503')))
        overlay.update(start_seconds=chosen['start_seconds']+.2,end_seconds=min(chosen['start_seconds']+6.2,chosen['end_seconds']),placement='upper-left compact label over moving footage')
    result={'schema_version':'cold_truth.provisional_visual_revision.v1','created_at_utc':datetime.now(timezone.utc).isoformat(),
        'status':'PROVISIONAL_AUDIO_TIMING_AND_NEW_ASSET_USE_APPROVAL_PENDING','audio':timing['audio'],
        'timing_draft':desc(TIMING),'caption_draft':desc(VIS/'captions_paced_draft.json'),
        'source_registry_historical':desc(HERE/'asset_registry.json'),'new_candidate_review':desc(HERE/'broll_revision_05_content_review_combined.json'),
        'audio_seconds':timing['duration_seconds'],'fps':30,'frames':frames,'video_seconds':frames/30,
        'full_frame_coverage':True,'shots':shots,'asset_use_statistics':dict(use),'overlays':overlays,
        'full_screen_card_seconds':0,'old_full_screen_card_seconds':194.7333333333333,
        'stock_audio':False,'background_music':False,'gameplay':False,'human_audio_approved':False,
        'human_timing_approved':False,'new_asset_use_approved':False,'actual_trim_crop_reviewed':False,
        'assembly_allowed':False,'render_ready':False,'publishing_authorized':False,
        'limitations':['No suitable school exterior or actual public-poster footage was found; bicycle/route/public-context footage serves those paragraphs without pretending to show actual case images.',
          'Some source intervals repeat; exact reused seconds are disclosed per asset. No stock source loops within a shot.',
          'School/name/flag mismatches, financial charts and the720p variant are excluded.',
          'B-roll and overlays translate approved narration, not independent case evidence. Final crop/motion, rights/use and human audio/timing review remain pending.']}
    RECIPE.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    PROOFS.mkdir(parents=True,exist_ok=True);caps=json.loads((VIS/'captions_paced_draft.json').read_text(encoding='utf-8'))['segments'];proofs=[]
    for pnum in (4,7,14,18):
        shot=next(s for s in shots if s['paragraph_id']==pnum and (pnum!=4 or s['source_identity'].endswith(':32835503')))
        ident=int(shot['source_identity'].split(':')[-1]);source_time=(shot['source_in_seconds']+shot['source_out_seconds'])/2
        raw=PROOFS/f'p{pnum:02}_source.jpg';cmd=['ffmpeg','-v','error','-nostdin','-n','-ss',str(source_time),'-i',str(ROOT/shot['file']['path']),'-frames:v','1','-q:v','2',str(raw)];subprocess.run(cmd,capture_output=True,check=True)
        im=Image.open(raw).convert('RGB');crop=shot['proposed_crop']
        if crop:im=im.crop((crop['x'],crop['y'],crop['x']+crop['width'],crop['y']+crop['height']))
        scale=min(1920/im.width,1080/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);canvas=Image.new('RGB',(1920,1080),'#10151a');canvas.paste(im,((1920-im.width)//2,(1080-im.height)//2));canvas=ImageEnhance.Brightness(canvas).enhance(.88)
        layer=Image.new('RGBA',(1920,1080),(0,0,0,0));draw=ImageDraw.Draw(layer)
        overlay=next(o for o in overlays if o['paragraph_id']==pnum)
        titlefont=ImageFont.truetype('C:/Windows/Fonts/seguisb.ttf',48);detailfont=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',32)
        boxwidth=max(draw.textlength(overlay['title'],font=titlefont),draw.textlength(overlay['detail'],font=detailfont))+60
        draw.rounded_rectangle((82,94,82+boxwidth,266),radius=12,fill=(13,20,26,205))
        draw.text((110,112),overlay['title'],font=ImageFont.truetype('C:/Windows/Fonts/seguisb.ttf',48),fill='#f4eee6')
        draw.text((110,181),overlay['detail'],font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',32),fill='#d2dbdf')
        label=shot['illustrative_label'];font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',25);width=draw.textlength(label,font=font)
        draw.rectangle((1810-width,38,1850,82),fill=(5,10,14,195));draw.text((1830-width,41),label,font=font,fill='white')
        at=(shot['start_seconds']+shot['end_seconds'])/2;caption=next((c for c in caps if c['start']<=at<=c['end']),next(c for c in caps if c['start']>=shot['start_seconds']))
        font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',44);lines=caption['text'].splitlines();y=1080-130-54*len(lines)
        for line in lines:
            width=draw.textlength(line,font=font);draw.text(((1920-width)/2,y),line,font=font,fill='white',stroke_width=3,stroke_fill='black');y+=54
        canvas=Image.alpha_composite(canvas.convert('RGBA'),layer).convert('RGB');out=PROOFS/f'p{pnum:02}_layout.jpg';canvas.save(out,quality=94)
        proofs.append({'paragraph_id':pnum,'shot':shot['shot_id'],'source_frame':desc(raw),'source_time':source_time,'caption_example':caption,'layout':desc(out),'command':cmd,'layout_proof_only':True})
    qc={'created_at_utc':datetime.now(timezone.utc).isoformat(),'recipe':desc(RECIPE),'processor':desc(Path(__file__)),
        'shot_count':len(shots),'unique_stock_sources':len(use),'maximum_shot_seconds':max(s['end_seconds']-s['start_seconds'] for s in shots),
        'full_frame_coverage':True,'full_screen_cards_seconds':0,'longform_short_visual_sources_and_hashes_disjoint':True,
        'proofs':proofs,'human_trim_crop_playback_reviewed':False,'video_rendered':False}
    (HERE/'visual_revision_05_preparation.json').write_text(json.dumps(qc,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:qc[k] for k in ['shot_count','unique_stock_sources','maximum_shot_seconds','full_frame_coverage','full_screen_cards_seconds']},indent=2))
