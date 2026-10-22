"""Append the completed direct trial record, preserving prior manifest entries."""
import datetime as dt
import hashlib
import json
import pathlib
import shutil

ROOT=pathlib.Path(__file__).resolve().parents[1]
VAULT=ROOT/"Brody's Vault"
AUTO=VAULT/'2_IN_PRODUCTION/Amy Mihaljevic/Automation'
TRIAL=ROOT/'voice_samples/voicestudio_trial_01'
now=dt.datetime.now(dt.timezone.utc).isoformat()

def describe(path):
    with path.open('rb') as source:
        sha=hashlib.file_digest(source,'sha256').hexdigest()
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha,'bytes':path.stat().st_size}

def save(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

result_path=AUTO/'voicestudio_cpu_trial_result_2026_10_20.json'
result=json.loads(result_path.read_text())
assert result['remaining_trial_attempts']==0 and result['generation_requests_submitted']==2
result['storage']['observed_pre_cleanup_file_allocation_upper_bound_bytes']=9179295744
result['storage']['continuous_historical_peak_certified']=False
result['backend_stopped_after_trial']=json.loads((TRIAL/'backend_stop.json').read_text())
result['runtime_imports_after_scratch_cleanup']='PASS: torch CPU, kittentts and onnxruntime imports; no generation submitted'
save(result_path,result)

shutil.copyfile(ROOT/'docs/vault_audit_voicestudio_trial_2026_10_20.json',ROOT/'docs/vault_audit.json')
audit=json.loads((ROOT/'docs/vault_audit.json').read_text())
state_path=VAULT/'0_ADMIN/COLD_TRUTH_EXECUTION_STATE.json'
state=json.loads(state_path.read_text())
state['local_voice_trial']['storage']=result['storage']
state['local_voice_trial']['validation']={'audit':'docs/vault_audit_voicestudio_trial_2026_10_20.json','notes':audit['note_count'],'reachable':audit['reachable_note_count'],'issues':len(audit['issues']),'reviewed_script_binding_valid':True,'runtime_imports_after_cleanup_pass':True,'backend_stopped_after_trial':True,'git_diff_check':'PASS; existing LF/CRLF warnings only'}
save(state_path,state)

manifest_path=AUTO/'direct_generation_manifest.json'
manifest=json.loads(manifest_path.read_text())
previous_entries=json.dumps(manifest['entries'],sort_keys=True)
event_id='amy-voicestudio-authorized-neutral-cpu-trial-2026-10-20-v1'
assert not any(x['event_id']==event_id for x in manifest['entries'])
paths=[
    AUTO/'approvals/voicestudio_cpu_trial_approval_2026_10_20.json',result_path,
    ROOT/'automation/voicestudio_trial_setup.py',ROOT/'automation/voicestudio_cpu_trial.py',ROOT/'automation/voicestudio_trial_receipt.py',ROOT/'automation/record_voicestudio_trial_closeout.py',ROOT/'automation/start_voicestudio_cpu_trial.py',ROOT/'automation/finalize_voicestudio_trial_manifest.py',
    VAULT/'0_ADMIN/VOICESTUDIO_CPU_TRIAL_2026_10_20.md',VAULT/'0_ADMIN/VOICESTUDIO_EVALUATION_2026_10_20.md',VAULT/'0_ADMIN/PROJECT_DASHBOARD.md',VAULT/'0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2.md',VAULT/'0_ADMIN/PROJECT_MEMORY.md',VAULT/'0_ADMIN/VAULT_INDEX.md',VAULT/'0_ADMIN/GITHUB_TRENDING_REVIEW_2026_10_20.md',state_path,VAULT/'00_START_HERE.md',VAULT/'00_WORKFLOW.canvas',VAULT/'2_CHANNEL_SYSTEM/NARRATION_VOICE.md',VAULT/'2_IN_PRODUCTION/PRODUCTION_HUB.md',VAULT/'2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary.md',AUTO/'Pilot_Runbook.md',ROOT/'docs/vault_audit_voicestudio_trial_2026_10_20.json',ROOT/'docs/vault_audit.json',
]
trial_names=['bella_01.wav','luna_01.wav','bella_attempt.json','luna_attempt.json','disk_baseline.json','disk_guard_reassessment.json','release_metadata.json','SHA256SUMS.txt','VoiceStudio-Electron-0.5.6-win-x64.exe','requirements-release.txt','requirements-cpu.txt','cpu_runtime_install.json','cpu_runtime_resume.json','cpu-runtime-install.log','model_metadata.json','model_download_receipt.json','engine_inspection_stdout.txt','engine_inspection_stderr.txt','backend_launch.json','backend.log','backend_stop.json','health.json','openapi.json','voices.json','voices_after_generation.json','component_license_inventory.json','installed_files_inventory.json']
paths.extend(TRIAL/name for name in trial_names)
manifest['entries'].append({
    'event_id':event_id,'recorded_at_utc':now,
    'tools':['functions tools.exec_command: official release/HF retrieval, verified NSIS installation, private uv CPU dependency installation, local API requests','automation/voicestudio_trial_setup.py','automation/voicestudio_cpu_trial.py (exactly two one-shot POST requests)','VoiceStudio 0.5.6 /v1/audio/speech, kittentts 0.8.1, Kitten mini 0.8, CPU ONNX','ffprobe actual output measurements; wave/numpy technical audio check','automation/pilot_evidence.py paired script binding','automation/vault_audit.py --strict','git diff --check'],
    'settings':{'scope':'Two neutral internal synthetic female-voice samples; not episode narration','approval':describe(AUTO/'approvals/voicestudio_cpu_trial_approval_2026_10_20.json'),'proposal':describe(AUTO/'voicestudio_trial_proposal.json'),'model_revision':result['model_revision'],'cpu_runtime_variant':result['runtime'],'request_receipts':[describe(TRIAL/'bella_attempt.json'),describe(TRIAL/'luna_attempt.json')],'offline_model_loading':True,'additional_speech_models':False,'generation_requests':2,'generation_retries':0,'maximum_trial_requests':2,'remaining_trial_requests':0,'maximum_trial_disk_increase_bytes':10737418240,'storage_measurement_and_limits':result['storage'],'synthetic_provenance':'Approval, neutral text, request/output paths, hashes, classification and this manifest. AudioSeal weights excluded from this one-model trial; invisible-watermark preference off in isolated trial data only.','live_orchestrator_enabled':False,'assembly_allowed':False},
    'outputs':[describe(path) for path in paths],
    'all_installation_output_paths_inventory':describe(TRIAL/'installed_files_inventory.json'),
    'installed_file_inventory_limits':'Every retained trial file path at receipt snapshot. Inventory self excluded; subsequent closeout manifest/state/receipt mutations listed explicitly above. Installer registry/shortcut entries and directory metadata are not enumerated.',
    'verification':{'samples':result['samples'],'all_88_notes_reachable':True,'navigation_issues':0,'approved_amy_binding_still_passes':True,'post_cleanup_runtime_imports_pass':True,'backend_stopped_after_trial':True,'human_listening_approved':False},
    'unverified':['Human listening/complete pronunciation and quality; phonemizer warnings preserved','Stable desktop GUI with custom CPU runtime override (launcher prepared, not executed)','Production voice/profile selection, final component rights review and episode scope','Historical whole-drive peak attribution; contained files are under cap at observations'],
    'audio_or_visual_media_created':True,'neutral_audio_files_created':2,'episode_audio_created':False,'visual_media_created':False,'publishing_authority':False,'manifest_self_hash_omitted':True,
    'next_action':result['next_action'],
})
assert json.dumps(manifest['entries'][:-1],sort_keys=True)==previous_entries
save(manifest_path,manifest)
print(json.dumps({'appended_event':event_id,'prior_entries_preserved':len(manifest['entries'])-1,'output_descriptors':len(paths),'vault_notes':audit['note_count'],'navigation_issues':len(audit['issues']),'samples_created':2,'remaining_trial_attempts':0,'trial_file_gib':result['storage']['unique_file_allocation_upper_bound_bytes']/1024**3},indent=2))
