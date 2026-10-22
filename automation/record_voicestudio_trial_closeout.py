"""Reconcile current vault navigation/state with the completed bounded trial."""
import datetime as dt
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
VAULT = ROOT / "Brody's Vault"
AUTO = VAULT / '2_IN_PRODUCTION/Amy Mihaljevic/Automation'
RESULT = AUTO / 'voicestudio_cpu_trial_result_2026_10_20.json'
result = json.loads(RESULT.read_text())
assert result['generation_requests_submitted'] == 2 and result['remaining_trial_attempts'] == 0
report_link = '[[0_ADMIN/VOICESTUDIO_CPU_TRIAL_2026_10_20|completed CPU voice trial]]'
approval_link = '[[2_IN_PRODUCTION/Amy Mihaljevic/Automation/approvals/voicestudio_cpu_trial_approval_2026_10_20.json|neutral-trial approval]]'
result_link = '[[2_IN_PRODUCTION/Amy Mihaljevic/Automation/voicestudio_cpu_trial_result_2026_10_20.json|measured trial receipt]]'
gib = result['storage']['unique_file_allocation_upper_bound_bytes'] / 1024**3

def edit(rel, before, after):
    path = VAULT / rel
    text = path.read_text(encoding='utf-8')
    assert before in text, (rel,before)
    path.write_text(text.replace(before,after),encoding='utf-8',newline='')

rows=[]
for sample in result['samples']:
    rows.append(f"| {sample['voice'].capitalize()} | `{sample['engine_voice_id']}` | {sample['duration_seconds']:.6f} s | {sample['wall_seconds']:.3f} s | {sample['sampled_peak_backend_tree_rss_bytes']/1024**2:.1f} MiB |")
report=f'''# VoiceStudio CPU trial — listening review

[[00_START_HERE|Home]] · [[0_ADMIN/PROJECT_DASHBOARD|Queue]] · [[0_ADMIN/VOICESTUDIO_EVALUATION_2026_10_20|Provider assessment]] · [[2_CHANNEL_SYSTEM/NARRATION_VOICE|Production voice history]]

**2026-10-20: two authorized neutral samples generated and technically verified; awaiting Brody's listening decision.** {approval_link} binds the unchanged proposal and the quote “Authorize this CPU voice trial.” {result_link} records requests, hashes, measurements and limits. This is an internal synthetic voice comparison, not Amy narration or production voice approval. Both trial attempts are used; no automatic retry occurred.

## Listen

[Bella sample](<C:/Youtube Automation Obsidian/voice_samples/voicestudio_trial_01/bella_01.wav>) · [Luna sample](<C:/Youtube Automation Obsidian/voice_samples/voicestudio_trial_01/luna_01.wav>)

Both are PCM 16-bit WAV, 24 kHz, mono, normal speed, with the same neutral 49-word text from the proposal. The output hashes differ. Technical checks do not establish pronunciation, completeness or creative quality.

| Voice | Actual preset ID | Audio duration | Request wall time | Sampled peak backend process-tree RSS |
|---|---|---|---|---|
{chr(10).join(rows)}

These two requests took longer than the resulting audio. Bella includes first model-load overhead; this small trial is not a sustained throughput benchmark. RAM figures sample the backend process tree every 250 ms and exclude installation/system memory.

The backend logged **phonemizer word-count mismatch warnings** during both requests. Listen through every sentence, especially “At eight fifteen in the morning,” and check missing or blurred words, pronunciation, calmness and natural pacing. No ASR or subjective listening approval was fabricated. Choose **Bella**, **Luna**, or **neither**; no further generation fits this exhausted grant.

## Verified installation and boundaries

- Stable [VoiceStudio Electron v0.5.6](https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.6), installed under `voice_samples/voicestudio_trial_01/app`. The 214,447,484-byte Windows installer matches SHA-256 `3d7ac1d6b54e7854ca7fff4dda838e402d1c5d31acc9656b1838432e29a97624` in both official release metadata and `SHA256SUMS.txt`.
- The release's bundled bootstrap selects CUDA on Windows. The private runtime instead preserves its frozen dependency versions with CPU PyTorch 2.8.0, torchaudio 2.8.0 and torchvision 0.23.0 wheels. Installed app/backend sources remain unchanged. This is a documented CPU runtime variant, not a claim that the stock GUI bootstrap supports this setup.
- Kitten adapter/library 0.8.1 loads **mini 0.8**, repository revision `c02725660cea441db4c383af69f1f26f5cd00947`. Config, weights and preset file total 81,547,388 bytes; including its model card, 81,548,122 bytes. Weight hashes and Git blob IDs were verified before loading. The model-card metadata says Apache-2.0; app/component notices are retained separately.
- Offline inspection of the exact installed adapter/model reports only `CPUExecutionProvider`, CPU-only torch, and both requested keys in the voice weights. Live `/health` reports 0.5.6/CPU; OpenAPI and actual engine catalog were captured. The post-generation catalog reports Kitten loaded/effective CPU but leaves its actual-provider field null; that field is not treated as independent provider proof.
- HF/Transformers offline flags stay enabled during validation/generation. No additional speech/ASR/AudioSeal weights were downloaded. The release-pinned Kitten phonemizer dependency chain includes packaged `en-core-web-sm` 3.8.0 NLP data (~12.2 MiB wheel); this is disclosed rather than called another TTS model. Component license metadata/notices are indexed in the trial folder. Production rights review remains open.
- Current directly attributable trial file allocation is conservatively estimated at **{gib:.3f} GiB**, counting hardlinks once and rounding files to 4 KiB, within the 10 GiB ceiling. An initial whole-drive guard stopped dependency installation; whole-drive free-space changes exceeded trial file sizes and include unattributed concurrent/system activity. The resumed install reused its cache with hardlinks and one download/install at a time. Historical whole-drive peak attribution cannot be certified; small installer registry/shortcut and directory metadata are excluded. See the receipt for raw readings and accounting limits.
- No paid service, cloud synthesis, cloning, Amy episode narration, visuals, rendering or publishing occurred. The historical ElevenLabs grant remains held and unused. Amy's exact reviewed script/outline/final binding still passes.

The stable installed backend was exercised through its local API. **The desktop GUI and its first-run settings were not validated.** `automation/start_voicestudio_cpu_trial.py` is a prepared, untested launcher using the supported backend-command override; it submits no generation. Do not use the stock CUDA bootstrap or treat the launcher as production certification.

## Next in the maintained plan

M5 remains in progress. Brody's listening decision comes next. Then bind an exact selected profile, component terms, a representative continuity check and episode narration request to new applicable scope. Preserve approved Amy wording; actual episode audio must still pass 480.000 seconds and full audio QA. Neutral sample duration cannot pass episode preflight. M6 and publishing keep their later scopes.
'''
(VAULT/'0_ADMIN/VOICESTUDIO_CPU_TRIAL_2026_10_20.md').write_text(report,encoding='utf-8')

state_path=VAULT/'0_ADMIN/COLD_TRUTH_EXECUTION_STATE.json'
state=json.loads(state_path.read_text())
state['operating_mode']='PROJECT_IMPLEMENTATION_LOCAL_CPU_VOICE_TRIAL_COMPLETE_AWAITING_LISTENING'
state['next_required_human_action']={'action':'LISTEN_AND_SELECT_BELLA_LUNA_OR_NEITHER','artifact':"Brody's Vault/0_ADMIN/VOICESTUDIO_CPU_TRIAL_2026_10_20.md",'reason':'Two neutral samples are technically verified. No selected replacement production voice or episode scope exists. Current trial grant is exhausted.','generation_attempts_submitted':2,'remaining_trial_attempts':0}
state['next_work']['action']='M5_HUMAN_LISTENING_THEN_EXACT_SELECTED_PROFILE_AND_NEW_APPLICABLE_PRODUCTION_SCOPE'
state['next_work']['entry_point']="Brody's Vault/0_ADMIN/VOICESTUDIO_CPU_TRIAL_2026_10_20.md"
state['local_voice_trial']={'status':result['status'],'approval':(AUTO/'approvals/voicestudio_cpu_trial_approval_2026_10_20.json').relative_to(ROOT).as_posix(),'result':RESULT.relative_to(ROOT).as_posix(),'generation_requests_submitted':2,'remaining_attempts':0,'automatic_retries':0,'episode_narration_authorized':False,'production_voice_selected':None,'assembly_allowed':False,'storage':result['storage']}
for item in state['execution_queue']:
    if item['id']=='M5':
        item['status']='in_progress_awaiting_local_voice_listening'
        item['trial_result']=RESULT.relative_to(ROOT).as_posix()
        item['trial_approval']=state['local_voice_trial']['approval']
state_path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')

edit('00_START_HERE.md','are next. Brody chose',f'now have a {report_link}: Bella and Luna await listening; both trial attempts are used. Brody chose')
edit('0_ADMIN/PROJECT_DASHBOARD.md','bounded local trial proposal]]; zero generation submissions',f'bounded local trial proposal]]; {report_link}, two neutral samples ready for listening; zero episode requests')
edit('0_ADMIN/PROJECT_DASHBOARD.md','All audio/media remain absent.','Episode audio/media remain absent; the separate neutral CPU trial now has two samples for listening.')
edit('0_ADMIN/PROJECT_DASHBOARD.md','No package installed. Work order remains M5.',f'VoiceStudio and its bounded CPU runtime/model trial are now installed; no memory backend was installed. See the {report_link}. Work order remains M5.')
edit('0_ADMIN/PROJECT_DASHBOARD.md','evaluate the bounded local voice trial before episode generation.','review the completed Bella/Luna trial samples before selecting an exact production voice and episode scope.')
edit('0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2.md','the next deliverable is a measured local voice trial and selected production profile','the local CPU trial is complete and awaits listening; the next deliverable is a selected production profile')
edit('0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2.md','Verify and run the bounded local voice trial under its applicable scope, select a replacement profile only after listening, then prepare the exact episode request.',f'The {report_link} has two authorized neutral outputs. Brody listens and chooses a voice or neither, then prepare an exact selected profile and new applicable episode/continuity-test scope. Trial attempts remaining: zero.')
edit('0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2.md',"VoiceStudio CPU evaluation is M5's next technical deliverable",f'The {report_link} is technically measured; listening/selection is the next M5 deliverable')
edit('0_ADMIN/PROJECT_MEMORY.md','It does not approve a new production voice. |',f'Brody separately authorized the {report_link}; its two samples await listening and its grant is exhausted. No production replacement is selected. |')
edit('0_ADMIN/VAULT_INDEX.md','- [[0_ADMIN/VOICESTUDIO_EVALUATION_2026_10_20|VoiceStudio assessment and bounded local trial]]',f'- [[0_ADMIN/VOICESTUDIO_EVALUATION_2026_10_20|VoiceStudio assessment and bounded local trial]]\n- {report_link}')
edit('2_CHANNEL_SYSTEM/NARRATION_VOICE.md','See the [[0_ADMIN/VOICESTUDIO_EVALUATION_2026_10_20|assessment and trial]];',f'See the {report_link}: Bella/Luna neutral clips await listening and both authorized attempts are used;')
edit('2_IN_PRODUCTION/PRODUCTION_HUB.md','the historical Mia attempt is held and the bounded local trial is next.',f'the historical Mia attempt is held and the {report_link} awaits Bella/Luna listening.')
edit('2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary.md','not approved; no request submitted.','not approved; zero episode requests submitted. Two separately authorized neutral trial samples exist for listening.')
edit('2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary.md','Hardware/documentation review complete; CPU Kitten mini 0.8 is the first candidate, not a selected production replacement',f'{report_link}: two neutral samples technically verified, awaiting listening; no production replacement selected')
summary=VAULT/'2_IN_PRODUCTION/Amy Mihaljevic/Production_Summary.md'
text=summary.read_text()
text=text[:text.index('**Next:**')]+f'**Next:** Brody listens to Bella and Luna in the {report_link}, choosing one or neither. {approval_link} authorized exactly the two completed neutral requests; no retries or additional requests remain. Then prepare an exact selected production profile and new applicable continuity-test/episode narration scope. No Amy audio runtime has been measured, and no episode preflight, alignment, visuals, Shorts or masters exist. The unused Mia grant remains held.\n'
summary.write_text(text,encoding='utf-8')
edit('2_IN_PRODUCTION/Amy Mihaljevic/Automation/Pilot_Runbook.md','before episode generation. The Mia-specific instructions',f'and {report_link} before episode generation. Its two neutral outputs await listening; the trial grant is exhausted. The Mia-specific instructions')
edit('0_ADMIN/GITHUB_TRENDING_REVIEW_2026_10_20.md','software installation, model download, memory-service integration and VoiceStudio quality are still unverified.',f'the {report_link} now verifies the installed local CPU API/model and two neutral outputs. Memory-service integration and VoiceStudio listening/production quality remain unverified.')
evaluation=VAULT/'0_ADMIN/VOICESTUDIO_EVALUATION_2026_10_20.md'
text=evaluation.read_text()
text=text.replace('**2026-10-20. Recommendation:',f'**Current execution result:** {report_link}: two authorized neutral samples await Brody listening; see actual measurements, warnings, installation variants and limits there. {approval_link} is separate from the held Mia grant. The assessment below preserves the pre-install findings.\n\n**2026-10-20. Recommendation:')
text=text.replace('No executable or checksum was downloaded or verified.','At the assessment checkpoint, no executable or checksum had been downloaded or verified; the completed-trial note above supersedes that installation status.')
text=text.replace('**Current result:** research/hardware review complete; local provider migration not yet validated; no software/model installation or generated media. M5 remains in progress. The immediate next technical deliverable is a measured local voice trial, followed by a selected exact production profile—not another general framework audit.',f'**Current result:** the {report_link} produced Bella and Luna neutral clips through the installed CPU API under the new trial grant. Software/model installation and technical sample measurements are recorded; listening and production replacement remain unapproved. M5 remains in progress. Next: listen, select or reject the voices, then bind an exact profile and new applicable generation scope.')
evaluation.write_text(text,encoding='utf-8')
canvas=VAULT/'00_WORKFLOW.canvas'
data=json.loads(canvas.read_text())
for node in data['nodes']:
    if 'text' in node:
        node['text']=node['text'].replace('zero generations.','two neutral CPU samples ready for listening; zero episode requests.').replace('zero\ngenerations.','two neutral CPU samples ready for listening; zero episode requests.')
canvas.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print('Current vault/state reconciled; trial result awaits listening. Historical approvals and reviewed scripts unchanged.')
