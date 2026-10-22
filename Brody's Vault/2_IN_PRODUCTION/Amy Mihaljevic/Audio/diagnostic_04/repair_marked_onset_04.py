"""One human-marked onset repair audition, not a full-master processing pass."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
import numpy as np
import scipy
from scipy import signal
import soundfile as sf

HERE=Path(__file__).resolve().parent
CASE=HERE.parent.parent
SOURCE=HERE.parent/'correction_03/Amy_Mihaljevic_Mia_correction_03_gain_only.wav'
RAW=HERE.parent/'Amy_Mihaljevic_Mia_attempt_01.mp3'
ALIGN=CASE/'Automation/alignment_draft.json'
TEXT=CASE/'Automation/Narration_Text.txt'
BEFORE=HERE/'opening_13p2s_before.wav'
AFTER=HERE/'opening_13p2s_onset_repair.wav'
REMOVED=HERE/'opening_13p2s_removed_component.wav'
RECEIPT=HERE/'diagnostic_04_receipt.json'
REPORT=HERE/'Diagnostic_04_Report.md'
RATE=44100
SAMPLES=round(13.2*RATE)
COMMANDS=[]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def desc(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def run(argv):
    COMMANDS.append(argv)
    return subprocess.run(argv,stdin=subprocess.DEVNULL,capture_output=True,check=True)
def encode(p):
    output=p.with_suffix('.mp3')
    run(['ffmpeg','-hide_banner','-nostdin','-n','-i',str(p),'-ar',str(RATE),'-ac','1','-c:a','libmp3lame','-b:a','192k',str(output)])
    return output
def stats(y,a,b):
    clip=y[round(a*RATE):round(b*RATE)]
    frequencies,power=signal.welch(clip,RATE,nperseg=min(4096,len(clip)))
    bands={}
    for lo,hi in [(20,180),(180,500),(500,3500),(3500,12000)]:
        mask=(frequencies>=lo)&(frequencies<hi)
        bands[f'{lo}-{hi}_hz']=float(np.trapezoid(power[mask],frequencies[mask]))
    total=sum(bands.values())
    return {'start_seconds':a,'end_seconds':b,'rms_dbfs':float(20*np.log10(np.sqrt(np.mean(clip*clip))+1e-20)),'peak_dbfs':float(20*np.log10(np.max(abs(clip))+1e-20)),'band_power_percent':{k:v/total*100 for k,v in bands.items()}}
def measure(p):
    y,rate=sf.read(p,dtype='float64')
    log=run(['ffmpeg','-hide_banner','-nostdin','-i',str(p),'-af','loudnorm=I=-20:TP=-2:LRA=7:print_format=json','-f','null','-']).stderr.decode('utf-8',errors='replace')
    loud,_=json.JSONDecoder().raw_decode(log[log.rfind('{'):])
    return {**desc(p),'sample_rate':rate,'channels':1,'pcm_subtype':sf.info(p).subtype,'samples':len(y),'duration_seconds':len(y)/rate,'sample_peak_dbfs':float(20*np.log10(np.max(abs(y))+1e-20)),'samples_at_or_above_full_scale':int(np.sum(abs(y)>=1)),'loudness':{k:v for k,v in loud.items() if k.startswith('input_')}}
def curve(size,begin,core_begin,core_end,end,depth_db):
    a,b,c,d=[round(t*RATE) for t in (begin,core_begin,core_end,end)]
    gain=np.ones(size)
    env=np.ones(d-a)
    env[:b-a]=.5-.5*np.cos(np.linspace(0,np.pi,b-a))
    env[c-a:]=.5+.5*np.cos(np.linspace(0,np.pi,d-c))
    gain[a:d]=10**(-depth_db*env/20)
    return gain,{'start_seconds':begin,'full_reduction_start_seconds':core_begin,'full_reduction_end_seconds':core_end,'end_seconds':end,'start_sample':a,'end_sample_exclusive':d,'maximum_reduction_db':depth_db,'envelope':'half cosine ramps in dB domain'}

if __name__=='__main__':
    started=datetime.now(timezone.utc).isoformat()
    assert sha(SOURCE)=='094bfbeafc865b5941efbaae09755e8f2f98c8b0cd9d270418f8557f2d1aaa25'
    assert sha(RAW)=='d328526697bae6d55cd3342edd9e01505aa8c6d8231ec138be832a0236c89f02'
    outputs=[BEFORE,AFTER,REMOVED,BEFORE.with_suffix('.mp3'),AFTER.with_suffix('.mp3'),REMOVED.with_suffix('.mp3'),RECEIPT,REPORT]
    for output in outputs:
        if output.exists():raise SystemExit('Refusing overwrite: '+str(output))
    full,rate=sf.read(SOURCE,dtype='float64');assert rate==RATE
    before=full[:SAMPLES].copy()
    onset_gain,onset=curve(SAMPLES,2.160,2.175,2.260,2.320,8)
    breath_gain,breath=curve(SAMPLES,6.050,6.075,6.260,6.285,6)
    gain=onset_gain*breath_gain
    after=before*gain
    removed=before-after
    assert len(after)==len(before)==SAMPLES
    unchanged=gain==1
    assert np.array_equal(before[unchanged],after[unchanged])
    assert np.all(gain>0) and np.all(gain<=1)
    assert np.max(abs(after))<=np.max(abs(before))
    sf.write(BEFORE,before,RATE,subtype='PCM_24')
    sf.write(AFTER,after,RATE,subtype='PCM_24')
    sf.write(REMOVED,removed,RATE,subtype='PCM_24')
    for path in (BEFORE,AFTER,REMOVED):encode(path)
    raw=np.frombuffer(run(['ffmpeg','-v','error','-nostdin','-i',str(RAW),'-t','13.2','-f','f32le','-ac','1','-ar',str(RATE),'pipe:1']).stdout,dtype='<f4')
    before_metrics=measure(BEFORE);after_metrics=measure(AFTER);removed_metrics=measure(REMOVED)
    preview_checks=[]
    for path in (BEFORE.with_suffix('.mp3'),AFTER.with_suffix('.mp3'),REMOVED.with_suffix('.mp3')):
        data=run(['ffmpeg','-v','error','-nostdin','-i',str(path),'-f','f32le','-ac','1','-ar',str(RATE),'pipe:1']).stdout
        samples=len(data)//4;assert samples==SAMPLES
        preview_checks.append({**desc(path),'decoded_samples':samples,'decoded_duration_seconds':samples/RATE})
    # A region entirely inside the constant -8dB core verifies the actual marked
    # onset change; other words and the second syllable are control regions.
    target_before=stats(before,2.180,2.250);target_after=stats(after,2.180,2.250)
    target_rms_change=target_after['rms_dbfs']-target_before['rms_dbfs']
    target_peak_change=target_after['peak_dbfs']-target_before['peak_dbfs']
    assert abs(target_rms_change+8)<1e-8 and abs(target_peak_change+8)<1e-8
    control_before=stats(before,2.350,2.600);control_after=stats(after,2.350,2.600)
    assert control_before==control_after
    breath_before=stats(before,6.100,6.250);breath_after=stats(after,6.100,6.250)
    assert abs(breath_after['rms_dbfs']-breath_before['rms_dbfs']+6)<1e-8
    assert sha(SOURCE)=='094bfbeafc865b5941efbaae09755e8f2f98c8b0cd9d270418f8557f2d1aaa25'
    feedback=CASE/'Automation/audio_feedback_revision03_2026_10_21.json'
    research=CASE/'Automation/professional_audio_reassessment_04.json'
    onset_measurements={'before':target_before,'after':target_after,'actual_rms_change_db':target_rms_change,'actual_peak_change_db':target_peak_change,'original_provider_region':stats(raw,2.180,2.250),'later_syllable_control_2p35_2p60_unchanged':True}
    report=f'''# Diagnostic 04 — human-marked “disappeared” onset

This candidate addresses the exact spot Brody identified, rather than lowering or limiting the entire recording again. The excerpt is the original 0–13.200 seconds: three complete sentences, including the marked onset and a later standalone gap-noise comparison. Timing and baseline correction-03 gain remain unchanged.

The onset jumps sharply out of a quiet interval near 2.18 seconds. The source-provider signal already contains the dense event. A smooth manual clip-gain dip begins at 2.160 seconds, reaches -8 dB at 2.175, holds through 2.260, and returns to unchanged gain at 2.320. The 2.180–2.250-second marked region changes exactly {target_rms_change:.2f} dB RMS and {target_peak_change:.2f} dB peak. The following 2.350–2.600-second syllable remains numerically identical. The D is attenuated rather than deleted or gated; intelligibility needs actual listening.

Only one standalone gap-noise region at 6.050–6.285 seconds receives a modest 6 dB clip-gain reduction with 25 ms ramps. It ends 157 ms before the next aligned word. Other between-phrase breathiness stays unchanged, reflecting Brody's clarification that it is not the main problem. That noise-like region is outside the approved spoken words, but numerical analysis alone cannot prove that every component is a breath.

No EQ, new compressor/limiter, de-esser, gate, normalization or additional global level change was applied. At the marked onset, most measured energy lies below 500 Hz, so a high-frequency de-esser would target the wrong feature. Low-mid speech energy can also be normal voice body; no speculative 180–500 Hz notch was used. Breathy timbre throughout spoken vowels cannot be established or repaired reliably from these numerical tests alone.

All three WAVs/previews contain exactly {SAMPLES:,} samples / 13.200 seconds at 44.1 kHz mono. The removed-only file is baseline minus repaired audio at its actual level, with no boost; it intentionally includes the attenuated consonant onset. It is for checking what was changed, not proof of clean separation. No full-episode processing, video render, new take, model/software download or canonical change occurred. Listening approval and subjective success remain pending.
'''
    REPORT.write_text(report,encoding='utf-8')
    receipt={'schema_version':'cold_truth.human_marked_onset_diagnostic.v1','status':'SHORT_DIAGNOSTIC_LISTENING_PENDING','started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'role':'Editor','case_id':'amy-mihaljevic','narration_branch':'youtube-longform','source':desc(SOURCE),'provider_source':desc(RAW),'approved_text':desc(TEXT),'word_timing_reference':desc(ALIGN),'feedback_record':desc(feedback) if feedback.exists() else None,'parent_professional_research':desc(research) if research.exists() else None,'specific_human_diagnosis':{'quote':'legit at2seconds when shes amy mahahvoici dissaeepared it peaks aroundthere. at the bggingin of the word dissapeared is when it spikes specifically. shes breathy between phrases but its not horrible imo','scope':'Human-marked onset of disappeared, aligned2.181–2.801 seconds; breathiness secondary'},'operations':[{'type':'manual_onset_clip_gain','justification':'Exact human-marked abrupt onset, not a generic plosive classifier or full-track peak threshold',**onset},{'type':'one_standalone_gap_noise_clip_gain','justification':'Noise-like event in protected interval after her. and before An; modest trial only',**breath}],'spectral_repair_applied':False,'deesser_applied':False,'deesser_omission_reason':'Human-marked event is dominated by low/low-mid energy; no high-frequency causal link established. Preserved ordinary sibilants and voiced body.','additional_global_gain_db':0,'baseline03_global_gain_preserved':True,'compression_or_limiting_applied':False,'gating_applied':False,'noise_generation_or_replacement':False,'normalization':False,'marked_onset_measurements':onset_measurements,'gap_noise_measurements':{'before':breath_before,'after':breath_after,'next_word_start_seconds':6.442,'right_guard_seconds':6.442-6.285,'actual_rms_change_db':breath_after['rms_dbfs']-breath_before['rms_dbfs']},'timbre_and_distortion_assessment':{'standalone_gap_noise':True,'breathy_timbre_inside_words_not_conclusively_established':True,'raw_fullscale_samples_in_excerpt':int(np.sum(abs(raw)>=1)),'no_fullscale_clip_does_not_rule_out_baked_provider_distortion':True,'dense_onset_present_in_original_provider_audio':True,'historical_processing':'Prior accepted profile includes compression/limiting; this cannot be undone and may influence perceived transient/tone character. This pilot does not claim to restore an unprocessed voice.','replacement_take_or_voice_may_be_preferable_if_audition_fails':True},'before':before_metrics,'after':after_metrics,'removed_component':removed_metrics,'mp3_preview_checks':preview_checks,'timeline':{'source_start_sample':0,'source_end_sample_exclusive':SAMPLES,'sample_rate':RATE,'before_samples':SAMPLES,'after_samples':SAMPLES,'removed_component_samples':SAMPLES,'duration_seconds':13.2,'cuts':False,'padding':False,'speed_change':False,'word_or_pause_timing_changed':False,'outside_two_gain_windows_identical_before_pcm_quantization':True},'full_episode_processed':False,'video_rendered':False,'tts_calls':0,'downloads_or_installs':0,'human_listening_approved':False,'assembly_allowed':False,'commands':COMMANDS,'tool_versions':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'soundfile':sf.__version__,'ffmpeg':run(['ffmpeg','-version']).stdout.decode('utf-8').splitlines()[0]},'processor':desc(Path(__file__)),'output_files':[desc(p) for p in outputs if p!=RECEIPT],'receipt_self_hash_omitted':True,'limitations':['Manual gain attenuates the intended consonant along with the burst; user listening must confirm clear diction and naturalness.','No subjective listening success is claimed.','Breath noise and breathy vocal timbre are different; limited spectral measurements cannot diagnose intrinsic voice suitability.','No claim of RX or professional proprietary de-plosive software use is made.','This exact13.2-second test does not approve or alter the full episode soundtrack.']}
    RECEIPT.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'receipt':desc(RECEIPT),'before_preview':desc(BEFORE.with_suffix('.mp3')),'after_preview':desc(AFTER.with_suffix('.mp3')),'removed_preview':desc(REMOVED.with_suffix('.mp3')),'actual_onset_change_db':target_rms_change,'before_level':before_metrics['loudness'],'after_level':after_metrics['loudness'],'output_count':len(list(HERE.iterdir())),'total_output_bytes':sum(p.stat().st_size for p in HERE.iterdir() if p.is_file())},indent=2),flush=True)
