"""Audit existing vertical exports against their approved WAVs; no generation."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,time,sys
import numpy as np
from scipy.signal import correlate,correlation_lags
from PIL import Image,ImageDraw,ImageFont
from render_short_reviews_01 import ROOT,A,CASE,read,describe,write

def main():
    report=A/'short_video_export_audit_01_2026_11_02.json'; assert not report.exists()
    entries=[]; commands=[]; output_paths=[]
    for bound in read(A/'shorts_review_preparation_2026_11_02.json')['recipes']:
        recipe=read(ROOT/bound['path']); branch=(ROOT/bound['path']).parent; receipt=branch/'review_video_render_01.json'
        for _ in range(120):
            try: render=read(receipt)
            except (FileNotFoundError,json.JSONDecodeError): time.sleep(5); continue
            if render['status']!='IN_PROGRESS': break
            time.sleep(5)
        else: raise RuntimeError('Existing render did not finish in10minutes; not retried')
        assert render['status']=='REVIEW_VIDEO_RENDERED_TECHNICAL_PASS_HUMAN_PLAYBACK_PENDING' and render['full_decode_passed']
        video=ROOT/recipe['output_path']; binding=describe(video); assert binding in render['outputs']
        wav=ROOT/recipe['audio']['path']; assert describe(wav)==recipe['audio']
        p=read(branch/'review_video_probe_01.json'); vs=next(s for s in p['streams'] if s['codec_type']=='video'); aus=next(s for s in p['streams'] if s['codec_type']=='audio')
        assert (vs['width'],vs['height'])==(1080,1920) and int(vs['nb_frames'])==recipe['frames'] and float(vs['duration'])<=60
        q=branch.parent/'Visuals/encoded_review_01'; assert not q.exists(); q.mkdir()
        command=['ffmpeg','-v','info','-nostdin','-i',str(video),'-vn','-af','loudnorm=I=-23:TP=-2:LRA=7:print_format=json','-f','null','-']
        result=subprocess.run(command,check=True,capture_output=True,text=True,timeout=180); commands.append(command)
        analysis=q/'audio_analysis.txt'; analysis.write_text(result.stderr,encoding='utf-8'); output_paths.append(analysis)
        raw=json.loads(result.stderr[result.stderr.rfind('{'):result.stderr.rfind('}')+1]); meters={k:float(raw[k]) for k in ('input_i','input_tp','input_lra')}
        comparisons=[]
        for label,start in [('opening',0),('middle',recipe['audio_duration_seconds']/2),('ending',recipe['audio_duration_seconds']-3)]:
            decoded=[]
            for source in (wav,video):
                command=['ffmpeg','-v','error','-nostdin','-i',str(source),'-ss',str(start),'-t','3','-map','0:a:0','-ac','1','-ar','44100','-f','f32le','-']; commands.append(command)
                decoded.append(np.frombuffer(subprocess.check_output(command,timeout=60),dtype='<f4').astype(np.float64))
            x,y=decoded; n=min(len(x),len(y)); x=x[:n]; y=y[:n]
            gain=float(10*np.log10(np.mean(y*y)/np.mean(x*x)))
            corr=correlate(y,x,method='fft'); lags=correlation_lags(n,n); mask=np.abs(lags)<=1024; lag=int(lags[mask][np.argmax(corr[mask])])
            normalized=float(np.dot(x,y)/np.sqrt(np.dot(x,x)*np.dot(y,y)))
            assert abs(gain)<.25 and abs(lag)<=2 and normalized>.98,(recipe['id'],label,gain,lag,normalized)
            comparisons.append(dict(label=label,start_seconds=start,rms_gain_db=gain,best_lag_samples=lag,zero_lag_correlation=normalized))
        selections=[dict(label='Opening',seconds=.5),dict(label='Ending',seconds=max(0,recipe['audio_duration_seconds']-.5))]
        selections.extend(dict(label=f'Overlay{i}',seconds=(o['start']+o['end'])/2) for i,o in enumerate(recipe['overlays'],1))
        for i,s in enumerate(selections):
            path=q/f'frame_{i:02}.jpg'; command=['ffmpeg','-v','error','-nostdin','-n','-threads','1','-ss',str(s['seconds']),'-i',str(video),'-frames:v','1','-vf','scale=540:960','-q:v','2',str(path)]
            commands.append(command); subprocess.run(command,check=True,capture_output=True,timeout=60); output_paths.append(path); s['file']=describe(path)
        rows=(len(selections)+2)//3; contact=q/'contact.jpg'; sheet=Image.new('RGB',(1620,1000*rows),(20,24,29)); draw=ImageDraw.Draw(sheet); font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',22)
        for i,s in enumerate(selections):
            x=i%3*540; y=i//3*1000
            with Image.open(ROOT/s['file']['path']) as im: sheet.paste(im,(x,y))
            draw.text((x+12,y+963),f"Short{recipe['id']} {s['label']}",font=font,fill='white')
        sheet.save(contact,quality=91); output_paths.append(contact)
        entries.append(dict(id=recipe['id'],video=binding,approved_audio=recipe['audio'],render_receipt=describe(receipt),video_seconds=float(vs['duration']),audio_seconds=float(aus['duration']),frames=int(vs['nb_frames']),full_decode_passed=True,measured_encoded_audio=meters,audio_comparisons=comparisons,frames_sampled=selections,contact_sheet=describe(contact),human_video_playback_approved=False))
        print(f"Short{recipe['id']}: decode/runtime/encoded-audio pass; sampled all factual overlays",flush=True)
    write(report,dict(status='TECHNICAL_PASS_ENCODED_SAMPLE_REVIEW_PENDING',recorded_at_utc=datetime.now(timezone.utc).isoformat(),tool='Installed FFmpeg/FFprobe8.1.1 and Python/numpy/scipy/Pillow',settings=dict(audio_measurement_only=True,gain_changes=False,frame_sample_size=[540,960],new_video_renders=0),entries=entries,commands=commands,outputs=[describe(p) for p in output_paths],new_provider_calls=0,publishing=False,human_video_playback_approved=False))

if __name__=='__main__': main()
