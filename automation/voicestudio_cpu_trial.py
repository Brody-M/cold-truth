"""One-shot neutral sample requests; this is not an episode production adapter."""
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'voice_samples/voicestudio_trial_01'
AUTO = ROOT / "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation"

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

alias = sys.argv[1].lower()
assert alias in ('bella', 'luna')
proposal_path = AUTO / 'voicestudio_trial_proposal.json'
proposal = json.loads(proposal_path.read_text(encoding='utf-8'))
approval = json.loads((AUTO / 'approvals/voicestudio_cpu_trial_approval_2026_10_20.json').read_text())
assert approval['human_decision_quote'] == 'Authorize this CPU voice trial'
assert approval['proposal']['sha256'] == hashlib.sha256(proposal_path.read_bytes()).hexdigest()
assert proposal['maximum_test_generations'] == 2
assert not proposal['input_is_approved_episode_text']
inspection = json.loads((TRIAL / 'engine_inspection_stdout.txt').read_text())
assert inspection['onnx_providers'] == ['CPUExecutionProvider']
assert inspection['torch'] == '2.8.0+cpu'
voice = next(v['engine_id'] for v in proposal['candidate_voices'] if v['alias'].lower() == alias)
assert voice in inspection['preset_voices'] and voice in inspection['weight_voice_keys']
assert inspection['aliases'][alias.capitalize()] == voice
openapi = json.loads((TRIAL / 'openapi.json').read_text())
assert '/v1/audio/speech' in openapi['paths']
catalog = json.loads((TRIAL / 'voices.json').read_text())
kitten = next(b for b in catalog['engines'] if b['id'] == 'kittentts')
assert kitten['available'] is True
with urllib.request.urlopen('http://127.0.0.1:3900/health', timeout=15) as response:
    health = json.load(response)
assert health['version'] == '0.5.6'

attempt_path = TRIAL / f'{alias}_attempt.json'
output = TRIAL / f'{alias}_01.wav'
assert not output.exists() and not attempt_path.exists(), 'No generation retry or overwrite permitted'
assert len(list(TRIAL.glob('*_attempt.json'))) < 2, 'Trial generation cap exhausted'
payload = {'model': 'kittentts', 'voice': voice, 'input': proposal['test_text'], 'response_format': 'wav', 'speed': 1.0, 'language': 'en'}
attempt = {
    'schema_version': 'cold_truth.neutral_voice_trial_attempt.v1',
    'started_at_utc': now(), 'status': 'SUBMISSION_STARTED_NO_AUTOMATIC_RETRY',
    'approval_path': str(AUTO / 'approvals/voicestudio_cpu_trial_approval_2026_10_20.json'),
    'endpoint': 'http://127.0.0.1:3900/v1/audio/speech', 'request': payload,
    'input_sha256': hashlib.sha256(payload['input'].encode()).hexdigest(),
    'output_path': str(output), 'classification': 'AI_GENERATED_NEUTRAL_INTERNAL_TRIAL',
    'target_format': 'youtube-longform', 'is_episode_narration': False, 'assembly_allowed': False,
    'engine_inspection': str(TRIAL / 'engine_inspection_stdout.txt'),
    'model_revision': 'c02725660cea441db4c383af69f1f26f5cd00947',
    'generation_retry_allowed': False,
}
# Exclusive write records the submission boundary before any POST is made.
with attempt_path.open('x', encoding='utf-8') as target:
    json.dump(attempt, target, indent=2)
outcome = {}
def request_once():
    try:
        request = urllib.request.Request(attempt['endpoint'], data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(request, timeout=600) as response:
            content = response.read()
            outcome.update(http_status=response.status, headers=dict(response.headers))
        assert content[:4] == b'RIFF' and content[8:12] == b'WAVE', 'Response is not a WAV'
        with output.open('xb') as target:
            target.write(content)
        outcome['bytes'] = len(content)
    except urllib.error.HTTPError as error:
        error_path = TRIAL / f'{alias}_http_error.txt'
        error_path.write_bytes(error.read())
        outcome.update(error=f'HTTP {error.code}', error_body_path=str(error_path))
    except Exception as error:
        outcome['error'] = repr(error)

try:
    import psutil
except ImportError:
    psutil = None
backend_pid = json.loads((TRIAL / 'backend_launch.json').read_text())['pid']
peak_rss = 0
started = time.monotonic()
worker = threading.Thread(target=request_once, daemon=True)
worker.start()
while worker.is_alive():
    if psutil:
        try:
            parent = psutil.Process(backend_pid)
            rss = sum(p.memory_info().rss for p in [parent, *parent.children(recursive=True)] if p.is_running())
            peak_rss = max(peak_rss, rss)
        except psutil.Error:
            pass
    worker.join(0.25)
attempt.update(completed_at_utc=now(), wall_seconds=round(time.monotonic()-started, 3), response=outcome, sampled_peak_backend_tree_rss_bytes=peak_rss or None, memory_sampling_interval_seconds=0.25)
attempt['status'] = 'FAILED_NO_RETRY' if 'error' in outcome else 'WAV_RECEIVED_PENDING_PROBE'
save(attempt_path, attempt)
if 'error' in outcome:
    print(json.dumps(attempt, indent=2))
    raise SystemExit(1)
probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=codec_name,sample_rate,channels,duration:format=duration', '-of', 'json', str(output)], capture_output=True, text=True, check=True)
metadata = json.loads(probe.stdout)
stream = metadata['streams'][0]
assert int(stream['sample_rate']) == 24000 and stream['channels'] == 1
attempt.update(status='TECHNICALLY_VERIFIED_AWAITING_HUMAN_LISTENING', audio_probe=metadata, output_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
save(attempt_path, attempt)
print(json.dumps({'voice':voice, 'path':str(output), 'probe':metadata, 'wall_seconds':attempt['wall_seconds'], 'peak_backend_tree_rss_bytes':peak_rss, 'sha256':attempt['output_sha256']}, indent=2))
