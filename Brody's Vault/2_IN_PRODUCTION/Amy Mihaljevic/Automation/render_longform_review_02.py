"""One remaining authorized corrective cut. No retry, provider or upload calls."""
import importlib.util, json, shutil, subprocess, sys, time
from pathlib import Path
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('previous',P/'render_longform_review_01.py')
old=importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
ROOT,CASE=old.ROOT,old.CASE
R=CASE/'Visuals/Longform/revision_05/approved_render_recipe_02.json'
RECEIPT=P/'longform_review_render_02.json'
def budget(): return sum(p.stat().st_size for p in CASE.rglob('*') if p.is_file())
def main():
    recipe=old.read(R); old.evidence.decision(old.read(old.APPROVAL))
    assert old.read(P/'longform_review_render_01.json')['render_attempt']==1
    for k in ('approval','preflight','alignment','asset_registry','audio'): old.evidence.bound(ROOT,recipe[k])
    pf=old.evidence.audio_preflight(ROOT,(P/'audio_preflight_request.json').relative_to(ROOT).as_posix())
    old.evidence.alignment(ROOT,recipe['alignment']['path'],pf)
    old.evidence.assets(ROOT,recipe['asset_registry']['path'])
    assert recipe['frames']==16458 and len(recipe['shots'])==65 and recipe['render_ready']
    output=ROOT/recipe['output_path']; work=ROOT/recipe['working_directory']
    assert not output.exists() and not work.exists() and not RECEIPT.exists()
    assert output.is_relative_to(CASE/'Exports/Longform') and budget()<old.CAP-1024**3
    if '--validate-only' in sys.argv: print('VALIDATED_NO_RENDER'); return
    work.mkdir(parents=True)
    record=dict(status='IN_PROGRESS',render_attempt=2,started_at_utc=old.now(),authority=old.describe(old.APPROVAL),recipe=old.describe(R),tool='Installed FFmpeg/FFprobe8.1.1',component_commands=[],outputs=[],new_provider_calls=0,publishing=False,human_master_playback_approved=False,settings=dict(fps=30,width=1920,height=1080,source_speed=1,source_audio=False,audio_gain_db=0,encoder='libx264 fast CRF20 max8M',audio='AAC192k',aggregate_case_cap_bytes=old.CAP))
    def save(): RECEIPT.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    def run(cmd,label):
        log=work/f'{label}.log'; event=dict(label=label,command=cmd,started_at_utc=old.now()); record['component_commands'].append(event); save()
        with log.open('xb') as f:
            process=subprocess.Popen(cmd,cwd=work,stdout=f,stderr=f)
            while process.poll() is None:
                if budget()>=old.CAP: process.terminate(); process.wait(timeout=15); raise RuntimeError('5GiB ceiling')
                time.sleep(1)
        event.update(returncode=process.returncode,finished_at_utc=old.now()); save()
        if process.returncode: raise RuntimeError(f'{label} failed; no automatic retry')
    try:
        ass=(CASE/'Visuals/Longform/revision_05/captions_paced_draft.ass').read_text(encoding='utf-8')
        # Caption text/time/layout unchanged. Add persistent illustrative label and compact factual overlays.
        for style in ['Style: Label,Segoe UI,24,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,9,64,64,44,1', 'Style: Fact,Segoe UI,32,&H00FFFFFF,&H00FFFFFF,&H00000000,&H70000000,0,0,0,0,100,100,0,0,3,12,0,7,70,70,70,1']:
            ass=ass.replace('[Events]',style+'\n\n[Events]')
        ass+=f"Dialogue: 0,{old.stamp(0)},{old.stamp(recipe['video_seconds'])},Label,,0,0,0,,Illustrative footage\n"
        for o in recipe['overlays']:
            ass+=f"Dialogue: 2,{old.stamp(o['start_seconds'])},{old.stamp(o['end_seconds'])},Fact,,0,0,0,,{old.ass_text(o['title']+chr(10)+o['detail'])}\n"
        (work/'captions.ass').write_text(ass,encoding='utf-8')
        lines=[]
        for i,s in enumerate(recipe['shots'],1):
            old.evidence.bound(ROOT,s['file']); crop=s['proposed_crop']; filters=''
            if crop: filters=f"crop={crop['width']}:{crop['height']}:{crop['x']}:{crop['y']},"
            filters+='fps=30,scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p'
            segment=work/f'shot_{i:03d}.mp4'
            frames=s['end_frame_exclusive']-s['start_frame']
            run(['ffmpeg','-v','warning','-nostdin','-n','-threads','2','-filter_threads','2','-ss',str(s['source_in_seconds']),'-i',str(ROOT/s['file']['path']),'-map','0:v:0','-an','-vf',filters,'-frames:v',str(frames),'-c:v','libx264','-preset','fast','-crf','20','-maxrate','8M','-bufsize','16M','-threads','2','-pix_fmt','yuv420p','-video_track_timescale','15360','-fs',str(160*1024**2),str(segment)],f'shot_{i:03d}')
            assert int(old.probe(segment)['streams'][0]['nb_frames'])==frames
            lines.append(f"file '{segment.name}'"); print(f'Shot {i}/65',flush=True)
        concat=work/'segments.txt'; concat.write_text('\n'.join(lines)+'\n',encoding='utf-8')
        run(['ffmpeg','-v','warning','-nostdin','-n','-threads','2','-filter_threads','2','-f','concat','-safe','1','-i',str(concat),'-i',str(ROOT/recipe['audio']['path']),'-map','0:v:0','-map','1:a:0','-vf','subtitles=captions.ass','-frames:v',str(recipe['frames']),'-c:v','libx264','-preset','fast','-crf','20','-maxrate','8M','-bufsize','16M','-threads','2','-c:a','aac','-b:a','192k','-movflags','+faststart','-fs',str(900*1024**2),str(output)],'final_caption_mux')
        probe=old.probe(output); video=next(s for s in probe['streams'] if s['codec_type']=='video'); audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
        assert int(video['nb_frames'])==recipe['frames'] and video['width']==1920 and video['height']==1080
        assert abs(float(audio['duration'])-recipe['audio_seconds'])<.05
        (P/'longform_review_02_probe.json').write_text(json.dumps(probe,indent=2)+'\n',encoding='utf-8')
        run(['ffmpeg','-v','error','-nostdin','-threads','2','-i',str(output),'-map','0:v:0','-map','0:a:0','-f','null','-'],'full_decode')
        assert (work/'full_decode.log').stat().st_size==0
        record.update(status='REVIEW_CUT_RENDERED_TECHNICAL_PASS_HUMAN_PLAYBACK_PENDING',full_decode_passed=True,completed_at_utc=old.now(),aggregate_case_bytes=budget())
    except BaseException as e:
        record.update(status='STOPPED_NO_AUTOMATIC_RETRY',error=f'{type(e).__name__}: {e}'); raise
    finally:
        paths=[p for p in work.rglob('*') if p.is_file()]+[p for p in (output,P/'longform_review_02_probe.json') if p.exists()]
        record['outputs']=[old.describe(p) for p in paths]; save()
    print(record['status'],flush=True)
if __name__=='__main__': main()
