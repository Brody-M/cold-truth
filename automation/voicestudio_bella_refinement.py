"""Execute the separately authorized one-take neutral Bella comparison once."""
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import sys
import threading
import time
import traceback
from zoneinfo import ZoneInfo

ROOT=pathlib.Path(__file__).resolve().parents[1]
TRIAL=ROOT/'voice_samples/voicestudio_trial_01'
AUTO=ROOT/"Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation"
PROPOSAL=AUTO/'voicestudio_bella_refinement_proposal_2026_10_20.json'
APPROVAL=AUTO/'approvals/voicestudio_bella_refinement_approval_2026_10_20.json'
MANIFEST=AUTO/'voicestudio_bella_refinement_manifest.json'

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def save(path,data,exclusive=False):
    with path.open('x' if exclusive else 'w',encoding='utf-8') as target:
        json.dump(data,target,indent=2)
        target.write('\n')

def desc(path):
    with path.open('rb') as source:
        sha=hashlib.file_digest(source,'sha256').hexdigest()
    return {'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':sha}

def storage_snapshot():
    files={}
    unique={}
    for folder,dirs,names in os.walk(TRIAL):
        for name in names:
            path=pathlib.Path(folder)/name
            stat=path.stat()
            size=((stat.st_size+4095)//4096)*4096
            files[path.relative_to(ROOT).as_posix()]=size
            unique[(stat.st_dev,stat.st_ino)]=size
    return files,sum(unique.values())

proposal=json.loads(PROPOSAL.read_text(encoding='utf-8'))
assert proposal['maximum_new_tts_generation_calls']==1
assert proposal['automatic_retry_allowed'] is False
assert proposal['voice_id']=='expr-voice-2-f' and proposal['speed']==1.15
assert not proposal['input_is_approved_episode_text'] and proposal['assembly_allowed'] is False

if sys.argv[1]=='record':
    save(APPROVAL,{
        'schema_version':'cold_truth.neutral_voice_refinement_approval.v1',
        'recorded_at_utc':now(),'approved_local_date':dt.datetime.now(ZoneInfo('America/New_York')).date().isoformat(),
        'human_decision_quote':'yes',
        'question_context':'Authorize that refinement? Your original approval covered two takes, both used. This adds one neutral take, no downloads, spending or episode narration.',
        'scope_context':'One Bella take at 1.15 speed, raw and processed versions of the same audio to investigate grainy/slow delivery.',
        'proposal':desc(PROPOSAL),'maximum_new_tts_generation_calls':1,'automatic_retry_allowed':False,
        'comparison_outputs':proposal['comparison_outputs'],'new_downloads_allowed':False,'new_installs_allowed':False,
        'paid_services_allowed':False,'cloud_synthesis_allowed':False,'case_narration_allowed':False,
        'visuals_or_publishing_allowed':False,'assembly_allowed':False,
        'does_not_reuse_exhausted_original_grant':True,
    },exclusive=True)
    print(json.dumps(desc(APPROVAL),indent=2))
    raise SystemExit(0)

assert sys.argv[1]=='run'
assert not MANIFEST.exists(),'One-shot attempt already exists. Do not retry synthesis.'
approval=json.loads(APPROVAL.read_text(encoding='utf-8'))
assert approval['proposal']==desc(PROPOSAL)
outputs=[ROOT/x['path'] for x in proposal['comparison_outputs']]
native=TRIAL/'bella_refinement_01_native.npy'
assert not any(p.exists() for p in [*outputs,native])
env=json.loads((TRIAL/'backend_launch.json').read_text(encoding='utf-8'))['environment_overrides']
os.environ.update(env)
os.environ.update(TEMP=str(TRIAL/'tmp'),TMP=str(TRIAL/'tmp'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
(TRIAL/'tmp').mkdir(exist_ok=True)
before,initial_allocation=storage_snapshot()
assert initial_allocation+proposal['maximum_additional_disk_bytes']<10737418240
model_receipt=json.loads((TRIAL/'model_download_receipt.json').read_text())
assert model_receipt['revision']==proposal['model_revision']
for item in model_receipt['files']:
    assert desc(ROOT/item['path'])==item

# These are the unmodified sources shipped by the installed stable app.
sys.path.insert(0,str(TRIAL/'app/resources'))
sys.path.insert(0,str(TRIAL/'app/resources/backend'))
import numpy as np
import torch
import soundfile as sf
import psutil
import pedalboard
from services.tts_backend import KittenTTSBackend
from services.audio_dsp import apply_mastering,MASTERING_CHAIN
backend=KittenTTSBackend()
backend._ensure_loaded()  # Offline cache load only, no synthesis.
backend._check_language('en')  # Validate language imports before the synthesis boundary.
assert torch.__version__=='2.8.0+cpu' and not torch.cuda.is_available()
assert backend._model.model.session.get_providers()==['CPUExecutionProvider']
assert proposal['voice_id'] in backend.PRESET_VOICES
assert proposal['voice_id'] in backend._model.model.voices.files
assert backend._model.model.voice_aliases['Bella']==proposal['voice_id']
manifest={
    'schema_version':'cold_truth.neutral_voice_refinement_manifest.v1',
    'started_at_utc':now(),'status':'ONE_SYNTHESIS_CALL_STARTING_NO_RETRY',
    'tool':'Installed VoiceStudio 0.5.6 KittenTTSBackend.generate, direct offline CPU invocation',
    'approval':desc(APPROVAL),'proposal':desc(PROPOSAL),
    'settings':{'engine':'kittentts','library_version':'0.8.1','model':proposal['model'],'model_revision':proposal['model_revision'],'voice':proposal['voice_id'],'speed':1.15,'language':'en','test_text':proposal['test_text'],'input_sha256':hashlib.sha256(proposal['test_text'].encode()).hexdigest(),'onnx_providers':backend._model.model.session.get_providers(),'offline':True,'mastering_chain':MASTERING_CHAIN,'target_rms_dbfs':-20,'peak_ceiling_dbfs':-1},
    'source_code':[desc(TRIAL/'app/resources/backend/services/tts_backend.py'),desc(TRIAL/'app/resources/backend/services/audio_dsp.py')],
    'target_format':'youtube-longform','classification':proposal['classification'],'assembly_allowed':False,'is_episode_narration':False,
    'generation_calls_submitted':0,'maximum_generation_calls':1,'automatic_retry_allowed':False,
    'pre_synthesis_runner_repair_record': 'Brody\'s Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation/voicestudio_bella_refinement_pre_synthesis_repair.json',
    'all_planned_audio_output_paths':[p.relative_to(ROOT).as_posix() for p in outputs],
    'native_waveform_path':native.relative_to(ROOT).as_posix(),
    'additional_evidence_paths':['voice_samples/voicestudio_trial_01/bella_refinement_01_run.log'],
    'storage_before_file_allocation_upper_bound_bytes':initial_allocation,
}
save(MANIFEST,manifest,exclusive=True) # Persist one-call boundary before synthesis.
actual_synthesize=backend._synthesize
def synthesize_once(*args,**kwargs):
    assert manifest['generation_calls_submitted']==0,'No synthesis retry permitted'
    manifest['generation_calls_submitted']=1
    manifest['status']='ONE_SYNTHESIS_CALL_STARTED_NO_RETRY'
    save(MANIFEST,manifest)
    return actual_synthesize(*args,**kwargs)
backend._synthesize=synthesize_once # Record/guard actual synthesis; source files unchanged.
finished=threading.Event()
resources={'peak_process_rss_bytes':psutil.Process().memory_info().rss}
def sample_memory():
    process=psutil.Process()
    while not finished.wait(0.1):
        resources['peak_process_rss_bytes']=max(resources['peak_process_rss_bytes'],process.memory_info().rss)
sampler=threading.Thread(target=sample_memory,daemon=True)
sampler.start()
started=time.monotonic()
try:
    waveform=backend.generate(proposal['test_text'],voice=proposal['voice_id'],speed=1.15,language='en')
    generation_wall=time.monotonic()-started
    assert waveform.device.type=='cpu' and backend.sample_rate==24000
    raw=waveform.detach().cpu().numpy().reshape(-1).astype(np.float32)
    assert raw.size and np.isfinite(raw).all()
    np.save(native,raw,allow_pickle=False)
    mastered=apply_mastering(waveform.clone(),sample_rate=24000).detach().cpu().numpy().reshape(-1).astype(np.float32)
    assert mastered.shape==raw.shape and np.isfinite(mastered).all()
    assert not np.array_equal(raw,mastered),'Mastering returned unchanged data; retain native take and report, do not regenerate.'
    def levels(array):
        rms=float(np.sqrt(np.mean(array.astype(np.float64)**2)))
        peak=float(np.max(np.abs(array)))
        assert rms>0 and peak>0
        return rms,peak
    level_pairs=[levels(a) for a in [raw,mastered]]
    common=min([10**(-20/20)]+[rms*(10**(-1/20))/peak for rms,peak in level_pairs])
    common*=0.99999 # Keep floating-point/PCM rounding inside the peak ceiling.
    results=[]
    for path,array,(rms,peak),label in zip(outputs,[raw,mastered],level_pairs,['gain_only_raw','VoiceStudio_mastering_then_gain']):
        gain=common/rms
        rendered=array*gain
        assert np.max(np.abs(rendered))<=10**(-1/20)
        sf.write(path,rendered,24000,subtype='PCM_16')
        decoded,rate=sf.read(path)
        decoded_rms,decoded_peak=levels(decoded)
        results.append({'file':desc(path),'processing':label,'sample_rate':rate,'channels':1,'sample_count':len(decoded),'duration_seconds':len(decoded)/rate,'source_rms':rms,'source_peak':peak,'linear_gain':gain,'gain_db':20*math.log10(gain),'achieved_rms_dbfs':20*math.log10(decoded_rms),'achieved_peak_dbfs':20*math.log10(decoded_peak),'clipped_full_scale_samples':int(np.count_nonzero(np.abs(decoded)>=0.999))})
    assert abs(results[0]['achieved_rms_dbfs']-results[1]['achieved_rms_dbfs'])<0.01
    after,final_allocation=storage_snapshot()
    growth=sum(max(0,size-before.get(path,0)) for path,size in after.items())
    assert growth<=16777216 and final_allocation<10737418240
    manifest.update(status='COMPLETED_AWAITING_HUMAN_COMPARISON',completed_at_utc=now(),generation_wall_seconds=round(generation_wall,3),total_generation_and_processing_wall_seconds=round(time.monotonic()-started,3),common_target_rms_dbfs=20*math.log10(common),outputs=results,native_waveform=desc(native),sampled_resources=resources,additional_trial_file_allocation_upper_bound_bytes=growth,final_trial_file_allocation_upper_bound_bytes=final_allocation,remaining_generation_calls=0,human_listening_approved=False)
    save(MANIFEST,manifest)
    print(json.dumps({'status':manifest['status'],'outputs':results,'generation_wall_seconds':generation_wall,'common_target_rms_dbfs':manifest['common_target_rms_dbfs'],'storage_growth_bytes':growth,'trial_file_gib':final_allocation/1024**3},indent=2),flush=True)
except BaseException as error:
    manifest.update(status='FAILED_AFTER_ONE_CALL_BOUNDARY_NO_SYNTHESIS_RETRY',completed_at_utc=now(),error=repr(error),retained_outputs=[desc(p) for p in [native,*outputs] if p.exists()],remaining_generation_calls=0)
    save(MANIFEST,manifest)
    traceback.print_exc()
    raise
finally:
    finished.set()
    sampler.join(timeout=1)
