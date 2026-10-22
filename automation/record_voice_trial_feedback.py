"""Record Brody's tentative preference and prepare, without executing, one refinement."""
import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess

ROOT=pathlib.Path(__file__).resolve().parents[1]
VAULT=ROOT/"Brody's Vault"
AUTO=VAULT/'2_IN_PRODUCTION/Amy Mihaljevic/Automation'
TRIAL=ROOT/'voice_samples/voicestudio_trial_01'
now=dt.datetime.now(dt.timezone.utc).isoformat()

def save(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def describe(path):
    with path.open('rb') as source:
        sha=hashlib.file_digest(source,'sha256').hexdigest()
    return {'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':sha}

def edit(relative,before,after):
    path=VAULT/relative
    text=path.read_text(encoding='utf-8')
    assert before in text,relative
    path.write_text(text.replace(before,after),encoding='utf-8')

feedback_path=AUTO/'voicestudio_listening_feedback_2026_10_20.json'
proposal_path=AUTO/'voicestudio_bella_refinement_proposal_2026_10_20.json'
if feedback_path.exists():
    assert json.loads(feedback_path.read_text(encoding='utf-8'))['human_quote']=='belal prolly better but theyre both lowk a lil slow an dkinda grainy sounding idk'
original=json.loads((AUTO/'voicestudio_trial_proposal.json').read_text())
trial=json.loads((AUTO/'voicestudio_cpu_trial_result_2026_10_20.json').read_text())
analysis=subprocess.run(['ffmpeg','-hide_banner','-i',str(TRIAL/'bella_01.wav'),'-af','silencedetect=noise=-40dB:d=0.25','-f','null','NUL'],capture_output=True,text=True,check=True)
(TRIAL/'bella_silence_diagnostic.txt').write_text(analysis.stderr,encoding='utf-8')
intervals=[float(x) for x in re.findall(r'silence_duration: ([0-9.]+)',analysis.stderr)]
feedback={
    'schema_version':'cold_truth.voice_listening_feedback.v1','recorded_at_utc':now,
    'human_quote':'belal prolly better but theyre both lowk a lil slow an dkinda grainy sounding idk',
    'interpretation':{'tentatively_preferred_voice':'Bella / expr-voice-2-f','preference_is_tentative':True,'both_voices_too_slow':True,'both_voices_grainy':True,'quality_accepted_for_production':False,'production_voice_selected':False,'additional_generation_authorized':False},
    'existing_samples':[s['file'] for s in trial['samples']],
    'offline_findings':{'input_words':49,'bella_words_per_minute_including_pauses':49*60/trial['samples'][0]['duration_seconds'],'luna_words_per_minute_including_pauses':49*60/trial['samples'][1]['duration_seconds'],'bella_quiet_intervals_seconds':intervals,'bella_quiet_total_seconds':sum(intervals),'quiet_detection_settings':{'threshold_dbfs':-40,'minimum_interval_seconds':0.25},'silence_is_threshold_measurement_not_missing_word_detection':True,'format':'24 kHz mono PCM 16-bit WAV, not MP3','samples_at_or_above_0_999':0,'installed_api_processing':'Kitten -> 60 Hz high-pass -> 1.5:1 compressor at -15 dB -> peak normalization to -2 dBFS -> PCM WAV. No invisible-watermark processing in this isolated trial.','grain_cause':'Unresolved. Model artifacts and mastering are hypotheses; higher sample rate or stronger denoising is not assumed to restore detail.'},
    'source_code':[describe(TRIAL/'app/resources/backend/api/routers/openai_compat.py'),describe(TRIAL/'app/resources/backend/services/audio_dsp.py')],
    'generation_requests_this_pass':0,'new_audio_files_this_pass':0,'existing_trial_attempts_remaining':0,
}
if not feedback_path.exists():
    save(feedback_path,feedback)
proposal={
    'schema_version':'cold_truth.neutral_voice_refinement_proposal.v1','prepared_at_utc':now,'status':'PREPARED_NOT_AUTHORIZED_OR_EXECUTED',
    'reason':'Tentative Bella preference with unresolved slow/grainy delivery; separate model output from mastering before changing engines.',
    'classification':'AI_GENERATED_NEUTRAL_INTERNAL_TRIAL_NOT_EPISODE_NARRATION','target_format':'youtube-longform','assembly_allowed':False,
    'compute':'CPUExecutionProvider only','application_source':'Installed stable VoiceStudio Electron 0.5.6 unmodified KittenTTSBackend adapter','engine_library':'kittentts 0.8.1','model':'KittenML/kitten-tts-mini-0.8','model_revision':trial['model_revision'],'voice_id':'expr-voice-2-f','voice_alias':'Bella','speed':1.15,
    'test_text':original['test_text'],'input_is_approved_episode_text':False,'maximum_new_tts_generation_calls':1,'automatic_retry_allowed':False,
    'method':'Call the exact installed adapter directly once at speed 1.15; retain that single generated waveform. Create two listening files from the same take. No patching installed application source.',
    'comparison_outputs':[{'path':'voice_samples/voicestudio_trial_01/bella_refinement_01_raw.wav','processing':'No high-pass, compressor, denoiser, reverb or added saturation; gain adjustment only for comparison.'},{'path':'voice_samples/voicestudio_trial_01/bella_refinement_01_mastered.wav','processing':'Same generated take through the installed VoiceStudio mastering chain (60 Hz high-pass and 1.5:1 compressor), then comparison gain.'}],
    'comparison_level_matching':'Match both to the same achievable RMS level, nominal -20 dBFS, lowering the common target if either would exceed -1 dBFS peak. Record achieved levels and all gains; do not hide level differences.',
    'output_format':'24 kHz mono PCM 16-bit WAV; preserve native sample rate; no upsampling claim',
    'maximum_additional_disk_bytes':16777216,'retain_original_10_gib_trial_storage_ceiling':True,
    'limits':{'new_downloads':False,'new_installs':False,'paid_services':False,'cloud_synthesis':False,'cloning':False,'case_narration':False,'visuals':False,'rendering_or_publishing':False},
    'measurements_required':['Exact model/voice/provider and source hashes','One generation-call boundary before synthesis, no retry','Both output paths, SHA-256, durations, RMS, peak, common gain target and wall time','Actual storage growth and listening feedback'],
    'next_after_comparison':'If raw and mastered both remain grainy, do not keep stacking effects. Prepare one alternative-engine quality comparison with its exact model, terms, resources and applicable scope.',
    'does_not_reuse_exhausted_trial_grant':True,
}
if not proposal_path.exists():
    save(proposal_path,proposal)
link='[[2_IN_PRODUCTION/Amy Mihaljevic/Automation/voicestudio_bella_refinement_proposal_2026_10_20.json|one-take Bella refinement proposal]]'
feedback_link='[[2_IN_PRODUCTION/Amy Mihaljevic/Automation/voicestudio_listening_feedback_2026_10_20.json|listening feedback]]'
note=VAULT/'0_ADMIN/VOICESTUDIO_CPU_TRIAL_2026_10_20.md'
text=note.read_text(encoding='utf-8')
text=text.replace('**2026-10-20: two authorized neutral samples generated and technically verified; awaiting Brody\'s listening decision.**',f'**2026-10-20 listening update:** Bella is tentatively preferred, but Brody finds both voices slow and grainy. Quality is not accepted for production. See {feedback_link} and the {link}. No further synthesis has run.\n\n**Original trial:** two authorized neutral samples generated and technically verified.')
text=text.replace('M5 remains in progress. Brody\'s listening decision comes next. Then bind an exact selected profile, component terms, a representative continuity check and episode narration request to new applicable scope.',f'M5 remains in progress. Bella leads provisionally; pacing and texture need improvement. The {link} defines **one new generation at speed 1.15**, producing raw and normally mastered comparisons from the same take with matched levels. It needs fresh applicable authority because the original two-request grant is exhausted. It adds no model, download, paid service or episode narration. Then resolve quality before selecting a production profile.')
text+='''
## Pacing and texture diagnosis after listening

Bella's 49-word sample runs about **110 words/minute including pauses**; Luna is about **142 words/minute**, although Brody perceived both as slow. A threshold-based FFmpeg check found about **3.50 seconds** of Bella audio below -40 dBFS in intervals of at least 250 ms, including edges. This cannot establish missing speech or justify automatically cutting natural pauses.

The files are uncompressed PCM and have no samples at or above 0.999 amplitude. The installed API applies a 60 Hz high-pass, gentle compression and peak normalization. Neither the sample rate nor the absence of clipping diagnoses the reported grain. It may originate in the model, phonemization or processing; those are hypotheses, not listening conclusions.

The [release-specific Kitten guide](https://github.com/debpalash/VoiceStudio/blob/v0.5.6/docs/engines/kittentts.md) documents speed as its available delivery control. The [Supertonic guide](https://github.com/debpalash/VoiceStudio/blob/v0.5.6/docs/engines/supertonic3.md) describes another CPU preset engine with separate weights/terms; it is only a later comparison candidate, not proof of superior quality or permission to install it. Higher sample rate alone is not an acceptance criterion.
'''
note.write_text(text,encoding='utf-8')
edit('00_START_HERE.md','Bella and Luna await listening; both trial attempts are used.','Bella is tentatively preferred, but both samples need pacing/texture improvement; both trial attempts are used.')
edit('0_ADMIN/PROJECT_DASHBOARD.md','two neutral samples ready for listening; zero episode requests','Bella tentatively preferred; slow/grainy delivery unresolved; one-take refinement prepared; zero episode requests')
edit('0_ADMIN/PROJECT_MEMORY.md','its two samples await listening and its grant is exhausted. No production replacement is selected.','Brody tentatively prefers Bella but finds both samples slow/grainy. Its grant is exhausted; a one-take refinement is prepared, not authorized. No production replacement is selected.')
edit('2_CHANNEL_SYSTEM/NARRATION_VOICE.md','Bella/Luna neutral clips await listening and both authorized attempts are used;','Brody tentatively prefers Bella but finds both samples slow/grainy. Both authorized attempts are used; the one-take refinement proposal has not run;')
edit('2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary.md','two neutral samples technically verified, awaiting listening; no production replacement selected','two neutral samples technically verified; Bella tentatively preferred, both slow/grainy; refinement prepared, no production replacement selected')
edit('2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary.md','**Next:** Brody listens to Bella and Luna in the','**Next:** Resolve the pacing/texture concerns recorded after Brody listened to the')
edit('0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2.md','the local CPU trial is complete and awaits listening; the next deliverable is a selected production profile','the local CPU trial is complete; Bella is tentatively preferred but both samples need pacing/texture improvement. The next deliverable is acceptable listening quality and a selected production profile')
edit('0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2.md','Brody listens and chooses a voice or neither, then prepare an exact selected profile and new applicable episode/continuity-test scope.',f'Brody tentatively prefers Bella but finds both samples slow/grainy. Prepare the {link} and obtain applicable new scope before another synthesis; resolve quality before an exact selected profile and episode/continuity-test request.')
edit('2_IN_PRODUCTION/PRODUCTION_HUB.md','awaits Bella/Luna listening.','records a tentative Bella preference with unresolved slow/grainy delivery; a bounded refinement is prepared.')
state_path=VAULT/'0_ADMIN/COLD_TRUTH_EXECUTION_STATE.json'
state=json.loads(state_path.read_text(encoding='utf-8'))
state['operating_mode']='LOCAL_VOICE_QUALITY_REFINEMENT_PREPARED_NO_NEW_GENERATION'
state['next_required_human_action']={'action':'REVIEW_ONE_TAKE_BELLA_REFINEMENT_SCOPE','artifact':proposal_path.relative_to(ROOT).as_posix(),'reason':'Brody tentatively preferred Bella but reported slow/grainy delivery. The original two-request trial is exhausted. Prepared one new neutral take at speed 1.15, raw/mastered comparison from that same take, no downloads/paid services/episode audio.','generation_attempts_submitted_under_new_proposal':0}
state['next_work']['action']='M5_RESOLVE_VOICE_PACING_AND_TEXTURE_WITH_BOUNDED_REFINEMENT_AFTER_APPLICABLE_AUTHORITY'
state['local_voice_trial'].update(status='LISTENED_BELLA_TENTATIVELY_PREFERRED_QUALITY_CONCERNS_UNRESOLVED',tentative_preference='Bella',quality_accepted_for_production=False,feedback_record=feedback_path.relative_to(ROOT).as_posix(),refinement_proposal=proposal_path.relative_to(ROOT).as_posix(),new_refinement_authorized=False)
next(x for x in state['execution_queue'] if x['id']=='M5')['status']='in_progress_voice_quality_refinement_prepared'
save(state_path,state)
canvas=VAULT/'00_WORKFLOW.canvas'
data=json.loads(canvas.read_text(encoding='utf-8'))
for node in data['nodes']:
    if 'text' in node:
        node['text']=node['text'].replace('two neutral CPU samples ready for listening; zero episode requests.','Bella tentatively preferred; slow/grainy delivery unresolved. One-take refinement prepared; zero episode requests.')
save(canvas,data)
print(json.dumps({'feedback':describe(feedback_path),'proposal':describe(proposal_path),'bella_wpm':feedback['offline_findings']['bella_words_per_minute_including_pauses'],'quiet_seconds':sum(intervals),'new_synthesis_requests':0,'new_audio_files':0},indent=2))
