"""Capture actual trial files, licenses and technical measurements without synthesis."""
import datetime as dt
import email
import hashlib
import json
import math
import os
import pathlib
import shutil
import wave

import numpy as np
from pilot_evidence import approval

ROOT = pathlib.Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'voice_samples/voicestudio_trial_01'
AUTO = ROOT / "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation"

def describe(path):
    with path.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    return {'path':path.relative_to(ROOT).as_posix(), 'bytes':path.stat().st_size, 'sha256':digest}

def save(path, value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

measurements = []
for name in ('bella','luna'):
    attempt = json.loads((TRIAL/f'{name}_attempt.json').read_text())
    assert attempt['status'] == 'TECHNICALLY_VERIFIED_AWAITING_HUMAN_LISTENING'
    audio = TRIAL/f'{name}_01.wav'
    with wave.open(str(audio)) as wav:
        assert wav.getsampwidth() == 2 and wav.getnchannels() == 1 and wav.getframerate() == 24000
        samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2').astype(np.float64)/32768
        duration = len(samples)/24000
    rms = float(np.sqrt(np.mean(samples*samples)))
    measurements.append({'voice':name,'engine_voice_id':attempt['request']['voice'],'file':describe(audio),'duration_seconds':duration,'sample_rate':24000,'channels':1,'codec':'pcm_s16le','peak_absolute_amplitude':float(np.max(np.abs(samples))),'samples_at_or_above_0_999':int(np.count_nonzero(np.abs(samples)>=0.999)),'rms_dbfs':20*math.log10(rms) if rms else None,'wall_seconds':attempt['wall_seconds'],'wall_to_audio_ratio':attempt['wall_seconds']/duration,'sampled_peak_backend_tree_rss_bytes':attempt['sampled_peak_backend_tree_rss_bytes'],'attempt_receipt':describe(TRIAL/f'{name}_attempt.json'),'human_listening_approved':False})
assert measurements[0]['file']['sha256'] != measurements[1]['file']['sha256']
assert len(list(TRIAL.glob('*_attempt.json'))) == 2

licenses = []
for metadata in (TRIAL/'runtime/Lib/site-packages').glob('*.dist-info/METADATA'):
    message = email.message_from_string(metadata.read_text(encoding='utf-8',errors='replace'))
    licenses.append({'package':message.get('Name'),'version':message.get('Version'),'license_expression':message.get('License-Expression'),'license_field':message.get('License'),'metadata_path':metadata.relative_to(ROOT).as_posix(),'license_files':[p.relative_to(ROOT).as_posix() for p in metadata.parent.rglob('*') if p.is_file() and any(x in p.name.lower() for x in ('license','copying','notice'))]})
save(TRIAL/'component_license_inventory.json', licenses)

inventory=[]
seen=set()
allocation=0
for folder, dirs, files in os.walk(TRIAL):
    for name in files:
        path=pathlib.Path(folder)/name
        if path.name == 'installed_files_inventory.json' and path.parent == TRIAL:
            continue
        info=path.stat()
        unique=(info.st_dev,info.st_ino) not in seen
        if unique:
            seen.add((info.st_dev,info.st_ino))
            allocation+=((info.st_size+4095)//4096)*4096
        inventory.append({'path':path.relative_to(ROOT).as_posix(),'bytes':info.st_size,'unique_allocation_counted':unique})
save(TRIAL/'installed_files_inventory.json',{'recorded_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'files':inventory,'inventory_self_omitted':True})
inventory_allocation=((TRIAL/'installed_files_inventory.json').stat().st_size+4095)//4096*4096
allocation+=inventory_allocation
assert allocation < 10737418240, 'Trial storage ceiling exceeded'
bound=approval(ROOT,(AUTO/'approvals/script_approval_2026_10_20.json').relative_to(ROOT).as_posix())
baseline=json.loads((TRIAL/'disk_baseline.json').read_text())
report={
    'schema_version':'cold_truth.local_voice_trial_result.v1',
    'recorded_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
    'status':'TWO_NEUTRAL_SAMPLES_TECHNICALLY_VERIFIED_AWAITING_BRODY_LISTENING',
    'application':'VoiceStudio Electron 0.5.6', 'installed_app_path':str(TRIAL/'app/VoiceStudio.exe'),
    'installer':describe(TRIAL/'VoiceStudio-Electron-0.5.6-win-x64.exe'),
    'published_checksum_file':describe(TRIAL/'SHA256SUMS.txt'),
    'installer_hash_matches_release_digest_and_checksum_file':True,
    'runtime':'Private CPython 3.11.9 environment; frozen release dependency versions, CPU torch/torchaudio/torchvision variants',
    'engine':'kittentts','model':'KittenML/kitten-tts-mini-0.8','model_revision':'c02725660cea441db4c383af69f1f26f5cd00947',
    'model_receipt':describe(TRIAL/'model_download_receipt.json'),
    'offline_engine_inspection':describe(TRIAL/'engine_inspection_stdout.txt'),
    'health':json.loads((TRIAL/'health.json').read_text()),
    'api_execution_evidence_limitation':'Catalog reports engine loaded/effective CPU but leaves actual_execution_provider null. Separate exact installed adapter/model inspection confirms CPUExecutionProvider only; torch is CPU-only.',
    'bound_approval':describe(AUTO/'approvals/voicestudio_cpu_trial_approval_2026_10_20.json'),
    'generation_requests_submitted':2, 'automatic_retries':0, 'remaining_trial_attempts':0,
    'samples':measurements,
    'storage':{'unique_file_allocation_upper_bound_bytes':allocation,'unique_files':len(seen)+1,'maximum_total_disk_increase_bytes':10737418240,'trial_files_under_cap':True,'initial_drive_free_bytes':baseline['drive_free_bytes'],'current_drive_free_bytes':shutil.disk_usage(ROOT).free,'whole_drive_delta_is_not_trial_attribution':True,'accounting_limits':'Deduplicates hardlinks and rounds files to 4 KiB. Small installer registry/shortcut entries and directory metadata excluded. Whole-drive growth includes unattributed concurrent/system activity and cannot establish attribution or a historical peak. Initial conservative whole-drive guard stopped the first dependency install; recovered files were reused without generation retry. Installation scratch/cache then removed after stopping the trial backend; installed runtime and all audio/evidence retained.'},
    'all_installed_file_paths':describe(TRIAL/'installed_files_inventory.json'),
    'component_license_inventory':describe(TRIAL/'component_license_inventory.json'),
    'model_license_metadata':'Apache-2.0; immutable model card captured. App AGPL-3.0-only; component notices retained. This is not production rights approval.',
    'dependency_model_disclosure':'Frozen Kitten phonemizer dependency chain includes packaged en-core-web-sm 3.8.0 NLP language data (~12.2 MiB wheel). It is not an additional TTS engine/voice model; full release dependencies installed. No additional speech, ASR or AudioSeal weights downloaded.',
    'warnings':['Phonemizer reported word-count mismatches for both requests. Human listening must check every sentence, omitted words, numbers and dates. No creative/content completeness approval is inferred.'],
    'application_gui_verified':False,
    'provider_files_created': [m['file']['path'] for m in measurements],
    'episode_narration_requests':0,'elevenlabs_requests':0,'paid_services_used':False,'voice_cloning_performed':False,
    'visuals_rendering_publishing_performed':False,'assembly_allowed':False,'target_format':'youtube-longform',
    'approved_amy_script_binding_still_valid':True,'binding_check':bound,
    'next_action':'Brody listens and chooses Bella, Luna, or neither. Then prepare an exact selected production profile and applicable episode/continuity-test scope. Do not submit more requests under this exhausted trial grant.'
}
save(AUTO/'voicestudio_cpu_trial_result_2026_10_20.json',report)
print(json.dumps({'samples':measurements,'storage':report['storage'],'paired_binding_valid':True},indent=2))
