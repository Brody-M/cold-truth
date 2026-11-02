"""Inspect the existing export. No video render, media acquisition or provider call."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, subprocess, sys
import numpy as np
from scipy.signal import correlate, correlation_lags
from PIL import Image, ImageDraw, ImageFont

A = Path(__file__).resolve().parent
ROOT = A.parents[3]
CASE = A.parent
Q = CASE / 'Visuals/Longform/revision_05/qc_export_2026_11_02'
REPORT = A / 'review02_export_audit_2026_11_02.json'

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def describe(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024**2), b''): h.update(block)
    return dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size, sha256=h.hexdigest())

def main():
    assert not REPORT.exists() and not Q.exists(), 'Preserve existing inspection evidence'
    render = read(A/'longform_review_render_02.json')
    assert render['status'] == 'REVIEW_CUT_RENDERED_TECHNICAL_PASS_HUMAN_PLAYBACK_PENDING'
    recipe = read(CASE/'Visuals/Longform/revision_05/approved_render_recipe_02.json')
    video = ROOT/recipe['output_path']; wav = ROOT/recipe['audio']['path']
    binding = describe(video)
    assert binding in render['outputs'], 'Changed export'
    assert describe(wav) == recipe['audio'], 'Changed approved WAV'
    assert render['full_decode_passed'] is True
    probe_command = ['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]
    probe = json.loads(subprocess.check_output(probe_command, timeout=30))
    vs = next(s for s in probe['streams'] if s['codec_type']=='video')
    aus = next(s for s in probe['streams'] if s['codec_type']=='audio')
    assert len(probe['streams'])==2 and int(vs['nb_frames'])==recipe['frames']
    assert (vs['width'],vs['height'])==(1920,1080)
    assert abs(float(aus['duration'])-recipe['audio_seconds'])<.05
    pts_command=['ffprobe','-v','error','-select_streams','v:0','-show_entries','frame=best_effort_timestamp_time','-of','json',str(video)]
    frame_data=json.loads(subprocess.check_output(pts_command, timeout=300))
    pts=np.array([float(f['best_effort_timestamp_time']) for f in frame_data['frames']])
    assert len(pts)==recipe['frames'] and np.all(np.diff(pts)>0)
    drift=pts-np.arange(len(pts))/30
    assert np.max(np.abs(drift))<.05, 'Frame timestamp drift exceeds50ms'
    commands=[probe_command,pts_command]
    comparisons=[]
    for label,start,length in [('opening',0,8),('marked_onset',2.16,.16),('middle',270,8),('ending',535,8)]:
        decoded=[]
        for path in (wav,video):
            command=['ffmpeg','-v','error','-nostdin','-i',str(path),'-ss',str(start),'-t',str(length),'-map','0:a:0','-ac','1','-ar','44100','-f','f32le','-']
            commands.append(command)
            decoded.append(np.frombuffer(subprocess.check_output(command, timeout=120),dtype='<f4').astype(np.float64))
        x,y=decoded; n=min(len(x),len(y)); x=x[:n]; y=y[:n]
        rms=lambda v: np.sqrt(np.mean(v*v))
        gain=float(20*np.log10(rms(y)/rms(x)))
        corr=correlate(y,x,mode='full',method='fft'); lags=correlation_lags(len(y),len(x)); mask=np.abs(lags)<=1024
        lag=int(lags[mask][np.argmax(corr[mask])])
        normalized=float(np.dot(x,y)/np.sqrt(np.dot(x,x)*np.dot(y,y)))
        assert abs(gain)<.25 and abs(lag)<=2 and normalized>.98, (label,gain,lag,normalized)
        comparisons.append(dict(label=label,start_seconds=start,duration_seconds=length,encoded_rms_gain_db=gain,best_lag_samples=lag,zero_lag_correlation=normalized))
    Q.mkdir()
    selections=[]
    for index,s in enumerate(recipe['shots'],1):
        selections.append(dict(label=f"{index:02} P{s['paragraph_id']:02} {s['asset_id']}",seconds=(s['start_seconds']+s['end_seconds'])/2,name=f'shot_{index:03}_middle.jpg'))
        if s.get('proposed_crop'):
            for label,fraction in [('early',.08),('late',.92)]:
                selections.append(dict(label=f"{index:02} crop {label}",seconds=s['start_seconds']+(s['end_seconds']-s['start_seconds'])*fraction,name=f'shot_{index:03}_{label}.jpg'))
    def extract(item):
        command=['ffmpeg','-v','error','-nostdin','-n','-threads','1','-ss',str(item['seconds']),'-i',str(video),'-frames:v','1','-vf','scale=640:360','-q:v','3',str(Q/item['name'])]
        subprocess.run(command,check=True,capture_output=True,timeout=60)
        return command
    with ThreadPoolExecutor(max_workers=3) as pool: commands.extend(pool.map(extract,selections))
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',16)
    sheets=[]
    for batch in range(0,len(selections),16):
        items=selections[batch:batch+16]; sheet=Image.new('RGB',(1280,840),(20,24,29)); draw=ImageDraw.Draw(sheet)
        for i,item in enumerate(items):
            x=(i%4)*320; y=(i//4)*210
            with Image.open(Q/item['name']) as im: sheet.paste(im.resize((320,180)),(x,y))
            draw.text((x+4,y+181),item['label'],font=font,fill='white')
        p=Q/f'contact_{batch//16+1:02}.jpg'; sheet.save(p,quality=90); sheets.append(describe(p))
    report=dict(status='TECHNICAL_PASS_EXPORT_CONTACT_REVIEW_PENDING',recorded_at_utc=datetime.now(timezone.utc).isoformat(),tool='Installed Python/numpy/scipy/Pillow and FFmpeg/FFprobe8.1.1',video=binding,approved_audio=describe(wav),render_receipt=describe(A/'longform_review_render_02.json'),settings=dict(video_render=False,source_downloads=0,provider_calls=0,frame_sample_width=640,shot_sampling='Every shot midpoint; early/late samples of cropped shots'),video_duration_seconds=float(vs['duration']),audio_duration_seconds=float(aus['duration']),frame_count=len(pts),maximum_frame_timestamp_drift_seconds=float(np.max(np.abs(drift))),audio_comparisons=comparisons,frame_samples=selections,contact_sheets=sheets,commands=commands,outputs=[describe(p) for p in sorted(Q.iterdir())],human_full_video_playback_approved=False,limits='Samples and technical checks do not certify uninterrupted motion, all captions, pronunciation or human creative approval.')
    REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','video_duration_seconds','audio_duration_seconds','maximum_frame_timestamp_drift_seconds','audio_comparisons')}),flush=True)

if __name__=='__main__': main()
