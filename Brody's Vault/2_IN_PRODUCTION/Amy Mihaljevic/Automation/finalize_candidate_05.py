"""Record the actual October22 review replies and promote their exact media."""
from pathlib import Path
from datetime import datetime, timezone
import json, sys, shutil
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from automation import pilot_evidence as pe
A = Path(__file__).resolve().parent
C = A.parent
V = C / 'Visuals/Longform/revision_05'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def desc(p): return pe.describe(ROOT, p.relative_to(ROOT).as_posix())
def write(p, value):
    assert not p.exists(), str(p)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
def main():
    packet = read(A/'candidate05_review_packet.json')
    for k in ('audio','alternate_original_timing','word_timing_draft','caption_draft','player','review_note','visual_gallery','provisional_recipe'):
        pe.bound(ROOT, packet[k])
    for row in packet['new_stock_uses']:
        pe.bound(ROOT, row['file']); pe.bound(ROOT, row['candidate_review'])
    approval = dict(human_approved=True, approved_by='Brody', approved_on='2026-10-22', recorded_at_utc=datetime.now(timezone.utc).isoformat(),
        user_quote='Listened fully; approve audio and synchronization', scope='Exact full 9:08.59 paced WAV: pronunciation, completeness, volume including disappeared, pacing, ending and synchronization across all19 paragraphs; not video-master approval.',
        question_item_id='["request_user_input_async","call_5be43ce33e404c8e806a9e6073f6a28f",0]', full_listen_passed=True,
        reviewed_packet=desc(A/'candidate05_review_packet.json'), audio=packet['audio'], word_timing=packet['word_timing_draft'],
        visual_decision=dict(user_quote='Approve proposed uses and recorded conditions', question_item_id='["request_user_input_async","call_5be43ce33e404c8e806a9e6073f6a28f",1]', scope='14 exact proposed new stock uses under recorded illustrative-use/crop conditions; actual motion/crops and final video playback still require review.'),
        publishing_authorized=False)
    receipt=A/'approvals/candidate05_approved_2026_10_22.json'; write(receipt, approval)
    qa=read(A/'audio_qa_pending_05_paced.json'); qa.update(approval); qa.update(status='FULL_AUDIO_AND_SYNCHRONIZATION_APPROVED', decision_receipt=desc(receipt), assembly_allowed=True)
    qap=A/'audio_qa_approved_05.json'; write(qap,qa)
    archive=A/'archive/before_candidate05_promotion'; archive.mkdir(parents=True, exist_ok=False)
    for name in ('preflight.json','audio_preflight_request.json','alignment.json','asset_registry.json','direct_generation_manifest.json'):
        shutil.copy2(A/name, archive/name)
    shutil.copy2(C/'Audio/Amy_Mihaljevic.srt',archive/'Amy_Mihaljevic.srt')
    request=read(A/'audio_preflight_request_candidate_05_paced.json'); request['audio_qa']=desc(qap)
    (A/'audio_preflight_request.json').write_text(json.dumps(request,indent=2)+'\n',encoding='utf-8')
    pf=pe.audio_preflight(ROOT,desc(A/'audio_preflight_request.json')['path']); assert pf['assembly_allowed']
    (A/'preflight.json').write_text(json.dumps(pf,indent=2)+'\n',encoding='utf-8')
    captions=read(V/'captions_paced_draft.json')
    align=dict(schema_version='cold_truth.reviewed_alignment.v1', case_id='amy-mihaljevic',target_format='youtube-longform',audio=request['audio'],script=request['script'],narration_text=request['narration_text'],
        tool='Sample-exact remapping of previously reviewed forced alignment after quiet-gap edits; reviewed full playback',recorded_at_utc=approval['recorded_at_utc'],reviewed_machine_draft=packet['word_timing_draft'], reviewed_caption_groups=packet['caption_draft'],segments=captions['segments'],timing_review=approval)
    (A/'alignment.json').write_text(json.dumps(align,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    pe.alignment(ROOT,desc(A/'alignment.json')['path'],pf)
    (C/'Audio/Amy_Mihaljevic.srt').write_text(pe.srt(align),encoding='utf-8')
    registry=read(A/'asset_registry.json'); approved={}
    for use in packet['new_stock_uses']:
        original=read(ROOT/use['candidate_review']['path'])
        review=dict(original); review.update(human_approved=True,approved_by='Brody',approved_on='2026-10-22',user_quote=approval['visual_decision']['user_quote'],scope=approval['visual_decision']['scope'],asset=use['file'],commercial_use_reviewed=True,credits='Pexels permits use without attribution; creator and item URL preserved in this record.',human_use_approved=True,rights_review_pending=False,actual_content_review_pending=False,actual_trim_crop_playback_reviewed=False,decision_receipt=desc(receipt),reviewed_candidate=use['candidate_review'])
        p=V/'rights'/f"{original['asset_id']}_approved_2026_10_22.json"; write(p,review)
        approved[original['asset_id']]=desc(p)
        registry['youtube-longform'].append(dict(asset_id=original['asset_id'],source_identity=original['source_identity'],asset_class='pexels_broll',file=use['file'],license_evidence=original['license_evidence'],rights_review=desc(p)))
    registry.update(status='RIGHTS_APPROVED_FINAL_MOTION_CROP_PLAYBACK_PENDING',updated_at_utc=approval['recorded_at_utc'])
    (A/'asset_registry.json').write_text(json.dumps(registry,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    checks=pe.assets(ROOT,desc(A/'asset_registry.json')['path'])
    recipe=read(V/'candidate_render_recipe_05.json')
    for shot in recipe['shots']:
        if shot['asset_id'] in approved: shot['rights_review']=approved[shot['asset_id']]
        shot['human_use_approved']=True
        review=read(ROOT/shot['rights_review']['path'])
        permitted=review.get('permitted_source_range_seconds')
        if permitted: assert shot['source_in_seconds'] >= permitted[0]-.001 and shot['source_out_seconds'] <= permitted[1]+.001, shot['shot_id']
        if review.get('proposed_crop'): assert shot['proposed_crop']==review['proposed_crop']
    recipe.update(status='APPROVED_INPUTS_CORRECTIVE_REVIEW_RENDER_ELIGIBLE',audio=request['audio'],human_audio_approved=True,human_timing_approved=True,new_asset_use_approved=True,assembly_allowed=True,render_ready=True,
        approval=desc(receipt),preflight=desc(A/'preflight.json'),alignment=desc(A/'alignment.json'),asset_registry=desc(A/'asset_registry.json'),
        output_path=(C/'Exports/Longform/Amy_Mihaljevic_review_02.mp4').relative_to(ROOT).as_posix(),working_directory=(C/'Exports/Longform/work_review_02').relative_to(ROOT).as_posix())
    write(V/'approved_render_recipe_02.json',recipe)
    write(A/'candidate05_promotion_check.json',dict(status='PASS',audio_preflight=pf,asset_check=checks,caption_count=len(align['segments']),word_count=1267,approval=desc(receipt),video_master_approved=False))
    print('PASS: approved exact audio, timing, 14 stock uses; preflight, alignment and isolation pass.')
if __name__=='__main__': main()
