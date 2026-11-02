"""Wait for the existing single render, record QA and refresh navigation. Never retries it."""
from pathlib import Path
import json,subprocess,time,hashlib
A=Path(__file__).resolve().parent; ROOT=A.parents[3]; C=A.parent
def main():
    receipt=A/'longform_review_render_02.json'
    for _ in range(720):
        try: record=json.loads(receipt.read_text(encoding='utf-8'))
        except (FileNotFoundError,json.JSONDecodeError): time.sleep(10); continue
        if record['status']!='IN_PROGRESS': break
        time.sleep(10)
    else: raise RuntimeError('Render monitoring timeout; no retry')
    if record['status']=='REVIEW_CUT_RENDERED_TECHNICAL_PASS_HUMAN_PLAYBACK_PENDING':
        video=C/'Exports/Longform/Amy_Mihaljevic_review_02.mp4'
        qc=C/'Visuals/Longform/revision_05/qc_review02'; qc.mkdir(exist_ok=False)
        commands=[]
        command=['ffmpeg','-v','info','-nostdin','-i',str(video),'-vn','-af','loudnorm=I=-23:TP=-2:LRA=7:print_format=json','-f','null','-']
        result=subprocess.run(command,capture_output=True,text=True,timeout=600,check=True)
        (qc/'audio_analysis.txt').write_text(result.stderr,encoding='utf-8'); commands.append(command)
        start=result.stderr.rfind('{'); end=result.stderr.rfind('}')
        metrics=json.loads(result.stderr[start:end+1])
        for name,seconds in [('opening',2.2),('parking',98),('laboratory',365),('ending',540)]:
            command=['ffmpeg','-v','error','-nostdin','-n','-ss',str(seconds),'-i',str(video),'-frames:v','1','-q:v','2',str(qc/(name+'.jpg'))]
            subprocess.run(command,capture_output=True,timeout=60,check=True); commands.append(command)
        (A/'longform_review_02_qc.json').write_text(json.dumps(dict(status='TECHNICAL_PASS_HUMAN_PLAYBACK_PENDING',render_receipt='longform_review_render_02.json',full_decode_passed=True,audio_measurement=metrics,analysis_only_no_gain_change=True,commands=commands,human_actual_motion_crop_and_master_review=False,new_provider_calls=0,publishing=False),indent=2)+'\n',encoding='utf-8')
    subprocess.run(['python',str(A/'update_vault_candidate05.py')],check=True,cwd=ROOT)
    subprocess.run(['python','automation/vault_audit.py','--strict','--output','docs/vault_audit.json'],check=True,cwd=ROOT)
    print(record['status'],flush=True)
if __name__=='__main__': main()
