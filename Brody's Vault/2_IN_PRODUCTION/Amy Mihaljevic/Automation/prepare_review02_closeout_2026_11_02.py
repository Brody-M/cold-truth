"""Prepare navigation and an exact review request for the already rendered cut."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,html,json,re,shutil

A=Path(__file__).resolve().parent; C=A.parent; ROOT=A.parents[3]; V=ROOT/"Brody's Vault"
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def describe(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024**2),b''): h.update(block)
    return dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=h.hexdigest())
def write(p,obj): p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def note(p,text): p.write_text(text.strip()+'\n',encoding='utf-8')

def main():
    audit=read(A/'review02_export_audit_2026_11_02.json')
    assert audit['status']=='TECHNICAL_PASS_EXPORT_CONTACT_REVIEW_PENDING'
    review=C/'Exports/Longform/Review_Cut_02.md'; player=C/'Exports/Longform/Review_Cut_02.html'
    assert not review.exists() and not player.exists()
    stamp=datetime.now(timezone.utc).isoformat()
    video=ROOT/audit['video']['path']; audio=ROOT/audit['approved_audio']['path']
    recipe=read(C/'Visuals/Longform/revision_05/approved_render_recipe_02.json')
    words=read(C/'Audio/full_repair_05/remapped_word_timing_draft.json')
    captions=read(A/'alignment.json')
    short_packet=read(A/'shorts_audio_review_packet_01.json')
    # Verify the actual Shorts review inputs before offering them again.
    for entry in short_packet['entries']:
        for key in ('audio','preview','script','timing_draft'):
            assert describe(ROOT/entry[key]['path'])==entry[key]
    assert describe(ROOT/short_packet['review_player']['path'])==short_packet['review_player']
    rows=[]
    for p in words['paragraphs']:
        start=p['start']; label=f"{int(start)//60}:{int(start)%60:02} · Section {p['paragraph_id']}"
        rows.append(f'<button data-seek="{start}">{label}</button>')
    short_html=''.join(f'<section><h2>{e["id"]}. {html.escape(e["title"])}</h2><audio controls preload="none" src="../../{html.escape((ROOT/e["audio"]["path"]).relative_to(C).as_posix())}"></audio></section>' for e in short_packet['entries'])
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amy · review cut02</title><style>body{font:17px/1.5 system-ui;background:#10151c;color:#e9edf3;max-width:1080px;margin:auto;padding:24px}video{width:100%;background:#000}audio{width:100%}a{color:#8cc9ff}button{background:#222e3b;color:#fff;border:1px solid #526478;border-radius:6px;padding:8px;margin:4px;cursor:pointer}p{max-width:82ch}.notice{background:#233041;padding:14px;border-radius:8px}section{margin-top:24px}</style><h1>Amy Mihaljevic · corrective review02</h1><p class="notice">Full video playback decision pending. Approved audio/timing and stock-use decisions are already recorded. Watch visuals, motion/crops, captions, pacing, synchronization, audio and ending. Publishing is separate.</p><video id="cut" controls preload="metadata" src="Amy_Mihaljevic_review_02.mp4"></video><p><a href="Amy_Mihaljevic_review_02.mp4">Open the exact MP4</a> · <a href="../../Shorts/Audio_Review_01.html">Shorts synchronized word player</a></p><h2>Long-form sections</h2>'''+''.join(rows)+'''<p>Section buttons seek within the full video; they do not replace full playback. Volume is controlled by your player/device. No script changes or extra gain were applied to this export.</p><h2>Separate Shorts audio/timing review</h2><p>These three existing WAVs still need full listening and matching word-timing review before their Orbital videos. They are the unchanged October21 takes, not newly generated or newly approved audio.</p>'''+short_html+'''<script>const cut=document.getElementById('cut');document.querySelectorAll('[data-seek]').forEach(b=>b.addEventListener('click',()=>{cut.currentTime=Number(b.dataset.seek);cut.focus();}));</script></html>'''
    note(player,page)
    body='''# Amy — corrective video review02

[[00_START_HERE|Home]] · [[0_ADMIN/PROJECT_DASHBOARD|Dashboard]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/M6_Preparation_Handoff|Production handoff]] · [Open the full local player](Review_Cut_02.html)

**Verified November 2, 2026. Full video playback approval is pending.** The exact MP4 finished on October22. The full9:08.59 WAV, timing across19 sections and14new proposed stock uses were explicitly approved before this render. Those decisions remain preserved; this review is for the resulting video.

![Amy corrective review02](<'''+video.as_posix()+'''>)

[Open the exact MP4](<'''+video.as_posix()+'''>) · [Chapter player and separate Shorts audio](Review_Cut_02.html)

This version uses65shots from24stock sources, no full-screen cards, compact factual labels and131captions limited to two lines. Some source intervals repeat; their use is quantified in the recipe. Illustrative footage is labeled and is not presented as actual case evidence or locations. Stock sound is disabled; no music or new narration was added.

The export is1920×1080 with16,458frames. Container duration is9:08.63; the approved narration is9:08.59. Frame timestamp drift and AAC/WAV sample checks are recorded in the export audit. Measured encoded audio is−40.16LUFS/−27.80dBTP, matching the approved quiet treatment without a gain increase. These measurements do not replace your listening judgment.

Watch the entire cut and assess visuals, actual crop/motion, captions, pacing, audio, synchronization and ending. If something needs work, give a timestamp and describe it. Both authorized long-form render slots are consumed; no further render or publishing is implied by this review. The source check spoken in the episode remains October16; current source status must be rechecked before release.

[[2_IN_PRODUCTION/Amy Mihaljevic/Automation/longform_review_render_02.json|Actual render receipt and output hash]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/longform_review_02_qc.json|Decode and encoded-audio checks]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/review02_export_audit_2026_11_02.json|Independent export audit]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Visuals/Longform/revision_05/Visual_Review|Reviewed stock-use gallery]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Shorts/Audio_Review_01|Three separate Short audio/timing reviews]]
'''
    note(review,body)
    pending=dict(schema_version='cold_truth.exact_video_review_request.v1',prepared_at_utc=stamp,case_id='amy-mihaljevic',video=describe(video),approved_audio=describe(audio),review_note=describe(review),player=describe(player),render_receipt=describe(A/'longform_review_render_02.json'),export_audit=describe(A/'review02_export_audit_2026_11_02.json'),scope='Full exact-video playback: visuals, actual crops/motion,131captions, pacing, audio, synchronization and ending; publishing excluded.',human_full_playback_approved=False,remaining_longform_renders=0,shorts=dict(packet=describe(A/'shorts_audio_review_packet_01.json'),human_audio_and_timing_approved=False),new_generation_authorized=False,publishing_authorized=False)
    write(A/'pending_review02_playback_2026_11_02.json',pending)
    current='**Current — November 2, 2026:** M5 complete: exact9:08.59 repaired audio and timing approved. Corrective review02 is rendered and technically checked; full video playback review remains. Both long-form render slots are used. Three Short audio/timing decisions are pending. [[2_IN_PRODUCTION/Amy Mihaljevic/Exports/Longform/Review_Cut_02|Watch the current cut]]. No new paid calls or publishing.'
    navigation=['00_START_HERE.md','0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2.md','0_ADMIN/PROJECT_DASHBOARD.md','0_ADMIN/PROJECT_MEMORY.md','0_ADMIN/VAULT_INDEX.md','2_CHANNEL_SYSTEM/NARRATION_VOICE.md','2_IN_PRODUCTION/PRODUCTION_HUB.md','2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary.md','2_IN_PRODUCTION/Amy Mihaljevic/Automation/M6_Preparation_Handoff.md']
    for name in navigation:
        p=V/name; text=p.read_text(encoding='utf-8')
        text=re.sub(r'\*\*Current — October22,2026:\*\*[^\n]*\n*','',text)
        start=text.find('\n---\n',4)+5 if text.startswith('---\n') else 0
        text=text[:start]+'\n'+current+'\n\n'+text[start:]
        text=text.replace('**Updated:** 2026-10-21.','**Updated:** 2026-11-02.')
        note(p,text)
    # Update the maintained plan in place; retain its original ordering and historical assessments.
    p=V/'0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2.md'; text=p.read_text(encoding='utf-8')
    text=re.sub(r'\*\*Revision2\.1.*?\n', '**Revision2.1 · assessed2026-10-16 · updated2026-11-02 · owner: Brody · execution: Codex.** No fixed deadline; prioritize a reliable workflow. M1–M5 complete. M6: corrective review02 ready for full video playback; the three existing Short audios need audio/timing decisions before conditional Orbital video production. [[0_ADMIN/PROJECT_DASHBOARD|Live queue]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/M6_Preparation_Handoff|Actual media handoff]].\n',text)
    text=re.sub(r'\| Amy Mihaljevic \|.*?\n','| Amy Mihaljevic | Full repaired audio/timing and14new stock uses approved October22. Corrective cut02 completed and technically checked; full video playback and Short audio/timing reviews remain pending. No publishing. |\n',text)
    text=re.sub(r'\| M5 \|.*?\n','| M5 | Finish audio QA — Brody/Editor/operator | M3 + M4 + current narration scope | **Complete October22:** exact548.592358-second repaired/paced WAV and full synchronization explicitly approved; current preflight passes. No narration attempts remain. |\n',text)
    text=text.replace('**Current M6 pass:** bounded execution is authorized. First long-form cut and three Short audios are produced; collect actual media playback decisions, then use the existing grant for conditional Short video production.','**Current M6 pass:** corrective long-form cut02 and three Short audios exist. Collect full exact-video playback and Short audio/timing decisions, then use the existing conditional grant for Orbital Short videos. Both long-form render slots are used.')
    text=text.replace('**Production interval:** M6 preparation is authorized; later narration/assembly/render scope remains separate.','**Production interval:** the existing bounded production grant permits conditional Short renders after their exact audio/timing review. New narration and additional long-form renders are outside its remaining allowance.')
    note(p,text)
    p=V/'0_ADMIN/PROJECT_DASHBOARD.md'; text=p.read_text(encoding='utf-8')
    text=re.sub(r'\| M6 — visual tracks/masters \|.*?\n','| M6 — visual tracks/masters | Corrective cut02 ready for full human playback; Short audio/timing pending | [[2_IN_PRODUCTION/Amy Mihaljevic/Exports/Longform/Review_Cut_02|Current video]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Shorts/Audio_Review_01|Three Short audios]] |\n',text)
    text=re.sub(r'- Amy: review01.*?\n','- Amy: [[2_IN_PRODUCTION/Amy Mihaljevic/Exports/Longform/Review_Cut_02|corrective review02]] finished October22. Exact9:08.59 repaired audio/timing and14new stock uses are approved; full resulting-video playback and the three Short audio/timing reviews remain pending. No narration attempts or long-form render slots remain.\n',text)
    text=text.replace('actual review cuts and master playback remain incomplete','actual review cuts exist; full video master playback remains pending')
    text=text.replace('One long-form corrective render remains.','Both long-form render slots are used.')
    note(p,text)
    # Preserve older handoff and summary content as dated history, rather than mixing it with current directions.
    archive=A/'archive'; archive.mkdir(exist_ok=True)
    for source in [A/'M6_Preparation_Handoff.md',C/'Production_Summary.md']:
        old=archive/(source.stem+'_before_review02_closeout_2026_11_02.md')
        assert not old.exists(); shutil.copy2(source,old)
    note(A/'M6_Preparation_Handoff.md', '# Amy — current production handoff\n\n'+current+'''

[[00_START_HERE|Home]] · [[0_ADMIN/PROJECT_DASHBOARD|Queue]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary|Episode status]]

1. Watch the complete [[2_IN_PRODUCTION/Amy Mihaljevic/Exports/Longform/Review_Cut_02|corrective long-form cut02]]. The separate [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/candidate05_approved_2026_10_22.json|October22 receipt]] already approves the exact9:08.59 repaired audio, all19sections of timing and14new stock-use conditions. Do not ask for those decisions again. Actual video motion/crops, captions, audiovisual synchronization and overall playback are still unapproved.
2. Listen to all three [[2_IN_PRODUCTION/Amy Mihaljevic/Shorts/Audio_Review_01|existing Shorts]] and check their matching word-timing player. Actual pronunciation, completeness, volume and synchronization approval is missing. Each exact WAV/script/timing is bound in [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/shorts_audio_review_packet_01.json|the Short review packet]]. No new TTS is authorized or needed to review these files.
3. After actual Short approval, finalize each branch's exact QA/preflight/alignment, then make its separate Orbital-only video under the [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/phase_2_review_production_2026_10_21.json|existing conditional grant]]. Max2renders per Short,8total across four videos,5GiB new outputs. Both long-form slots are already consumed; no third long-form render is authorized.
4. After local master reviews, finish release packaging and recheck current source status. The episode explicitly dates its source check to October16. Publishing requires separate exact account/file/visibility/schedule authority.

The current video is1920×1080,16,458frames,9:08.63 container duration, with9:08.59 approved narration. It uses65shots/24stock sources,0full-screen cards,131two-line captions, no music and no stock sound. Exported audio is−40.16LUFS/−27.80dBTP; the full-decode pass and audio comparison are technical checks, not creative approval. Actual sample/crop findings and any remaining limits are recorded in the export audit and review request.

[[2_IN_PRODUCTION/Amy Mihaljevic/Automation/longform_review_render_02.json|Completed render/output hashes]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/review02_export_audit_2026_11_02.json|Independent export check]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/pending_review02_playback_2026_11_02.json|Exact pending playback request]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/Production_Update_05|Approved-input history]]

[[2_IN_PRODUCTION/Amy Mihaljevic/Automation/archive/M6_Preparation_Handoff_before_review02_closeout_2026_11_02|October production handoff history]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Visuals/Longform/Editorial_Visual_Brief|Original scope-bound visual brief]]. Historical grant hashes, provider holds and rejected cuts remain preserved. Do not rerun completed generation/render helpers on continuation.
''')
    note(C/'Production_Summary.md','# Amy Mihaljevic — production status\n\n'+current+'''

[[00_START_HERE|Home]] · [[0_ADMIN/PROJECT_DASHBOARD|Dashboard]] · [[0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2|Plan]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/M6_Preparation_Handoff|Current handoff]]

**Updated November2,2026. Format:** `youtube-longform`. **Current stage:** M6 — exact resulting-video playback and Short audio/timing review. **Editorial source boundary:** October16,2026; not a fresh November fact check.

| Artifact / decision | Current evidence |
|---|---|
| Research/viability | [[2_IN_PRODUCTION/Amy Mihaljevic/Research_Source_Ledger|Base ledger]] + [[2_IN_PRODUCTION/Amy Mihaljevic/Editorial/Source_Refresh_2026_10_16|October addendum]]; [[2_IN_PRODUCTION/Amy Mihaljevic/Editorial/Strategist_Viability_Assessment_v3|standard long-form viability v3]] |
| Paired script approval | [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/script_approval_2026_10_20.json|Exact full-draft/reverse-outline decision]] and unchanged [[2_IN_PRODUCTION/Amy Mihaljevic/Script_Final|final script]];1,267spoken words/19sections |
| Current narration/timing | [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/candidate05_approved_2026_10_22.json|Full9:08.59 repaired/paced WAV and synchronization approved October22]]; [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/preflight.json|passing exact-audio preflight]] and [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/alignment.json|131-cue current alignment]] |
| Visual use rights | [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/asset_registry.json|Bound registry]];14new stock uses approved with crop/illustrative conditions. Motion/crops in actual final playback remain pending. Long-form and Orbital tracks stay separate. |
| Current video | [[2_IN_PRODUCTION/Amy Mihaljevic/Exports/Longform/Review_Cut_02|Corrective cut02]], rendered October22;1,920×1,080/16,458frames,9:08.63 container duration. Full decode passed; exported audio retains approved quiet level. Human full-video approval pending. |
| Shorts | [[2_IN_PRODUCTION/Amy Mihaljevic/Shorts/Approved_Package|Three approved script/outline pairs]]; [[2_IN_PRODUCTION/Amy Mihaljevic/Shorts/Audio_Review_01|44.58/41.66/49.50-second audio and timing drafts]]; actual listening/timing decisions pending. No Short video rendered. |
| Remaining authority | [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/phase_2_review_production_2026_10_21.json|Existing bounded conditional Short video grant]]. Both long-form render slots used. All narration attempts exhausted. No paid services, new narration or publishing. |

Next: full exact-video playback review and the three separate Short audio/timing decisions, then eligible Short production under the saved grant. Technical checks cannot substitute for these human decisions.

[[2_IN_PRODUCTION/Amy Mihaljevic/Automation/archive/Production_Summary_before_review02_closeout_2026_11_02|Historical source/editorial/voice-trial/production detail]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/Production_Update_05|Repair and approvals history]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Exports/Longform/Review_Cut_01|Rejected review01]]. Historical cost balances are dated snapshots, not live provider/account balances.
''')
    # Bring only current state descriptors forward; historical receipts and approved packets stay unchanged.
    statep=V/'0_ADMIN/COLD_TRUTH_EXECUTION_STATE.json'; state=read(statep)
    state.update(updated_at='2026-11-02',operating_mode='M6_REVIEW02_COMPLETE_HUMAN_VIDEO_AND_SHORT_AUDIO_REVIEW_PENDING',next_required_human_action='FULL_REVIEW02_VIDEO_PLAYBACK_AND_THREE_SHORT_AUDIO_TIMING_DECISIONS')
    state['next_work'].update(milestone_id='M6',action='REVIEW_EXACT_VIDEO02_AND_SHORT_AUDIO_TIMING_THEN_CONDITIONAL_SHORT_VIDEOS',entry_point=review.relative_to(ROOT).as_posix())
    state['review02_current'].update(video=describe(video),review_note=describe(review),review_request=describe(A/'pending_review02_playback_2026_11_02.json'),export_audit=describe(A/'review02_export_audit_2026_11_02.json'),human_master_approved=False,remaining_longform_render_attempts=0)
    state['active_editorial_case']['production_authority_scope']='LONGFORM_RENDER_BUDGET_EXHAUSTED_SHORT_RENDERS_CONDITIONAL_ON_ACTUAL_AUDIO_TIMING_APPROVAL'
    state['episode_audio']['full_listen_passed']=True
    state['m6_preparation'].update(status='REVIEW02_COMPLETE_VIDEO_PLAYBACK_AND_SHORT_AUDIO_TIMING_PENDING',human_video_master_approved=False)
    for item in state['execution_queue']:
        if item['id']=='M6': item['status']='review02_complete_human_video_and_short_audio_timing_pending'
    def current_bindings(value):
        if isinstance(value,dict):
            if {'path','sha256','bytes'}==set(value) and value['path'] in [(A/name).relative_to(ROOT).as_posix() for name in ['preflight.json','asset_registry.json','alignment.json']]: value.update(describe(ROOT/value['path']))
            else:
                for key,child in value.items():
                    if not ('historical' in key or key.startswith('archive')): current_bindings(child)
        elif isinstance(value,list):
            for child in value: current_bindings(child)
    current_bindings(state['m6_preparation'])
    # Existing top-level live counters must agree with completed review02.
    def counters(value):
        if isinstance(value,dict):
            for key,child in value.items():
                if key=='review_renders_consumed' and isinstance(child,dict):
                    for track in child:
                        if 'longform' in track.lower() or 'long_form' in track.lower(): child[track]=2
                elif key in ('remaining_longform_renders','remaining_longform_render_attempts'): value[key]=0
                elif not ('historical' in key or key.startswith('archive')): counters(child)
        elif isinstance(value,list):
            for child in value: counters(child)
    counters(state); write(statep,state)
    arp=A/'asset_readiness.json'; readiness=read(arp); archived= A/'archive/asset_readiness_before_review02_closeout_2026_11_02.json'; shutil.copy2(arp,archived)
    readiness.update(status='LONGFORM_LOCAL_REVIEW02_READY_FULL_VIDEO_PLAYBACK_PENDING',registry=describe(A/'asset_registry.json'),audio_preflight=describe(A/'preflight.json'),alignment=describe(A/'alignment.json'),assembly_authorized=False,render_authorized=False,render_budget_remaining_longform=0,conditional_short_render_authority_preserved=True,visual_timeline_ready=True,human_master_playback_approved=False,remaining=['Full exact-video motion/crop/caption/audio/synchronization/ending review','Three actual Short audio/timing decisions before conditional Orbital video production','Current-source recheck and release packaging after local master reviews; separate publishing authority'],previous_preparation_snapshot=describe(archived))
    current_bindings(readiness); write(arp,readiness)
    # Keep old prep counts explicitly historical rather than falsely calling them totals.
    for key in ['pexels_downloads','pexels_decode_passes','pexels_1080p','pexels_editorial_candidates','pexels_excluded','case_cards','new_media_bytes','new_media_ceiling_bytes']:
        if key in readiness: del readiness[key]
    readiness.update(current_recipe_stock_sources=24,current_recipe_fullscreen_cards=0,current_registry_longform_assets=len(read(A/'asset_registry.json')['youtube-longform']),case_bytes=sum(p.stat().st_size for p in C.rglob('*') if p.is_file()))
    write(arp,readiness)
    # Update short historical statements in live shelves, leaving all exact approval records untouched.
    p=V/'2_IN_PRODUCTION/PRODUCTION_HUB.md'; text=p.read_text(encoding='utf-8'); text=text.replace('One long-form corrective render remains.','Both long-form render slots are used.'); note(p,text)
    p=V/'2_CHANNEL_SYSTEM/NARRATION_VOICE.md'; text=p.read_text(encoding='utf-8'); text=re.sub(r'\*\*M6 execution update:\*\*[^\n]*','**M6 execution update:** [[2_IN_PRODUCTION/Amy Mihaljevic/Exports/Longform/Review_Cut_02|Corrective review02]] uses the approved9:08.59 repaired audio. Full video playback and the three separate Short audio/timing reviews remain pending. All narration attempts and both long-form render slots are used; conditional Short video authority remains. No paid calls or publishing.',text); text=text.replace('## Current direction — 2026-10-21','## Historical direction — 2026-10-21'); note(p,text)
    p=ROOT/'AGENTS.md'; text=p.read_text(encoding='utf-8'); text=text.replace('## Current project entry points — 2026-09-05','## Current project entry points — 2026-11-02'); text=re.sub(r'- Amy current status:[^\n]*','- Amy current status: full9:08.59 repaired audio and synchronization and14new stock uses approved October22. Corrective review02 is complete/decoded and ready for full human video playback. Both long-form render slots are consumed. Read Exports/Longform/Review_Cut_02.md and Automation/M6_Preparation_Handoff.md. Three Short audio/timing decisions remain pending before conditional Orbital videos under the existing grant. No new narration, paid calls or publishing. Preserve historical approvals/provider holds.',text); note(p,text)
    print('Prepared exact video/Short review page, maintained plan/handoff and current machine state; no human playback decision inferred.')

if __name__=='__main__': main()
