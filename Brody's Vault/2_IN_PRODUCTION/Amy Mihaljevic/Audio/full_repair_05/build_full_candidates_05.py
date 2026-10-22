"""Two local audition candidates: exact repair04 transfer, then guarded pacing.

No synthesis, external calls, timing approval, canonical changes, or video work.
"""
from pathlib import Path
from datetime import datetime, timezone
import bisect
import csv
import hashlib
import json
import re
import subprocess
import sys
import numpy as np
import scipy
from scipy import ndimage
import soundfile as sf

HERE=Path(__file__).resolve().parent
CASE=HERE.parent.parent
SOURCE=HERE.parent/'correction_03/Amy_Mihaljevic_Mia_correction_03_gain_only.wav'
DIAGNOSTIC=HERE.parent/'diagnostic_04/diagnostic_04_receipt.json'
DIAGNOSTIC_WAV=HERE.parent/'diagnostic_04/opening_13p2s_onset_repair.wav'
ALIGN=CASE/'Automation/alignment_draft.json'
TEXT=CASE/'Automation/Narration_Text.txt'
REPAIRED=HERE/'Amy_Mihaljevic_Mia_full_repair_05_original_timing.wav'
PACED=HERE/'Amy_Mihaljevic_Mia_full_repair_05_pacing_candidate.wav'
CUT_MAP=HERE/'pacing_cut_map_draft.json'
CUT_CSV=HERE/'pacing_cuts.csv'
WORD_DRAFT=HERE/'remapped_word_timing_draft.json'
RECEIPT=HERE/'full_repair_05_receipt.json'
REPORT=HERE/'Full_Repair_05_Report.md'
RATE=44100
FRAME=441
GUARD=round(.100*RATE)
JOIN=round(.005*RATE)
FOLDER_LIMIT=500*1024**2
TARGETS={'clause':.350,'sentence':.700,'paragraph':1.000}
REMOVAL_CAPS={'clause':.300,'sentence':.550,'paragraph':.350}
COMMANDS=[]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def desc(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def run(argv):
    COMMANDS.append(argv)
    return subprocess.run(argv,stdin=subprocess.DEVNULL,capture_output=True,check=True)
def write_json(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def encode(path):
    output=path.with_suffix('.mp3')
    run(['ffmpeg','-hide_banner','-nostdin','-n','-i',str(path),'-ar',str(RATE),'-ac','1','-c:a','libmp3lame','-b:a','192k',str(output)])
    return output
def encode_excerpt(y,path):
    argv=['ffmpeg','-hide_banner','-nostdin','-n','-f','f64le','-ar',str(RATE),'-ac','1','-i','pipe:0','-c:a','libmp3lame','-b:a','192k',str(path)]
    COMMANDS.append(argv)
    subprocess.run(argv,input=np.asarray(y,dtype='<f8').tobytes(),capture_output=True,check=True)
def pcm_count(path):
    raw=run(['ffmpeg','-v','error','-nostdin','-i',str(path),'-f','f32le','-ac','1','-ar',str(RATE),'pipe:1']).stdout
    return len(raw)//4
def rms(y):return float(20*np.log10(np.sqrt(np.mean(y*y))+1e-20))
def peak(y):return float(20*np.log10(np.max(abs(y))+1e-20))
def measure(path):
    data,rate=sf.read(path,dtype='float64')
    log=run(['ffmpeg','-hide_banner','-nostdin','-i',str(path),'-af','loudnorm=I=-20:TP=-2:LRA=7:print_format=json','-f','null','-']).stderr.decode('utf-8',errors='replace')
    loud,_=json.JSONDecoder().raw_decode(log[log.rfind('{'):])
    return {**desc(path),'samples':len(data),'duration_seconds':len(data)/rate,'sample_rate':rate,'channels':1,'subtype':sf.info(path).subtype,'sample_peak_dbfs':peak(data),'samples_at_or_above_full_scale':int(np.sum(abs(data)>=1)),'loudness':{k:v for k,v in loud.items() if k.startswith('input_')}}
def intersects(a,b,regions):return any(a<d and b>c for c,d in regions)

if __name__=='__main__':
    started=datetime.now(timezone.utc).isoformat()
    expected_files=[REPAIRED,REPAIRED.with_suffix('.mp3'),PACED,PACED.with_suffix('.mp3'),CUT_MAP,CUT_CSV,WORD_DRAFT,RECEIPT,REPORT]
    for p in expected_files:
        if p.exists():raise SystemExit('Refusing overwrite: '+str(p))
    assert sha(SOURCE)=='094bfbeafc865b5941efbaae09755e8f2f98c8b0cd9d270418f8557f2d1aaa25'
    assert sha(TEXT)=='00157d1ad4473c3dbd447073c71baf54053ff85e62344a1149e5d7a5640eed37'
    source,rate=sf.read(SOURCE,dtype='float64');assert rate==RATE and len(source)==25161728
    assert len(source)*3*2+30_000_000<FOLDER_LIMIT
    diagnostic=json.loads(DIAGNOSTIC.read_text(encoding='utf-8'))
    words=json.loads(ALIGN.read_text(encoding='utf-8'))['word_segments']
    text=TEXT.read_text(encoding='utf-8');paragraphs=text.strip().split('\n\n')
    assert [w['word'] for w in words]==text.split() and len(words)==1267
    paragraph_counts=np.cumsum([len(p.split()) for p in paragraphs]).tolist()
    paragraph_ends={i-1 for i in paragraph_counts}
    gain=np.ones(len(source));repair_regions=[]
    for op in diagnostic['operations']:
        a,b,c,d=[round(op[key]*RATE) for key in ('start_seconds','full_reduction_start_seconds','full_reduction_end_seconds','end_seconds')]
        env=np.ones(d-a)
        env[:b-a]=.5-.5*np.cos(np.linspace(0,np.pi,b-a))
        env[c-a:]=.5+.5*np.cos(np.linspace(0,np.pi,d-c))
        gain[a:d]*=10**(-op['maximum_reduction_db']*env/20)
        repair_regions.append((a,d))
    repaired=source*gain
    sf.write(REPAIRED,repaired,RATE,subtype='PCM_24')
    repaired,rate=sf.read(REPAIRED,dtype='float64')
    diagnostic_pcm,_=sf.read(DIAGNOSTIC_WAV,dtype='float64')
    assert np.array_equal(repaired[:len(diagnostic_pcm)],diagnostic_pcm)
    unchanged=gain==1
    assert np.array_equal(repaired[unchanged],source[unchanged])
    encode(REPAIRED)
    print('Original-timing repair written; exact diagnostic04 prefix and outside-window PCM identity verified',flush=True)
    cuts=[];observations=[]
    for index,(left_word,right_word) in enumerate(zip(words,words[1:])):
        kind='paragraph' if index in paragraph_ends else 'sentence' if re.search(r'[.!?][\'\"]?$',left_word['word']) else 'clause' if re.search(r'[,;:][\'\"]?$',left_word['word']) else None
        if kind is None:continue
        gap=right_word['start']-left_word['end']
        desired=round(max(0,gap-TARGETS[kind])*RATE)
        observation={'word_index':index,'left_word':left_word['word'],'right_word':right_word['word'],'kind':kind,'original_gap_seconds':gap,'target_gap_seconds':TARGETS[kind]}
        observations.append(observation)
        if desired<round(.060*RATE):observation['result']='NO_EXCESS_GAP';continue
        if min(left_word.get('score',0),right_word.get('score',0))<.6:observation['result']='PROTECTED_LOW_WORD_TIMING_CONFIDENCE';continue
        start=round((left_word['end']+.100)*RATE);end=round((right_word['start']-.100)*RATE)
        if end-start<round(.130*RATE):observation['result']='NO_GUARDED_INTERIOR';continue
        frame_starts=np.arange(start,end-FRAME+1,FRAME,dtype=int)
        frames=[repaired[i:i+FRAME] for i in frame_starts]
        frame_rms=np.array([rms(f) for f in frames]);frame_peaks=np.array([peak(f) for f in frames])
        voice_left=repaired[round(left_word['start']*RATE):round(left_word['end']*RATE)]
        voice_right=repaired[round(right_word['start']*RATE):round(right_word['end']*RATE)]
        reference=min(rms(voice_left),rms(voice_right))
        local_floor=float(np.percentile(frame_rms,20))
        rms_limit=min(-54.0,local_floor+5.0,reference-18.0)
        peak_limit=rms_limit+12.0
        quiet=(frame_rms<=rms_limit)&(frame_peaks<=peak_limit)
        for j,position in enumerate(frame_starts):
            if intersects(int(position),int(position+FRAME),repair_regions):quiet[j]=False
        quiet=ndimage.binary_erosion(quiet,structure=np.ones(5),border_value=0)
        transitions=np.diff(np.r_[False,quiet,False].astype(int))
        lo=np.where(transitions==1)[0];hi=np.where(transitions==-1)[0]
        options=[]
        for l,h in zip(lo,hi):
            a=start+int(l)*FRAME+JOIN;b=start+int(h)*FRAME-JOIN
            available=b-a
            if available>=round(.060*RATE):options.append((available,a,b))
        observation.update({'local_floor_dbfs':local_floor,'quiet_rms_limit_dbfs':rms_limit,'quiet_peak_limit_dbfs':peak_limit,'adjacent_word_rms_reference_dbfs':reference})
        if not options:observation['result']='NO_VERIFIED_QUIET_RUN_PRESERVE_ACTIVITY';continue
        available,a,b=max(options)
        remove=min(desired,available,round(REMOVAL_CAPS[kind]*RATE))
        if remove<round(.060*RATE):observation['result']='TOO_SMALL_TO_EDIT';continue
        a+=(available-remove)//2;b=a+remove
        verification=repaired[a-JOIN:b+JOIN]
        assert not intersects(a-JOIN,b+JOIN,repair_regions)
        assert peak(verification)<=peak_limit+1e-8 and rms(verification)<=rms_limit+1e-8
        assert a-JOIN>=round(left_word['end']*RATE)+round(.080*RATE)
        assert b+JOIN<=round(right_word['start']*RATE)-round(.080*RATE)
        cut={**observation,'input_start_sample':a,'input_end_sample_exclusive':b,'input_start_seconds':a/RATE,'input_end_seconds':b/RATE,'removed_samples':remove,'removed_seconds':remove/RATE,'remaining_gap_seconds':gap-remove/RATE,'removed_rms_dbfs':rms(repaired[a:b]),'removed_peak_dbfs':peak(repaired[a:b]),'quiet_join_shoulders_verified':True,'left_word_end_seconds':left_word['end'],'right_word_start_seconds':right_word['start'],'word_guard_ms':100,'neighbor_timing_scores':[left_word['score'],right_word['score']]}
        cuts.append(cut);observation['result']='CANDIDATE_QUIET_CUT'
    assert cuts,'No safe supported pacing route; original-timing repair retained'
    removed_total=sum(c['removed_samples'] for c in cuts)
    final_samples=len(repaired)-removed_total
    assert final_samples/RATE>=480,'Pacing blocked below480seconds; do not pad'
    parts=[];cursor=0;shift=0
    for cut in cuts:
        a=cut['input_start_sample'];b=cut['input_end_sample_exclusive']
        piece=repaired[cursor:a].copy();assert len(piece)>=JOIN
        piece[-JOIN:]*=np.linspace(1,0,JOIN)
        if cursor:piece[:JOIN]*=np.linspace(0,1,JOIN)
        parts.append(piece)
        cut['output_join_sample']=a-shift;cut['output_join_seconds']=(a-shift)/RATE
        shift+=b-a;cursor=b
    last=repaired[cursor:].copy();last[:JOIN]*=np.linspace(0,1,JOIN);parts.append(last)
    paced=np.concatenate(parts)
    assert len(paced)==final_samples and np.max(abs(paced))<=np.max(abs(repaired))+1e-15
    sf.write(PACED,paced,RATE,subtype='PCM_24');encode(PACED)
    paced,_=sf.read(PACED,dtype='float64')
    cut_ends=[c['input_end_sample_exclusive'] for c in cuts]
    cumulative=np.cumsum([0]+[c['removed_samples'] for c in cuts]).tolist()
    def remap(sample):
        assert not any(c['input_start_sample']<sample<c['input_end_sample_exclusive'] for c in cuts)
        return sample-cumulative[bisect.bisect_right(cut_ends,sample)]
    remapped=[];word_audio_exact=True
    for index,word in enumerate(words):
        a=round(word['start']*RATE);b=round(word['end']*RATE)
        mapped_a,mapped_b=remap(a),remap(b)
        assert np.array_equal(repaired[a:b],paced[mapped_a:mapped_b]),'Spoken word PCM changed during pacing'
        remapped.append({**word,'start':mapped_a/RATE,'end':mapped_b/RATE,'start_sample':mapped_a,'end_sample_exclusive':mapped_b,'original_start':word['start'],'original_end':word['end'],'original_word_index':index,'paragraph_id':bisect.bisect_right(paragraph_counts,index)+1})
    assert [w['word'] for w in remapped]==text.split()
    assert all(0<=w['start']<=w['end']<=len(paced)/RATE for w in remapped)
    assert all(remapped[i]['start']>=remapped[i-1]['end'] for i in range(1,len(remapped)))
    mapped_repairs=[]
    for op,(a,b) in zip(diagnostic['operations'],repair_regions):
        ma,mb=remap(a),remap(b)
        assert np.array_equal(repaired[a:b],paced[ma:mb])
        mapped_repairs.append({'type':op['type'],'source_start_sample':a,'source_end_sample_exclusive':b,'paced_start_sample':ma,'paced_end_sample_exclusive':mb,'paced_start_seconds':ma/RATE,'paced_end_seconds':mb/RATE,'exact_pcm_preserved':True})
    cut_record={'schema_version':'cold_truth.pacing_cut_map_draft.v1','status':'MACHINE_SCREENED_AUDITION_ONLY','source_audio':desc(REPAIRED),'paced_audio':desc(PACED),'approved_text':desc(TEXT),'word_timing_source':desc(ALIGN),'sample_rate':RATE,'original_samples':len(repaired),'paced_samples':len(paced),'removed_samples':removed_total,'removed_seconds':removed_total/RATE,'cuts':cuts,'observations':observations,'protected_repair_windows':mapped_repairs,'human_reviewed':False,'approval_inferred':False}
    write_json(CUT_MAP,cut_record)
    with CUT_CSV.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(cuts[0]));writer.writeheader();writer.writerows(cuts)
    paragraph_rows=[];first=0
    for paragraph_id,(paragraph,last_index) in enumerate(zip(paragraphs,paragraph_counts),1):
        group=remapped[first:last_index]
        paragraph_rows.append({'paragraph_id':paragraph_id,'text':paragraph,'word_start_index':first,'word_end_index_exclusive':last_index,'start':group[0]['start'],'end':group[-1]['end'],'original_start':words[first]['start'],'original_end':words[last_index-1]['end']})
        first=last_index
    timing={'schema_version':'cold_truth.remapped_word_timing_draft.v1','status':'DRAFT_NOT_HUMAN_REVIEWED','case_id':'amy-mihaljevic','narration_branch':'youtube-longform','audio':desc(PACED),'approved_text':desc(TEXT),'source_word_timing':desc(ALIGN),'cut_map':desc(CUT_MAP),'duration_seconds':len(paced)/RATE,'sample_rate':RATE,'source_text':text,'word_segments':remapped,'paragraphs':paragraph_rows,'word_count':len(remapped),'qa':{'exact_approved_word_sequence':True,'word_pcm_identical_to_original_timing_repair':True,'no_negative_inverted_or_overlapping_words':True,'cuts_avoid_all_word_intervals_and_repair_windows':True},'timing_review':{'human_reviewed':False,'approved':False,'reviewer':None},'old_alignment_and_captions_invalid_for_this_paced_audio':True,'assembly_allowed':False}
    write_json(WORD_DRAFT,timing)
    samples=[]
    for label,target in [('opening',0),('middle',300),('end',500)]:
        row=paragraph_rows[0] if target==0 else min(paragraph_rows,key=lambda p:0 if p['original_start']<=target<=p['original_end'] else min(abs(p['original_start']-target),abs(p['original_end']-target)))
        start=0 if target==0 else max(0,round((row['original_start']-.1)*RATE))
        finish=min(len(source),round((row['original_end']+.2)*RATE))
        # End at a retained sample boundary outside any proposed quiet removal.
        for cut in cuts:
            if cut['input_start_sample']<=finish<cut['input_end_sample_exclusive']:finish=cut['input_start_sample']
            if cut['input_start_sample']<start<cut['input_end_sample_exclusive']:start=cut['input_end_sample_exclusive']
        mapped_start,mapped_finish=remap(start),remap(finish)
        before_file=HERE/f'{label}_paragraph_before.mp3';after_file=HERE/f'{label}_paragraph_after_pacing.mp3'
        assert not before_file.exists() and not after_file.exists()
        encode_excerpt(source[start:finish],before_file)
        encode_excerpt(paced[mapped_start:mapped_finish],after_file)
        assert pcm_count(before_file)==finish-start
        assert pcm_count(after_file)==mapped_finish-mapped_start
        samples.append({'label':label,'paragraph_id':row['paragraph_id'],'complete_approved_paragraph_text':row['text'],'before_source_start_sample':start,'before_source_end_sample_exclusive':finish,'before_source_start_seconds':start/RATE,'before_source_end_seconds':finish/RATE,'after_paced_start_sample':mapped_start,'after_paced_end_sample_exclusive':mapped_finish,'after_paced_start_seconds':mapped_start/RATE,'after_paced_end_seconds':mapped_finish/RATE,'before_duration_seconds':(finish-start)/RATE,'after_duration_seconds':(mapped_finish-mapped_start)/RATE,'before':desc(before_file),'after':desc(after_file),'same_baseline_gain':True,'note':'Before is correction03 source, after includes exact diagnostic04 repair where applicable plus proposed pacing; no new global gain.'})
    print(f'Both full candidates and three complete-paragraph A/B pairs ready;{len(cuts)}cuts,{removed_total/RATE:.6f}s removed,{len(paced)/RATE:.6f}s paced duration',flush=True)
    original_metrics=measure(SOURCE);repair_metrics=measure(REPAIRED);paced_metrics=measure(PACED)
    assert pcm_count(REPAIRED.with_suffix('.mp3'))==len(source)
    assert pcm_count(PACED.with_suffix('.mp3'))==len(paced)
    assert repair_metrics['samples_at_or_above_full_scale']==0 and paced_metrics['samples_at_or_above_full_scale']==0
    assert sha(SOURCE)=='094bfbeafc865b5941efbaae09755e8f2f98c8b0cd9d270418f8557f2d1aaa25'
    assert sha(TEXT)=='00157d1ad4473c3dbd447073c71baf54053ff85e62344a1149e5d7a5640eed37'
    total_before_receipt=sum(p.stat().st_size for p in HERE.iterdir() if p.is_file())
    assert total_before_receipt<FOLDER_LIMIT
    report=f'''# Full repair 05 — two local listening candidates

The original-timing candidate transfers exactly the two diagnostic-04 gain windows to the full correction-03 source. Its first 13.2 seconds matches the saved diagnostic WAV exactly; every persisted PCM sample outside the two windows is identical to correction03. It retains {len(source):,} samples / {len(source)/RATE:.9f} seconds. This does not imply that Brody accepted the diagnostic or full master.

The separate pacing candidate removes {len(cuts)} verified quiet interiors totaling {removed_total/RATE:.6f} seconds, leaving {len(paced)/RATE:.6f} seconds ({int(len(paced)/RATE)//60}:{len(paced)/RATE%60:05.2f}). It remains above 480 seconds without padding or speeding. All 1,267 words preserve the approved sequence and have PCM samples identical to the original-timing repaired candidate. Stronger gap activity and mild breaths are protected; the two manually repaired windows are retained exactly and their new locations are recorded.

Only punctuation gaps are eligible. Clause/sentence/paragraph goals are 350/700/1000 ms, with maximum removals 300/550/350 ms and no forced target. Word-edge guards are 100 ms; neighboring machine word scores must be at least0.6. The per-gap quiet limit is the smaller of local20th-percentile floor+5 dB, quieter adjacent-word RMS-18 dB, and -54 dBFS. Peak limits,20 ms activity protection, minimum60 ms removal and5 ms quiet joins guard against cutting phonemes or breath cores. These are technical screens, not proof of subjective naturalness.

Original correction03 measures {original_metrics['loudness']['input_i']} LUFS. Original-timing repair measures {repair_metrics['loudness']['input_i']} LUFS / {repair_metrics['loudness']['input_tp']} dBTP. Paced candidate measures {paced_metrics['loudness']['input_i']} LUFS / {paced_metrics['loudness']['input_tp']} dBTP. No additional global gain, makeup, normalization, EQ, compression or limiter was added.

Three complete-paragraph before/after examples cover the opening, the paragraph containing300 seconds and the paragraph containing500 seconds. Their actual source/output bounds are in the receipt. The new word timing is a machine-remapped DRAFT, not reviewed alignment or captions. All old alignment/caption timing is invalid for the paced version until remapped and reviewed; the canonical files were not changed.

No paid/provider calls, new narration, ASR/model/software download, video render or publishing occurred. Both full candidates and all comparisons await actual human listening; no approval is inferred from permission to continue local work. If a breath, diction or cadence issue remains, retain the original-timing candidate and revise only reviewed locations rather than forcing more silence removal.
'''
    REPORT.write_text(report,encoding='utf-8')
    receipt={'schema_version':'cold_truth.full_repair_and_guarded_pacing_candidates.v1','status':'TWO_FULL_CANDIDATES_AWAIT_HUMAN_LISTENING','started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'role':'Editor','user_direction_quote':'proceed until usage runs out dont spend credits','authority_interpretation':'Continue bounded reversible local audio work only; no listening approval, paid/provider calls, new narration or video render inferred.','case_id':'amy-mihaljevic','narration_branch':'youtube-longform','source':original_metrics,'exact_diagnostic_reference':desc(DIAGNOSTIC),'exact_diagnostic_wav':desc(DIAGNOSTIC_WAV),'approved_text':desc(TEXT),'existing_machine_word_timing':desc(ALIGN),'original_timing_repair':repair_metrics,'paced_candidate':paced_metrics,'full_mp3_previews':[desc(REPAIRED.with_suffix('.mp3')),desc(PACED.with_suffix('.mp3'))],'repair_qa':{'diagnostic_prefix_samples':len(diagnostic_pcm),'prefix_pcm_identical':True,'outside_gain_windows_pcm_identical_to_correction03':True,'repair_windows':diagnostic['operations'],'mapped_repair_windows':mapped_repairs,'additional_global_gain_db':0},'pacing_qa':{'cuts':len(cuts),'removed_samples':removed_total,'removed_seconds':removed_total/RATE,'duration_seconds':len(paced)/RATE,'minimum480_seconds_passed':len(paced)/RATE>=480,'all1267_word_pcm_regions_identical_to_repaired_audio':True,'exact_approved_spoken_sequence':True,'word_count':len(remapped),'negative_inverted_or_overlapping_word_intervals':0,'word_edge_guard_ms':100,'protected_activity_guard_ms':20,'neighbor_min_ctc_score':.6,'quiet_limit_formula':'min(-54, local_gap_20th_percentile_rms+5, quieter_adjacent_word_rms-18)','quiet_peak_limit_formula':'quiet_rms_limit+12','analysis_frame_ms':10,'minimum_removal_ms':60,'join_fades_ms':5,'targets_seconds':TARGETS,'maximum_removal_per_gap_seconds':REMOVAL_CAPS,'unpunctuated_word_gaps_unchanged':True,'no_whole_voice_speedup':True,'no_padding':True,'no_changes_inside_repair_windows':True},'cut_map':desc(CUT_MAP),'cut_csv':desc(CUT_CSV),'remapped_word_timing_draft':desc(WORD_DRAFT),'actual_paragraph_comparisons':samples,'timing_and_authority':{'human_listening_approved':False,'remapped_timing_reviewed':False,'canonical_alignment_changed':False,'canonical_preflight_changed':False,'canonical_scripts_changed':False,'state_or_manifest_changed':False,'assembly_allowed':False,'old_caption_sync_invalid_for_paced_candidate':True},'limits':{'new_folder_maximum_bytes':FOLDER_LIMIT,'total_before_receipt_bytes':total_before_receipt,'provider_or_paid_calls':0,'tts_calls':0,'asr_calls':0,'model_or_software_downloads':0,'video_renders':0},'commands':COMMANDS,'tool_versions':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'soundfile':sf.__version__,'ffmpeg':run(['ffmpeg','-version']).stdout.decode('utf-8').splitlines()[0]},'processor':desc(Path(__file__)),'output_files':[desc(p) for p in HERE.iterdir() if p.is_file() and p!=RECEIPT],'receipt_self_hash_omitted':True,'limitations':['Signal thresholds and machine timing do not guarantee natural delivery or perfectly classify breath sounds.','Human listening approval is not inferred; both full audio candidates are provisional.','No claim of final synchronization, reviewed captions or assembly readiness is made.','The finite quiet-cut plan is conservative; it does not remove every long pause or every comma.']}
    write_json(RECEIPT,receipt)
    total=sum(p.stat().st_size for p in HERE.iterdir() if p.is_file())
    assert total<FOLDER_LIMIT
    print(json.dumps({'receipt':desc(RECEIPT),'original_timing_repair':desc(REPAIRED),'paced_candidate':desc(PACED),'word_draft':desc(WORD_DRAFT),'cut_count':len(cuts),'removed_seconds':removed_total/RATE,'paced_seconds':len(paced)/RATE,'repaired_loudness':repair_metrics['loudness'],'paced_loudness':paced_metrics['loudness'],'output_files':len(list(HERE.iterdir())),'total_output_bytes':total},indent=2),flush=True)
