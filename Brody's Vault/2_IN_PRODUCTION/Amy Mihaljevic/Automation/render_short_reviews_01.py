"""Prepared existing-scope Shorts: preview stills or one numbered video per branch."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,subprocess,sys,time,shutil
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from automation import pilot_evidence as pe
A=Path(__file__).resolve().parent; CASE=A.parent; CAP=5*1024**3
def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def describe(p):
    if p.stat().st_size==0: return dict(path=p.relative_to(ROOT).as_posix(),bytes=0,sha256=hashlib.sha256(b'').hexdigest())
    return pe.describe(ROOT,p.relative_to(ROOT).as_posix())
def write(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def budget(): return sum(p.stat().st_size for p in CASE.rglob('*') if p.is_file())
def probe(p): return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],timeout=30))

def main():
    assert len(sys.argv)==2 and sys.argv[1] in ('--preview-stills','--render'), 'Choose an explicit prepared stage'
    authority=A/'approvals/phase_2_review_production_2026_10_21.json'; auth=read(authority); pe.decision(auth); pe.bound(ROOT,auth['proposal'])
    proposal=read(ROOT/auth['proposal']['path']); assert proposal['limits']['maximum_new_output_bytes']==CAP
    preparation=read(A/'shorts_review_preparation_2026_11_02.json')
    isolation=pe.assets(ROOT,(A/'asset_registry.json').relative_to(ROOT).as_posix())
    for bound_recipe in preparation['recipes']:
        pe.bound(ROOT,bound_recipe); rp=ROOT/bound_recipe['path']; recipe=read(rp); branch=rp.parent
        for key in ('authority','branch_authority','actual_audio_timing_approval','script','audio','preflight','audio_request','alignment','subtitles','srt','registry'): pe.bound(ROOT,recipe[key])
        pe.decision(read(ROOT/recipe['actual_audio_timing_approval']['path'])['short_audio_timing'])
        pf=pe.audio_preflight(ROOT,recipe['audio_request']['path']); pe.alignment(ROOT,recipe['alignment']['path'],pf)
        assert pf['assembly_allowed'] and 30<=pf['narration_duration_seconds']<=60
        assert recipe['gameplay']['asset_class']=='orbital_gameplay' and recipe['gameplay'] in read(ROOT/recipe['registry']['path'])['shorts']
        assert recipe['output_path'] in read(ROOT/recipe['branch_authority']['path'])['output_paths']
        source=ROOT/recipe['gameplay']['file']['path']; metadata=probe(source)
        vs=next(s for s in metadata['streams'] if s['codec_type']=='video')
        assert (vs['width'],vs['height'])==(2560,1440)
        assert recipe['source_in_seconds']+recipe['audio_duration_seconds']<float(metadata['format']['duration'])
        assert recipe['frames']==math.ceil(pf['narration_duration_seconds']*30)
        prefix=['ffmpeg','-v','warning','-nostdin','-n','-threads','2','-filter_threads','2']
        if sys.argv[1]=='--preview-stills':
            directory=branch.parent/'Visuals/preview_review_01'; assert not directory.exists(); directory.mkdir()
            shutil.copy2(ROOT/recipe['subtitles']['path'],directory/'captions.ass')
            commands=[]
            for i,overlay in enumerate(recipe['overlays'],1):
                t=(overlay['start']+overlay['end'])/2; output=directory/f'overlay_{i:02}.jpg'
                command=prefix+['-ss',str(recipe['source_in_seconds']+t),'-i',str(source),'-map','0:v:0','-an','-vf',f'crop=810:1440:875:0,scale=1080:1920:flags=lanczos,setsar=1,setpts=PTS-STARTPTS+{t}/TB,subtitles=captions.ass,scale=540:960','-frames:v','1','-q:v','2',str(output)]
                result=subprocess.run(command,cwd=directory,capture_output=True,text=True,timeout=90)
                commands.append(dict(command=command,returncode=result.returncode))
                if result.returncode: (directory/'error.log').write_text(result.stderr,encoding='utf-8'); raise RuntimeError('Preview failed; preserved evidence; no video render attempted')
            write(branch/'visual_preview_receipt_01.json',dict(status='STILL_PREVIEWS_READY_FOR_INSPECTION',recorded_at_utc=now(),recipe=bound_recipe,tool='Installed FFmpeg8.1.1',commands=commands,outputs=[describe(p) for p in sorted(directory.iterdir())],video_render=False,new_provider_calls=0))
            print(f"Short{recipe['id']}: overlay previews ready",flush=True)
            continue
        preview_review=A/'short_visual_preview_review_2026_11_02.json'
        assert preview_review.exists() and read(preview_review)['assistant_sample_review_passed'] is True
        assert read(preview_review)['human_final_video_review_passed'] is False
        assert budget()<CAP-512*1024**2
        output=ROOT/recipe['output_path']; work=ROOT/recipe['working_directory']; receipt=branch/'review_video_render_01.json'
        assert output.is_relative_to(CASE/'Exports/Shorts') and work.is_relative_to(CASE/'Exports/Shorts')
        assert not output.exists() and not work.exists() and not receipt.exists(), 'No overwrite or implicit retry'
        prior=list((CASE/'Shorts').glob('*/Automation/review_video_render_*.json'))
        assert 2+len(prior)<proposal['limits']['maximum_review_video_renders_total']
        output.parent.mkdir(parents=True,exist_ok=True); work.mkdir()
        shutil.copy2(ROOT/recipe['subtitles']['path'],work/'captions.ass')
        record=dict(status='IN_PROGRESS',render_attempt=1,case_id=recipe['case_id'],target_format='shorts',started_at_utc=now(),authority=describe(authority),recipe=bound_recipe,tool='Installed FFmpeg/FFprobe8.1.1',settings=dict(size=[1080,1920],fps=30,encoder='libx264 fast CRF20 max8M',audio='AAC192k; no filter or gain change',source_speed=1,gameplay_audio=False,gameplay_loop=False),isolation=isolation,component_commands=[],outputs=[],new_provider_calls=0,publishing=False,human_master_playback_approved=False)
        def save(): write(receipt,record)
        def run(command,label):
            log=work/f'{label}.log'; event=dict(label=label,command=command,started_at_utc=now()); record['component_commands'].append(event); save()
            with log.open('xb') as f:
                process=subprocess.Popen(command,cwd=work,stdout=f,stderr=f)
                while process.poll() is None:
                    if budget()>=CAP: process.terminate(); process.wait(timeout=15); raise RuntimeError('5GiB case output ceiling reached')
                    time.sleep(1)
            event.update(returncode=process.returncode,finished_at_utc=now()); save()
            if process.returncode: raise RuntimeError(f'{label} failed; no automatic retry')
        try:
            command=prefix+['-ss',str(recipe['source_in_seconds']),'-i',str(source),'-i',str(ROOT/recipe['audio']['path']),'-map','0:v:0','-map','1:a:0','-vf','crop=810:1440:875:0,fps=30,scale=1080:1920:flags=lanczos,setsar=1,subtitles=captions.ass,format=yuv420p','-frames:v',str(recipe['frames']),'-c:v','libx264','-preset','fast','-crf','20','-maxrate','8M','-bufsize','16M','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-fs',str(256*1024**2),str(output)]
            run(command,'vertical_caption_mux')
            actual=probe(output); video=next(s for s in actual['streams'] if s['codec_type']=='video'); audio=next(s for s in actual['streams'] if s['codec_type']=='audio')
            assert len(actual['streams'])==2 and (video['width'],video['height'])==(1080,1920)
            assert int(video['nb_frames'])==recipe['frames'] and float(video['duration'])<=60
            assert abs(float(audio['duration'])-recipe['audio_duration_seconds'])<.05
            write(branch/'review_video_probe_01.json',actual)
            run(['ffmpeg','-v','error','-nostdin','-threads','2','-i',str(output),'-map','0:v:0','-map','0:a:0','-f','null','-'],'full_decode')
            assert (work/'full_decode.log').stat().st_size==0
            record.update(status='REVIEW_VIDEO_RENDERED_TECHNICAL_PASS_HUMAN_PLAYBACK_PENDING',completed_at_utc=now(),full_decode_passed=True,case_output_bytes=budget(),remaining_branch_renders=1)
        except BaseException as error:
            record.update(status='STOPPED_NO_AUTOMATIC_RETRY',error=f'{type(error).__name__}: {error}'); raise
        finally:
            actual_paths=[p for p in work.rglob('*') if p.is_file()]+[p for p in (output,branch/'review_video_probe_01.json') if p.exists()]
            record['outputs']=[describe(p) for p in actual_paths]; save()
        print(f"Short{recipe['id']}: {record['status']}",flush=True)

if __name__=='__main__': main()
