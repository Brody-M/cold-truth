"""Apply the accepted audio profile to one authorized, reconciled Short take."""
from pathlib import Path
from datetime import datetime, timezone
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from automation import pilot_evidence as evidence
HERE = Path(__file__).resolve().parent

def now():
    return datetime.now(timezone.utc).isoformat()

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def describe(path):
    return evidence.describe(ROOT, path.relative_to(ROOT).as_posix())

def write(path, record):
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def probe(path):
    return json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
        '-of', 'json', str(path)], capture_output=True, text=True, check=True, timeout=30).stdout)

def decoded_samples(path):
    result = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-threads', '2', '-i', str(path),
        '-map', '0:a:0', '-ac', '1', '-ar', '44100', '-f', 's24le', '-'],
        capture_output=True, check=True, timeout=60)
    assert len(result.stdout) % 3 == 0
    return len(result.stdout) // 3

def main():
    index = int(sys.argv[1]) - 1
    assert index in range(3)
    proposal = read(HERE / 'next_production_scope_2026_10_21.json')
    branch = proposal['shorts_branches'][index]
    batch = read(HERE / 'shorts_narration_batch_01.json')
    entry = batch['entries'][index]
    assert entry['status'] == 'GENERATED_RECONCILED' and entry['attempts_submitted'] == 1
    evidence.bound(ROOT, entry['phase_2_scope'])
    scope = read(ROOT / entry['phase_2_scope']['path'])
    evidence.decision(scope)
    evidence.bound(ROOT, scope['parent_approval'])
    evidence.bound(ROOT, branch['audio_treatment_profile'])
    profile = read(ROOT / branch['audio_treatment_profile']['path'])
    base = (ROOT / branch['script']['path']).parent
    audio = base / 'Audio'
    automation = base / 'Automation'
    sources = list((ROOT / branch['provider_output_directory']).glob('*.mp3'))
    assert len(sources) == 1
    raw, master, preview = [ROOT / p for p in branch['canonical_audio_paths']]
    assert not any(p.exists() for p in [raw, master, preview])
    assert decoded_samples(sources[0]) > 0
    shutil.copyfile(sources[0], raw)
    assert describe(sources[0])['sha256'] == describe(raw)['sha256']
    work = audio / 'processing_work_01'
    work.mkdir()
    receipt = automation / 'audio_processing_01.json'
    assert not receipt.exists()
    record = {'status': 'IN_PROGRESS', 'started_at_utc': now(), 'tool': 'Installed FFmpeg8.1.1',
        'authority': entry['phase_2_scope'], 'profile': branch['audio_treatment_profile'],
        'raw_provider_file': describe(sources[0]), 'raw_canonical': describe(raw), 'commands': [],
        'new_generation_calls_in_processing': 0, 'time_stretch': False, 'padding': False, 'cuts': False}
    write(receipt, record)
    current = raw
    try:
        for stage in [1, 2, 3]:
            output = master if stage == 3 else work / f'stage_{stage}.wav'
            command = ['ffmpeg', '-v', 'warning', '-nostdin', '-n', '-threads', '2', '-filter_threads', '2',
                '-i', str(current), '-af', profile[f'stage_{stage}_filter'], '-ar', '44100', '-ac', '1',
                '-c:a', 'pcm_s24le', str(output)]
            record['commands'].append({'stage': stage, 'started_at_utc': now(), 'command': command})
            write(receipt, record)
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
            record['commands'][-1].update(returncode=result.returncode, diagnostics=result.stderr)
            assert result.returncode == 0, result.stderr
            current = output
        command = ['ffmpeg', '-v', 'warning', '-nostdin', '-n', '-threads', '2', '-i', str(master),
            '-c:a', 'libmp3lame', '-b:a', '192k', str(preview)]
        record['commands'].append({'stage': 'listening_preview', 'started_at_utc': now(), 'command': command})
        write(receipt, record)
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        record['commands'][-1].update(returncode=result.returncode, diagnostics=result.stderr)
        assert result.returncode == 0, result.stderr
        raw_samples = decoded_samples(raw)
        master_samples = decoded_samples(master)
        assert raw_samples == master_samples, 'Accepted processing changed decoded sample count'
        measurement_command = ['ffmpeg', '-v', 'info', '-nostdin', '-threads', '2', '-filter_threads', '2',
            '-i', str(master), '-af', 'loudnorm=I=-23:TP=-1:LRA=7:print_format=json', '-f', 'null', '-']
        measured = subprocess.run(measurement_command, capture_output=True, text=True, check=True, timeout=60)
        stats, _ = json.JSONDecoder().raw_decode(measured.stderr[measured.stderr.rfind('{'):])
        duration = master_samples / 44100
        record.update(status='PROCESSED_TECHNICAL_PASS_HUMAN_FULL_LISTEN_PENDING', completed_at_utc=now(),
            raw_decoded_samples=raw_samples, master_decoded_samples=master_samples, duration_seconds=duration,
            measured_lufs=float(stats['input_i']), measured_true_peak_dbtp=float(stats['input_tp']),
            duration_within_30_to60=30 <= duration <= 60, measurement_command=measurement_command,
            loudness_measurement_output_discarded=True)
        assert float(stats['input_tp']) < 0, 'Unexpected full-scale peak'
        record['probe'] = probe(master)
    except BaseException as error:
        record.update(status='STOPPED_NO_AUTOMATIC_RETRY', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        paths = [p for p in sorted(audio.rglob('*')) if p.is_file()]
        record['outputs'] = [describe(p) for p in paths]
        write(receipt, record)
    event = {'event_id': branch['case_id'] + '-narration-attempt-01', 'case_id': branch['case_id'],
        'target_format': 'shorts', 'script': branch['script'], 'narration_text': branch['narration_text'],
        'phase_2_scope': entry['phase_2_scope'], 'tool': 'mcp__elevenlabs__text_to_speech + authorized local accepted audio treatment',
        'recorded_at_utc': entry['submitted_at_utc'], 'settings': branch['settings'],
        'outputs': record['outputs'], 'billing': entry.get('billing'), 'processing_receipt': describe(receipt)}
    attempt = automation / 'narration_attempt_01.json'
    assert not attempt.exists()
    write(attempt, {'schema_version': 'cold_truth.direct_narration_receipt.v1', 'entries': [event]})
    qa = automation / 'audio_qa_01.json'
    assert not qa.exists()
    write(qa, {'case_id': branch['case_id'], 'target_format': 'shorts', 'script': branch['script'],
        'audio': describe(master), 'human_approved': False, 'approved_by': None, 'approved_on': None,
        'user_quote': None, 'scope': 'Full playback pronunciation/completeness/levels for exact treated Short audio',
        'full_listen_passed': False, 'technical_processing': describe(receipt), 'assembly_allowed': False,
        'issues': ['Actual human full-listen decision required; no listening approval inferred from text/sample acceptance.']})
    request = {'case_id': branch['case_id'], 'case_name': f'Amy Mihaljevic Short {index+1:02}', 'target_format': 'shorts',
        'script_approval': branch['script_approval'], 'script': branch['script'], 'narration_text': branch['narration_text'],
        'audio': describe(master), 'phase_2_scope': entry['phase_2_scope'], 'generation_manifest': describe(attempt),
        'generation_event_id': event['event_id'], 'audio_qa': describe(qa)}
    request_path = automation / 'audio_preflight_request.json'
    assert not request_path.exists()
    write(request_path, request)
    try:
        evidence.audio_preflight(ROOT, request_path.relative_to(ROOT).as_posix())
        raise AssertionError('Unreviewed audio unexpectedly passed')
    except evidence.EvidenceError as error:
        assert str(error) == 'Human decision required'
        write(automation / 'preflight_pending_qa.json', {'status': 'BLOCKED_PENDING_ACTUAL_FULL_LISTEN',
            'case_id': branch['case_id'], 'target_format': 'shorts', 'request': describe(request_path),
            'actual_audio': describe(master), 'measured_duration_seconds': duration,
            'duration_in_target_range': 30 <= duration <= 60, 'assembly_allowed': False, 'blocking_result': str(error)})
    print(json.dumps({'short': index+1, 'duration_seconds': duration, 'lufs': record['measured_lufs'],
        'true_peak': record['measured_true_peak_dbtp'], 'status': record['status']}), flush=True)

if __name__ == '__main__':
    main()
