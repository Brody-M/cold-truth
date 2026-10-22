"""Local level fix and limited pacing audition; no full paced episode or video."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import re
import subprocess
import sys
import numpy as np
from scipy import ndimage
import scipy
import soundfile as sf

HERE = Path(__file__).resolve().parent
CASE = HERE.parent.parent
SOURCE = HERE.parent / 'correction_02/Amy_Mihaljevic_Mia_correction_02.wav'
ALIGNMENT = CASE / 'Automation/alignment_draft.json'
TEXT = CASE / 'Automation/Narration_Text.txt'
FULL_WAV = HERE / 'Amy_Mihaljevic_Mia_correction_03_gain_only.wav'
FULL_MP3 = HERE / 'Amy_Mihaljevic_Mia_correction_03_gain_only.mp3'
BEFORE_WAV = HERE / 'pilot_first_two_paragraphs_before_minus3db.wav'
BEFORE_MP3 = HERE / 'pilot_first_two_paragraphs_before_minus3db.mp3'
AFTER_WAV = HERE / 'pilot_first_two_paragraphs_pacing_minus3db.wav'
AFTER_MP3 = HERE / 'pilot_first_two_paragraphs_pacing_minus3db.mp3'
CUTS = HERE / 'pilot_pause_cuts.csv'
RECEIPT = HERE / 'audio_correction_03_receipt.json'
REPORT = HERE / 'Audio_Correction_03_Report.md'
RATE = 44100
FRAME = 441
GAIN_DB = -3.0
GUARD = round(.080 * RATE)
JOIN = round(.005 * RATE)
PILOT_END = round(56.7 * RATE)
TARGETS = {'clause': .300, 'sentence': .600, 'paragraph': .900}
COMMANDS = []

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def descriptor(path): return {'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)}
def run(argv):
    COMMANDS.append(argv)
    return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, check=True)
def encode(path, output):
    run(['ffmpeg','-hide_banner','-nostdin','-n','-i',str(path),'-ar',str(RATE),'-ac','1','-c:a','libmp3lame','-b:a','192k',str(output)])
def pcm_count(path):
    data=run(['ffmpeg','-v','error','-nostdin','-i',str(path),'-f','f32le','-ac','1','-ar',str(RATE),'pipe:1']).stdout
    return len(data)//4
def measure(path):
    probe=json.loads(run(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=codec_name,sample_rate,channels,duration,bits_per_raw_sample','-of','json',str(path)]).stdout)
    log=run(['ffmpeg','-hide_banner','-nostdin','-i',str(path),'-af','loudnorm=I=-20:TP=-2:LRA=7:print_format=json','-f','null','-']).stderr.decode('utf-8',errors='replace')
    loud,_=json.JSONDecoder().raw_decode(log[log.rfind('{'):])
    audio,rate=sf.read(path,dtype='float64')
    return {**descriptor(path),'probe':probe,'samples':len(audio),'duration_seconds':len(audio)/rate,'sample_peak_dbfs':float(20*np.log10(np.max(abs(audio))+1e-20)),'samples_at_or_above_full_scale':int(np.sum(abs(audio)>=1)),'loudness':{k:v for k,v in loud.items() if k.startswith('input_')}}
def db_rms(y):return float(20*np.log10(np.sqrt(np.mean(y*y))+1e-20))
def db_peak(y):return float(20*np.log10(np.max(abs(y))+1e-20))

if __name__=='__main__':
    started=datetime.now(timezone.utc).isoformat()
    outputs=[FULL_WAV,FULL_MP3,BEFORE_WAV,BEFORE_MP3,AFTER_WAV,AFTER_MP3,CUTS,RECEIPT,REPORT]
    for p in outputs:
        if p.exists():raise SystemExit('Refusing overwrite: '+str(p))
    assert sha(SOURCE)=='2c91f93c26182807405ab08434b2726dcde09eac31f1697fd5dba9379a731637'
    assert sha(TEXT)=='00157d1ad4473c3dbd447073c71baf54053ff85e62344a1149e5d7a5640eed37'
    source,rate=sf.read(SOURCE,dtype='float64')
    assert rate==RATE and len(source)==25161728
    text=TEXT.read_text(encoding='utf-8')
    paragraphs=text.strip().split('\n\n')
    words=json.loads(ALIGNMENT.read_text(encoding='utf-8'))['word_segments']
    assert text.split()==[w['word'] for w in words], 'Exact spoken source sequence changed'
    paragraph_ends={int(i)-1 for i in np.cumsum([len(p.split()) for p in paragraphs])}
    safe_plan=[];observations=[]
    for index,(previous,next_word) in enumerate(zip(words,words[1:])):
        if 'end' not in previous or 'start' not in next_word:continue
        kind='paragraph' if index in paragraph_ends else 'sentence' if re.search(r'[.!?][\'\"]?$',previous['word']) else 'clause' if re.search(r'[,;:][\'\"]?$',previous['word']) else None
        if kind is None:continue
        gap=next_word['start']-previous['end']
        desired=round(max(0,gap-TARGETS[kind])*RATE)
        observation={'word_index':index,'previous_word':previous['word'],'next_word':next_word['word'],'kind':kind,'original_gap_seconds':gap,'target_gap_seconds':TARGETS[kind]}
        observations.append(observation)
        if desired<round(.040*RATE):observation['result']='NO_EXCESS';continue
        if previous.get('score',0)<.5 or next_word.get('score',0)<.5:observation['result']='SKIP_LOW_ALIGNMENT_CONFIDENCE';continue
        start=round(previous['end']*RATE)+GUARD
        end=round(next_word['start']*RATE)-GUARD
        if end-start<round(.100*RATE):observation['result']='INSUFFICIENT_GUARDED_INTERIOR';continue
        previous_voice=source[max(0,round(previous['start']*RATE)):round(previous['end']*RATE)]
        next_voice=source[round(next_word['start']*RATE):min(len(source),round(next_word['end']*RATE))]
        adjacent_reference=min(db_rms(previous_voice),db_rms(next_voice))
        rms_limit=min(-62.0,adjacent_reference-22.0)
        peak_limit=-51.0
        blocks=[source[i:i+FRAME] for i in range(start,end-FRAME+1,FRAME)]
        if not blocks:observation['result']='NO_COMPLETE_ANALYSIS_FRAMES';continue
        rms=np.array([db_rms(block) for block in blocks])
        peak=np.array([db_peak(block) for block in blocks])
        quiet=(rms<=rms_limit)&(peak<=peak_limit)
        # Protect every stronger breath/noise/phoneme-like island plus 20ms on
        # either side. Only the remaining low-energy continuous middle is cut.
        quiet=ndimage.binary_erosion(quiet,structure=np.ones(5),border_value=0)
        edges=np.diff(np.r_[False,quiet,False].astype(int))
        lefts=np.where(edges==1)[0];rights=np.where(edges==-1)[0]
        options=[]
        for left,right in zip(lefts,rights):
            a=start+int(left)*FRAME+JOIN
            b=start+int(right)*FRAME-JOIN
            available=b-a
            if available>=round(.040*RATE):options.append((available,a,b))
        if not options:observation['result']='NO_LONG_ENOUGH_VERIFIED_QUIET_RUN';continue
        available,a,b=max(options)
        remove=min(desired,available)
        a=a+(available-remove)//2;b=a+remove
        # Verify the removed portion and the retained 5ms join shoulders.
        verify=source[a-JOIN:b+JOIN]
        assert a>=start and b<=end
        assert db_peak(verify)<=peak_limit+1e-8
        assert db_rms(verify)<=rms_limit+1e-8
        cut={**observation,'previous_word_end_seconds':previous['end'],'next_word_start_seconds':next_word['start'],'cut_start_sample':a,'cut_end_sample_exclusive':b,'cut_start_seconds':a/RATE,'cut_end_seconds':b/RATE,'removed_samples':remove,'removed_seconds':remove/RATE,'resulting_gap_seconds':gap-remove/RATE,'adjacent_word_rms_reference_dbfs':adjacent_reference,'quiet_rms_limit_dbfs':rms_limit,'quiet_peak_limit_dbfs':peak_limit,'removed_rms_dbfs':db_rms(source[a:b]),'removed_peak_dbfs':db_peak(source[a:b]),'retained_join_shoulders_verified':True,'aligned_word_edge_guard_ms':80,'machine_alignment_scores':[previous['score'],next_word['score']],'result':'CANDIDATE_SAFE_QUIET_INTERIOR_ONLY'}
        safe_plan.append(cut)
        observation['result']='VERIFIED_QUIET_CUT_AVAILABLE'
    pilot_plan=[c for c in safe_plan if c['cut_end_sample_exclusive']<PILOT_END]
    assert pilot_plan, 'No validated pilot cuts'
    gain=10**(GAIN_DB/20)
    leveled=source*gain
    sf.write(FULL_WAV,leveled,RATE,subtype='PCM_24');encode(FULL_WAV,FULL_MP3)
    before=leveled[:PILOT_END].copy()
    after_parts=[];cursor=0;removed_before=0
    for cut in pilot_plan:
        a=cut['cut_start_sample'];b=cut['cut_end_sample_exclusive']
        piece=before[cursor:a].copy()
        assert len(piece)>=JOIN
        piece[-JOIN:]*=np.linspace(1,0,JOIN)
        if cursor:piece[:JOIN]*=np.linspace(0,1,JOIN)
        after_parts.append(piece)
        cut['pilot_output_join_sample']=a-removed_before
        cut['pilot_output_join_seconds']=(a-removed_before)/RATE
        removed_before+=b-a;cursor=b
    last=before[cursor:].copy();last[:JOIN]*=np.linspace(0,1,JOIN);after_parts.append(last)
    after=np.concatenate(after_parts)
    assert len(after)==len(before)-sum(c['removed_samples'] for c in pilot_plan)
    assert np.max(abs(after))<=np.max(abs(before))+1e-15
    sf.write(BEFORE_WAV,before,RATE,subtype='PCM_24');encode(BEFORE_WAV,BEFORE_MP3)
    sf.write(AFTER_WAV,after,RATE,subtype='PCM_24');encode(AFTER_WAV,AFTER_MP3)
    print('PILOT_READY '+str(AFTER_MP3),flush=True)
    with CUTS.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(pilot_plan[0]));writer.writeheader();writer.writerows(pilot_plan)
    source_metrics=measure(SOURCE)
    gain_metrics=measure(FULL_WAV)
    before_metrics=measure(BEFORE_WAV)
    after_metrics=measure(AFTER_WAV)
    assert pcm_count(FULL_MP3)==len(source)
    assert pcm_count(BEFORE_MP3)==len(before)
    assert pcm_count(AFTER_MP3)==len(after)
    assert sha(SOURCE)=='2c91f93c26182807405ab08434b2726dcde09eac31f1697fd5dba9379a731637'
    full_potential=sum(c['removed_samples'] for c in safe_plan)
    potential_duration=(len(source)-full_potential)/RATE
    report=f'''# Amy correction 03 — level fix and pacing pilot

The full gain-only master is another 3 dB quieter, retains all {len(source):,} samples and lasts {len(source)/RATE:.9f} seconds. No makeup gain or loudness normalization follows it.

The listening pilot covers the original 0–56.700 seconds: Amy's first two paragraphs, ending before paragraph three. Both previews use exactly the same -3 dB sample gain. {len(pilot_plan)} conservative interior cuts remove {removed_before/RATE:.6f} seconds; the pacing version lasts {len(after)/RATE:.6f} seconds. Speech has not been sped up. The approved text and punctuation were not edited.

The analysis treats machine word gaps as candidates only. Every proposed cut has at least 80 ms protection from both aligned word edges, sufficiently confident neighboring word alignment, measured quietness at least 22 dB below the quieter adjacent word, an absolute RMS ceiling of -62 dBFS, peak ceiling -51 dBFS, and 20 ms protection around stronger breath/transient activity. Only one verified continuous quiet interior per punctuation gap is shortened. Retained quiet shoulders receive 5 ms fades. No word-boundary audio is cut. Some pauses remain longer than the desired 300 ms clause, 600 ms sentence and 900 ms paragraph targets because quietness and breath protection take precedence.

Across the full episode the same conservative criteria identify {len(safe_plan)} possible cuts totaling {full_potential/RATE:.6f} seconds, which would leave {potential_duration:.6f} seconds. This is a bounded machine-screened potential, not authorization or an auditory guarantee. No full paced episode was created. It {'stays above' if potential_duration>=480 else 'falls below'} the 480-second release minimum; never pad or force a duration result.

Full gain-only level: {gain_metrics['loudness']['input_i']} LUFS / {gain_metrics['loudness']['input_tp']} dBTP. Pilot before: {before_metrics['loudness']['input_i']} LUFS; pilot pacing: {after_metrics['loudness']['input_i']} LUFS. The pilot may have slightly higher integrated loudness because silence occupies less time, despite identical sample gain and no higher peak.

Listening review is pending. Signal tests cannot prove every faint breath or consonant is preserved, and machine timing can be imperfect. Brody's statement that correction 02 sounds better was partial feedback, not full-master approval. The full gain-only version keeps the old timeline; any later full pacing correction changes timing and requires alignment, captions, shot timing and audio preflight to be remapped and reviewed before video assembly.
'''
    REPORT.write_text(report,encoding='utf-8')
    receipt={'schema_version':'cold_truth.audio_level_and_pacing_pilot.v1','status':'PILOT_AWAITING_LISTENING_NO_FULL_PACED_EPISODE','started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'role':'Editor','case_id':'amy-mihaljevic','narration_branch':'youtube-longform','source':source_metrics,'approved_text':descriptor(TEXT),'timing_candidate_input':descriptor(ALIGNMENT),'settings':{'global_gain_db':GAIN_DB,'makeup_gain':False,'normalization':False,'whole_voice_speed_change':False,'targets_seconds':TARGETS,'word_edge_guard_ms':80,'neighbor_alignment_min_score':.5,'analysis_frame_samples':FRAME,'quiet_rms_absolute_ceiling_dbfs':-62,'quiet_rms_below_quieter_adjacent_word_db':22,'quiet_peak_ceiling_dbfs':-51,'stronger_activity_guard_ms':20,'minimum_cut_ms':40,'join_fades_ms':5,'cut_policy':'Only longest verified quiet interior run of each source punctuation gap; preserve stronger activity and never force target gap duration.'},'full_gain_only':gain_metrics,'pilot':{'source_start_sample':0,'source_end_sample_exclusive':PILOT_END,'source_start_seconds':0,'source_end_seconds':56.7,'paragraph_count':2,'before':before_metrics,'after':after_metrics,'removed_samples':removed_before,'removed_seconds':removed_before/RATE,'cut_count':len(pilot_plan),'cuts':pilot_plan,'identical_minus3db_sample_gain':True,'before_preview':descriptor(BEFORE_MP3),'after_preview':descriptor(AFTER_MP3)},'full_episode_machine_screened_potential':{'candidate_cut_count':len(safe_plan),'maximum_under_this_conservative_plan_samples':full_potential,'maximum_under_this_conservative_plan_seconds':full_potential/RATE,'resulting_duration_seconds':potential_duration,'at_least480_seconds':potential_duration>=480,'not_a_full_pacing_output':True,'not_an_auditory_safety_guarantee':True,'candidate_cuts':safe_plan},'punctuation_gap_observations':observations,'timeline':{'full_gain_only_samples':len(leveled),'original_samples':len(source),'full_gain_only_duration_unchanged':True,'pilot_duration_changed':True,'full_paced_episode_created':False,'future_full_pacing_invalidates_old_alignment_and_captions':True},'human_listening_approved':False,'partial_feedback_does_not_approve_full_master':True,'assembly_allowed':False,'video_rendered':False,'tts_calls':0,'software_installs':0,'model_downloads':0,'canonical_preflight_and_state_untouched':True,'commands':COMMANDS,'tool_versions':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'soundfile':sf.__version__,'ffmpeg':run(['ffmpeg','-version']).stdout.decode('utf-8').splitlines()[0]},'processor':descriptor(Path(__file__)),'outputs':[descriptor(p) for p in outputs if p!=RECEIPT],'receipt_self_hash_omitted':True,'limitations':['No subjective listening approval is claimed.','Machine word alignment and signal thresholds cannot perfectly classify breaths or phonemes; user audition remains essential.','Conservative criteria deliberately leave gaps longer than targets where stronger activity or uncertain timing prevents safe trimming.','Full-episode potential is limited to this exact method and its numerical screening, not a maximal possible edit or permission to execute it.']}
    RECEIPT.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'receipt':descriptor(RECEIPT),'full_gain_master':descriptor(FULL_WAV),'full_gain_preview':descriptor(FULL_MP3),'pilot_before':descriptor(BEFORE_MP3),'pilot_after':descriptor(AFTER_MP3),'pilot_cuts':len(pilot_plan),'removed_seconds':removed_before/RATE,'before_seconds':len(before)/RATE,'after_seconds':len(after)/RATE,'full_episode_potential_cut_seconds':full_potential/RATE,'full_potential_remaining_seconds':potential_duration,'total_output_files':len(list(HERE.iterdir())),'total_output_bytes':sum(p.stat().st_size for p in HERE.iterdir() if p.is_file())},indent=2),flush=True)
