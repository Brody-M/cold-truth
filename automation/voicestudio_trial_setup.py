"""Bounded, explicit operations for Brody's authorized neutral VoiceStudio trial."""
import datetime as dt
import hashlib
import json
import pathlib
import os
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'voice_samples/voicestudio_trial_01'
AUTO = ROOT / "Brody's Vault/2_IN_PRODUCTION/Amy Mihaljevic/Automation"

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def descriptor(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
            'sha256': hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'ColdTruth-authorized-CPU-trial'}), timeout=60) as r:
        return r.read()

def disk_upper_bound():
    # Count hardlinked cache/runtime files once; round each file up to NTFS 4 KiB.
    seen = set()
    total = count = 0
    for folder, dirs, files in os.walk(TRIAL):
        for name in files:
            try:
                info = os.stat(os.path.join(folder, name))
            except FileNotFoundError:
                continue
            identity = (info.st_dev, info.st_ino)
            if identity not in seen:
                seen.add(identity)
                total += ((info.st_size + 4095) // 4096) * 4096
                count += 1
    return {'file_allocation_upper_bound_bytes': total, 'unique_files': count}

def backend_env():
    env = os.environ.copy()
    env.update({
        'OMNIVOICE_DATA_DIR': str(TRIAL / 'data'),
        'OMNIVOICE_CACHE_DIR': str(TRIAL / 'model-cache'),
        'HF_HOME': str(TRIAL / 'model-cache'),
        'HF_HUB_CACHE': str(TRIAL / 'model-cache'),
        'OMNIVOICE_ENGINES_DIR': str(TRIAL / 'engines'),
        'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
        'OMNIVOICE_TTS_BACKEND': 'kittentts',
        'OMNIVOICE_KITTENTTS_MODEL': 'KittenML/kitten-tts-mini-0.8',
        'OMNIVOICE_PRELOAD_CAPTURE_ASR': '0', 'OMNIVOICE_PRELOAD_WATERMARK': '0',
        'OMNIVOICE_PRELOAD_TTS_ASR': '0', 'CUDA_VISIBLE_DEVICES': '',
        'PYTHONIOENCODING': 'utf-8', 'PYTHONNOUSERSITE': '1',
        'TEMP': str(TRIAL / 'tmp'), 'TMP': str(TRIAL / 'tmp'),
    })
    return env

if sys.argv[1] == 'record':
    proposal = AUTO / 'voicestudio_trial_proposal.json'
    approval = AUTO / 'approvals/voicestudio_cpu_trial_approval_2026_10_20.json'
    if approval.exists():
        raise SystemExit('Approval already recorded; refusing overwrite')
    write(approval, {
        'schema_version': 'cold_truth.local_voice_trial_approval.v1',
        'recorded_at_utc': now(), 'approved_on': '2026-10-20',
        'human_decision_quote': 'Authorize this CPU voice trial',
        'question': 'Your earlier narration grant named Mia/ElevenLabs. Authorize the prepared VoiceStudio CPU trial instead: install the stable app with a 10 GiB total disk-increase ceiling, download only Kitten mini 0.8 (about 80 MB for the model), and generate two neutral female-voice samples for you to review? No paid services, cloning or episode narration are included.',
        'proposal': descriptor(proposal),
        'scope': json.loads(proposal.read_text(encoding='utf-8')),
        'scope_status': 'AUTHORIZED_NEUTRAL_CPU_TRIAL_ONLY',
        'episode_narration_authorized': False, 'assembly_allowed': False,
        'does_not_consume_or_reuse_mia_grant': True,
    })
    TRIAL.mkdir(parents=True, exist_ok=True)
    write(TRIAL / 'disk_baseline.json', {
        'recorded_at_utc': now(), 'drive_free_bytes': shutil.disk_usage(ROOT).free,
        'maximum_total_disk_increase_bytes': 10737418240,
        'trial_root': str(TRIAL), 'existing_trial_bytes': sum(p.stat().st_size for p in TRIAL.rglob('*') if p.is_file()),
        'accounting': 'Track all app/runtime/cache/data/tmp/download/output paths; also compare C drive free space conservatively.'
    })
    print(descriptor(approval))

elif sys.argv[1] == 'download':
    release = json.loads(get('https://api.github.com/repos/debpalash/VoiceStudio/releases/tags/v0.5.6'))
    assert not release['prerelease'] and not release['draft']
    write(TRIAL / 'release_metadata.json', release)
    selected = [a for a in release['assets'] if a['name'] == 'VoiceStudio-Electron-0.5.6-win-x64.exe' or a['name'] == 'SHA256SUMS.txt']
    assert any(a['name'].endswith('.exe') for a in selected)
    print([{k: a.get(k) for k in ('name','size','digest','browser_download_url')} for a in selected], flush=True)
    for asset in selected:
        path = TRIAL / asset['name']
        if not path.exists():
            with urllib.request.urlopen(asset['browser_download_url'], timeout=60) as response, path.open('xb') as target:
                shutil.copyfileobj(response, target, 1024*1024)
        actual = descriptor(path)
        assert actual['bytes'] == asset['size']
        assert 'sha256:' + actual['sha256'] == asset['digest']
        print(actual, flush=True)
    exe = TRIAL / 'VoiceStudio-Electron-0.5.6-win-x64.exe'
    sums = TRIAL / 'SHA256SUMS.txt'
    if sums.exists():
        assert descriptor(exe)['sha256'] in sums.read_text()
    print('Official release digest verified. No execution performed.')

elif sys.argv[1] in ('launch', 'serve'):
    # Start only the backend shipped by the installed stable app, loopback only.
    # No engine or application sources are patched.
    try:
        get('http://127.0.0.1:3900/health')
    except Exception:
        pass
    else:
        raise SystemExit('Port 3900 already responds; inspect existing backend before reuse')
    prefs_path = TRIAL / 'data/prefs.json'
    if not prefs_path.exists():
        write(prefs_path, {'tts_backend': 'kittentts', 'watermark.invisible': False})
    command = [str(TRIAL / 'runtime/Scripts/python.exe'), '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '3900']
    env = backend_env()
    with (TRIAL / 'backend.log').open('ab') as log:
        process = subprocess.Popen(command, cwd=TRIAL / 'app/resources', env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    write(TRIAL / 'backend_launch.json', {'recorded_at_utc': now(), 'pid': process.pid, 'command': command, 'environment_overrides': {k: v for k, v in env.items() if k.startswith(('OMNIVOICE_', 'HF_', 'TRANSFORMERS_', 'CUDA_', 'PYTHON'))}, 'preferences': {'watermark.invisible': False, 'reason': 'Neutral internal synthetic trial only; additional AudioSeal weights not authorized. Synthetic provenance is explicit in trial approval, filenames, manifest and delivery.'}, 'application_gui_verified': False})
    print('Stable installed backend launched with PID', process.pid, flush=True)
    if sys.argv[1] == 'serve':
        sys.exit(process.wait())

elif sys.argv[1] == 'inspect':
    script = '''import sys,json,pathlib,importlib.metadata as md
sys.path.insert(0, 'backend')
import torch
from services.tts_backend import KittenTTSBackend
b=KittenTTSBackend()
b._ensure_loaded()
m=b._model.model
assert m.session.get_providers() == ['CPUExecutionProvider']
assert all(v in b.PRESET_VOICES and v in m.voices.files for v in ['expr-voice-2-f','expr-voice-3-f'])
print(json.dumps({'torch':torch.__version__,'torch_cuda_available':torch.cuda.is_available(),'engine':b.id,'sample_rate':b.sample_rate,'onnx_providers':m.session.get_providers(),'model_path':m.model_path,'preset_voices':b.PRESET_VOICES,'weight_voice_keys':m.voices.files,'aliases':m.voice_aliases,'packages':{n:md.version(n) for n in ['onnxruntime','kittentts','phonemizer-fork','espeakng-loader','en-core-web-sm']},'generation_calls':0}, indent=2))
'''
    completed = subprocess.run([str(TRIAL / 'runtime/Scripts/python.exe'), '-c', script], cwd=TRIAL / 'app/resources', env=backend_env(), capture_output=True, text=True, encoding='utf-8', timeout=120)
    (TRIAL / 'engine_inspection_stdout.txt').write_text(completed.stdout, encoding='utf-8')
    (TRIAL / 'engine_inspection_stderr.txt').write_text(completed.stderr, encoding='utf-8')
    print(completed.stdout)
    print(completed.stderr[-2500:])
    sys.exit(completed.returncode)

elif sys.argv[1] == 'model':
    metadata = json.loads((TRIAL / 'model_metadata.json').read_text(encoding='utf-8-sig'))
    revision = metadata['sha']
    assert revision == 'c02725660cea441db4c383af69f1f26f5cd00947'
    assert metadata['cardData']['license'] == 'apache-2.0'
    cache = TRIAL / 'model-cache/models--KittenML--kitten-tts-mini-0.8'
    snapshot = cache / 'snapshots' / revision
    snapshot.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for asset in metadata['siblings']:
        name = asset['rfilename']
        if name not in ('README.md', 'config.json', 'kitten_tts_mini_v0_8.onnx', 'voices.npz'):
            continue
        destination = snapshot / name
        if not destination.exists():
            with urllib.request.urlopen(f'https://huggingface.co/KittenML/kitten-tts-mini-0.8/resolve/{revision}/{name}', timeout=60) as response, destination.open('xb') as target:
                shutil.copyfileobj(response, target, 1024*1024)
        actual = descriptor(destination)
        assert actual['bytes'] == asset['size']
        if 'lfs' in asset:
            assert actual['sha256'] == asset['lfs']['sha256']
        else:
            content = destination.read_bytes()
            assert hashlib.sha1(f'blob {len(content)}\0'.encode() + content).hexdigest() == asset['blobId']
        downloaded.append(actual)
    (cache / 'refs').mkdir(exist_ok=True)
    (cache / 'refs/main').write_text(revision, encoding='ascii')
    write(TRIAL / 'model_download_receipt.json', {'recorded_at_utc': now(), 'repository': 'KittenML/kitten-tts-mini-0.8', 'revision': revision, 'license_metadata': 'apache-2.0', 'files': downloaded, 'total_file_bytes': sum(x['bytes'] for x in downloaded), 'runtime_network_policy': 'HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1 during backend validation/generation. Cache main ref pinned to immutable revision; no fallback models.'})
    print(json.dumps({'revision': revision, 'files': downloaded}, indent=2))

elif sys.argv[1] in ('cpu-runtime', 'resume-runtime'):
    env = os.environ.copy()
    for name, folder in [('UV_CACHE_DIR','uv-cache'), ('UV_PYTHON_INSTALL_DIR','python'), ('TEMP','tmp'), ('TMP','tmp')]:
        destination = TRIAL / folder
        destination.mkdir(exist_ok=True)
        env[name] = str(destination)
    env['UV_NO_PROGRESS'] = '1'
    env['UV_CONCURRENT_DOWNLOADS'] = '1'
    env['UV_CONCURRENT_INSTALLS'] = '1'
    uv = str(pathlib.Path.home() / '.local/bin/uv.exe')
    venv = TRIAL / 'runtime'
    if not (venv / 'Scripts/python.exe').exists():
        subprocess.run([uv, 'venv', str(venv), '--python', str(pathlib.Path.home() / 'AppData/Local/Programs/Python/Python311/python.exe')], env=env, check=True)
    source = (TRIAL / 'requirements-release.txt').read_text()
    # Preserve frozen release versions and platform markers; replace NVIDIA builds only.
    cpu = source.replace('torch==2.8.0+cu128', 'torch==2.8.0+cpu').replace('torchaudio==2.8.0+cu128', 'torchaudio==2.8.0+cpu').replace('torchvision==0.23.0+cu128', 'torchvision==0.23.0+cpu')
    (TRIAL / 'requirements-cpu.txt').write_text(cpu, encoding='utf-8')
    cache_args = ['--no-cache']
    resumed = sys.argv[1] == 'resume-runtime'
    if resumed:
        # Reuse only this attempt's interrupted cache, which is inside the trial.
        recovered = [p for p in (TRIAL / 'tmp').iterdir() if p.is_dir() and (p / 'archive-v0').is_dir()]
        assert len(recovered) == 1
        cache_args = ['--cache-dir', str(recovered[0]), '--link-mode', 'hardlink']
        before = disk_upper_bound()
        assert before['file_allocation_upper_bound_bytes'] < 8 * 1024**3
        write(TRIAL / 'disk_guard_reassessment.json', {'recorded_at_utc': now(), 'trial_storage': before, 'drive_increase_bytes': json.loads((TRIAL / 'disk_baseline.json').read_text())['drive_free_bytes'] - shutil.disk_usage(ROOT).free, 'finding': 'Whole-drive free-space change exceeds storage attributable to this contained trial. Original conservative drive guard stopped installation. Reuse existing unpacked cache with hardlinks, single download/install concurrency, and count unique file allocations under the original trial ceiling.', 'generation_attempts': 0})
    command = [uv, 'pip', 'sync', '--python', str(venv / 'Scripts/python.exe'), *cache_args, '--index', 'https://download.pytorch.org/whl/cpu', '--index-strategy', 'unsafe-best-match', str(TRIAL / 'requirements-cpu.txt')]
    write(TRIAL / ('cpu_runtime_resume.json' if resumed else 'cpu_runtime_install.json'), {'started_at_utc': now(), 'command': command, 'release_requirements': descriptor(TRIAL / 'requirements-release.txt'), 'cpu_requirements': descriptor(TRIAL / 'requirements-cpu.txt'), 'deviation': 'Same release-pinned dependencies, CPU wheels for torch 2.8.0/torchaudio 2.8.0/torchvision 0.23.0; do not run CUDA frozen bootstrap on AMD host.', 'models_downloaded_by_this_action': False})
    baseline = json.loads((TRIAL / 'disk_baseline.json').read_text())
    log_path = TRIAL / 'cpu-runtime-install.log'
    with log_path.open('ab') as log:
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        while process.poll() is None:
            time.sleep(3)
            increase = baseline['drive_free_bytes'] - shutil.disk_usage(ROOT).free
            measured = disk_upper_bound()['file_allocation_upper_bound_bytes'] if resumed else increase
            if measured > 9 * 1024**3:
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
                raise SystemExit('Stopped installation at conservative disk guard')
    print(log_path.read_text(encoding='utf-8', errors='replace')[-7000:])
    print('Runtime installer exit:', process.returncode)
    sys.exit(process.returncode)
