"""Reconcile navigation and machine state with approved candidate05 and actual render status."""
from pathlib import Path
from datetime import datetime,timezone
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[4]; VAULT=ROOT/"Brody's Vault"; A=Path(__file__).resolve().parent; C=A.parent
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def desc(p): return dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def write(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
    render=read(A/'longform_review_render_02.json') if (A/'longform_review_render_02.json').exists() else {'status':'NOT_STARTED'}
    done=render['status']=='REVIEW_CUT_RENDERED_TECHNICAL_PASS_HUMAN_PLAYBACK_PENDING'
    phase='Corrective review02 rendered and decoded; full human video playback pending.' if done else 'Corrective review02 is '+render['status']+'; check the live render receipt before resuming. No automatic retry.'
    link='2_IN_PRODUCTION/Amy Mihaljevic/Automation/Production_Update_05'
    block=f'**Current — October22,2026:** Full9:08.59 repaired/paced audio and synchronization explicitly approved;14new stock uses approved under recorded conditions. Exact-audio preflight passes. {phase} Shorts still need actual audio/timing approval. No paid calls or publishing. See [[{link}|current production evidence and next steps]].'
    note=A/'Production_Update_05.md'
    note.write_text('# Amy — approved audio and corrective production05\n\n'+block+'\n\n[[00_START_HERE|Home]] · [[0_ADMIN/PROJECT_DASHBOARD|Dashboard]] · [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/M6_Preparation_Handoff|Handoff]]\n\nBrody approved the full exact WAV, pronunciation, completeness, volume including “disappeared,” pacing, ending and synchronization across all19 paragraphs: “Listened fully; approve audio and synchronization.” He separately approved the14new proposed stock uses: “Approve proposed uses and recorded conditions.” Both replies bind the immutable [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/candidate05_review_packet.json|review packet]] in the [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/candidate05_approved_2026_10_22.json|approval receipt]].\n\nThe [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/Review_Package_05|review package]] links the exact audio/player and [[2_IN_PRODUCTION/Amy Mihaljevic/Visuals/Longform/revision_05/Visual_Review|visual gallery]]. The [[2_IN_PRODUCTION/Amy Mihaljevic/Audio/full_repair_05/Full_Repair_05_Report|audio processing report]] preserves the sample-level evidence. The packet and those reviewed files remain unchanged; their old pending labels are historical snapshots superseded by the separate receipt.\n\nThe [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/preflight.json|current preflight]], [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/alignment.json|131-cue reviewed alignment]] and [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/asset_registry.json|rights/isolation registry]] bind current files. Previous canonical bytes are retained in Automation/archive/before_candidate05_promotion. Script and narration words are unchanged.\n\nThe [[2_IN_PRODUCTION/Amy Mihaljevic/Visuals/Longform/revision_05/approved_render_recipe_02.json|corrective recipe]] has65shots,24stock sources, no full-screen cards, compact factual labels and captions limited to two lines. Some stock source intervals repeat; the recipe quantifies them. This consumes the second and final authorized long-form review render; component encodes belong to that single cut. The [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/longform_review_render_02.json|live render receipt]] records every command/output and actual completion or failure.\n\n'+phase+'\n\nNext: inspect actual output motion/crops, captions, audio, ending and technical checks, then obtain full human video-playback approval. Both long-form render slots are consumed once review02 starts. Publishing remains separately unauthorized. The three [[2_IN_PRODUCTION/Amy Mihaljevic/Shorts/Audio_Review_01|Short audio/timing reviews]] remain pending; no Short video render or new narration is inferred. Recheck current case-source status before release; last editorial source refresh was October16.\n\nGitHub sync includes versioned notes, helpers and receipts; media, installed runtimes, credentials and editor caches stay excluded by .gitignore. The local vault remains necessary for actual media playback.\n',encoding='utf-8')
    paths=['00_START_HERE.md','0_ADMIN/PROJECT_DASHBOARD.md','0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2.md','0_ADMIN/PROJECT_MEMORY.md','0_ADMIN/VAULT_INDEX.md','2_CHANNEL_SYSTEM/NARRATION_VOICE.md','2_IN_PRODUCTION/PRODUCTION_HUB.md','2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary.md','2_IN_PRODUCTION/Amy Mihaljevic/Automation/M6_Preparation_Handoff.md']
    for name in paths:
        p=VAULT/name; s=p.read_text(encoding='utf-8')
        s=re.sub(r'\*\*Current audio reassessment04, 2026-10-21:\*\*.*?(?:\n\n|\Z)','',s,flags=re.S)
        s=re.sub(r'\*\*Current — October22,2026:\*\*.*?(?:\n\n|\Z)','',s,flags=re.S)
        s=s.replace('| M5 — narration | Reopened for delivery/level correction | Earlier9:30.56 approval is historical; correction03 rejected. Targeted onset/breath diagnostic04 ready for listening; no TTS attempts remain. |','| M5 — narration | Complete: exact repaired9:08.59 audio/timing approved | [[2_IN_PRODUCTION/Amy Mihaljevic/Automation/Production_Update_05|Approval and passing preflight]]; no TTS attempts remain. |')
        # Older detailed entries remain explicitly historical after the dated current block.
        offset=s.find('\n---\n',4)+5 if s.startswith('---\n') else 0
        s=s[:offset]+'\n'+block+'\n\n'+s[offset:]
        s=re.sub(r'\*\*As of 2026-10-21:\*\*.*?\n\n','**October21 history:** Earlier audio/video revisions were rejected; the current October22 decision above supersedes their pending gates.\n\n',s,flags=re.S)
        s=s.replace('**Current milestone:** M5 — precise word-onset/breath diagnosis; M6 video correction waits for accepted audio.','**Current milestone:** M6 — corrective review02 production and actual video playback review.')
        s=s.replace('On “continue,” finish the Editor\'s targeted pop repair and several-dB reduction, then review that candidate and prepare more relevant B-roll coverage before the remaining long-form render.','On “continue,” inspect the live review02 receipt and finish actual technical/video playback review; do not restart or duplicate its render.')
        p.write_text(s,encoding='utf-8')
    agents=ROOT/'AGENTS.md'; s=agents.read_text(encoding='utf-8'); s=re.sub(r'- Amy’s original processed.*?\n', '- Amy current status: full9:08.59 repaired/paced audio and synchronization explicitly approved October22;14new stock uses approved with conditions. Exact preflight/alignment/assets pass. Corrective review02 uses the final long-form render slot; inspect Automation/Production_Update_05.md and the live receipt. No new narration or publishing; Shorts actual audio/timing review remains pending. Preserve historical approvals and provider holds.\n',s); agents.write_text(s,encoding='utf-8')
    statep=VAULT/'0_ADMIN/COLD_TRUTH_EXECUTION_STATE.json'; state=read(statep)
    state.update(updated_at='2026-10-22',operating_mode='M6_CORRECTIVE_REVIEW02_'+('HUMAN_PLAYBACK_PENDING' if done else 'IN_PROGRESS'))
    state['next_work'].update(milestone_id='M6',action='INSPECT_REVIEW02_RECEIPT_THEN_TECHNICAL_AND_HUMAN_VIDEO_REVIEW',entry_point=note.relative_to(ROOT).as_posix())
    state['active_editorial_case']['status']='AUDIO_TIMING_AND_STOCK_USES_APPROVED_VIDEO_MASTER_PENDING'
    ea=state['episode_audio']
    if 'historical_before_candidate05' not in ea:
        ea['historical_before_candidate05']= {k:ea[k] for k in ('master','preflight','audio_qa') if k in ea}
    ea.update(status='REPAIRED_PACED_FULL_AUDIO_APPROVED',master=read(A/'candidate05_review_packet.json')['audio'],preflight=desc(A/'preflight.json'),audio_qa=desc(A/'audio_qa_approved_05.json'),duration_seconds=548.592358276644)
    state['m6_preparation'].update(status='CORRECTIVE_REVIEW02_'+render['status'],alignment=desc(A/'alignment.json'),asset_registry=desc(A/'asset_registry.json'),new_stock_use_approval=desc(A/'approvals/candidate05_approved_2026_10_22.json'),human_video_master_approved=False)
    for item in state['execution_queue']:
        if item['id']=='M5': item['status']='complete_exact_repaired_audio_and_timing_approved'
        if item['id']=='M6': item['status']='corrective_review02_'+render['status'].lower()
    state['review02_current']=dict(status=render['status'],receipt=(A/'longform_review_render_02.json').relative_to(ROOT).as_posix(),human_master_approved=False,remaining_longform_render_attempts=0)
    write(statep,state)
    arp=A/'asset_readiness.json'; ar=read(arp); ar.update(status='CURRENT_AUDIO_AND_ASSET_USES_APPROVED_REVIEW02_VIDEO_PLAYBACK_PENDING',current_approval=desc(A/'approvals/candidate05_approved_2026_10_22.json'),current_preflight=desc(A/'preflight.json'),human_master_playback_approved=False); write(arp,ar)
    canvasp=VAULT/'00_WORKFLOW.canvas'; canvas=read(canvasp)
    for node in canvas['nodes']:
        if node.get('type')=='text' and ('M5' in node.get('text','') or 'diagnostic04' in node.get('text','')): node['text']='M5 complete: exact9:08.59 audio/timing approved. M6: corrective review02; actual final video playback pending. No publishing.'
    write(canvasp,canvas)
    manifestp=A/'direct_generation_manifest.json'; manifest=read(manifestp); eventid='amy-no-cost-repair-broll-and-corrective-review02-2026-10-22'
    files=set()
    for folder in (C/'Audio/full_repair_05',C/'Visuals/Longform/revision_05',C/'Exports/Longform/work_review_02'):
        if folder.exists(): files.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in str(p))
    files.update((C/'Visuals/Longform/assets').glob('*revision05*'))
    for p in A.glob('*'):
        if p.is_file() and ('05' in p.name or '02' in p.name or 'no_cost' in p.name): files.add(p)
    files.update((A/'approvals').glob('*05*'))
    if (C/'Exports/Longform/Amy_Mihaljevic_review_02.mp4').exists(): files.add(C/'Exports/Longform/Amy_Mihaljevic_review_02.mp4')
    event=dict(event_id=eventid,recorded_at_utc=datetime.now(timezone.utc).isoformat(),tool='Installed Python, FFmpeg/FFprobe8.1.1; free Pexels file acquisition; no paid provider',settings=dict(voice_generation=False,audio='Existing take local clip-gain and quiet-gap edits',render_attempt=2,new_provider_calls=0,publishing=False),authority=desc(A/'approvals/candidate05_approved_2026_10_22.json'),render_status=render['status'],output_paths=[p.relative_to(ROOT).as_posix() for p in sorted(files)],outputs=[desc(p) for p in sorted(files)],note='Render outputs may be incomplete while IN_PROGRESS; live render receipt is authoritative, update this inventory after completion.')
    manifest['entries']=[e for e in manifest['entries'] if e.get('event_id')!=eventid]+[event]; write(manifestp,manifest)
    print(json.dumps(dict(render=render['status'],manifest_output_count=len(files),case_bytes=sum(p.stat().st_size for p in C.rglob('*') if p.is_file()))))
if __name__=='__main__': main()
