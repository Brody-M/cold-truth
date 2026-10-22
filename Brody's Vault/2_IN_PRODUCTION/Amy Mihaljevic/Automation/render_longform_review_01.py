"""Authorized Amy review cut, using existing approved media. No provider/upload calls."""
from pathlib import Path
from datetime import datetime, timezone
import json
import hashlib
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from automation import pilot_evidence as evidence

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
APPROVAL = HERE / 'approvals/phase_2_review_production_2026_10_21.json'
RECIPE = CASE / 'Visuals/Longform/review_cut_recipe_2026_10_21.json'
RECEIPT = HERE / 'longform_review_render_01.json'
CAP = 5 * 1024**3

def now():
    return datetime.now(timezone.utc).isoformat()

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def describe(path):
    if path.is_file() and path.stat().st_size == 0:
        return {'path': path.relative_to(ROOT).as_posix(), 'bytes': 0,
                'sha256': hashlib.sha256(b'').hexdigest()}
    return evidence.describe(ROOT, path.relative_to(ROOT).as_posix())

def persist(record):
    RECEIPT.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def budget_bytes():
    folders = [CASE / 'Exports'] + list((CASE / 'Shorts').glob('*/Audio'))
    return sum(p.stat().st_size for folder in folders if folder.exists()
               for p in folder.rglob('*') if p.is_file())

def probe(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                             '-of', 'json', str(path)], check=True, capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout)

def stamp(seconds):
    cs = round(seconds * 100)
    minutes, centiseconds = divmod(cs, 6000)
    hours, minute = divmod(minutes, 60)
    return f'{hours}:{minute:02}:{centiseconds // 100:02}.{centiseconds % 100:02}'

def ass_text(value):
    return value.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}').replace('\n', r'\N')

def main():
    authority = read(APPROVAL)
    evidence.decision(authority)
    proposal = read(ROOT / evidence.bound(ROOT, authority['proposal'])['path'])
    assert proposal['limits']['maximum_new_output_bytes'] == CAP
    evidence.bound(ROOT, proposal['longform_review_recipe'])
    recipe = read(RECIPE)
    for item in recipe['inputs'].values():
        evidence.bound(ROOT, item)
    preflight = evidence.audio_preflight(ROOT, (HERE / 'audio_preflight_request.json').relative_to(ROOT).as_posix())
    evidence.alignment(ROOT, (HERE / 'alignment.json').relative_to(ROOT).as_posix(), preflight)
    asset_check = evidence.assets(ROOT, (HERE / 'asset_registry.json').relative_to(ROOT).as_posix())
    output = ROOT / recipe['output_path']
    work = ROOT / recipe['working_directory']
    assert output.relative_to(ROOT).as_posix() == proposal['longform_outputs'][0]
    assert output.is_relative_to(CASE / 'Exports/Longform') and work.is_relative_to(CASE / 'Exports/Longform')
    assert not output.exists() and not work.exists() and not RECEIPT.exists()
    assert recipe['video_frames'] == 17117 and len(recipe['shots']) == 56
    if '--validate-only' in sys.argv:
        print(json.dumps({'status': 'VALIDATED_NO_RENDER', 'assets': asset_check['counts']}))
        return
    work.mkdir(parents=True)
    record = {'schema_version': 'cold_truth.longform_review_render.v1', 'status': 'IN_PROGRESS',
              'started_at_utc': now(), 'authority': describe(APPROVAL), 'recipe': describe(RECIPE),
              'tool': 'Installed FFmpeg/FFprobe8.1.1', 'render_attempt': 1,
              'settings': recipe['settings'], 'component_commands': [], 'outputs': [],
              'implementation_adjustments': ['Caption bottom margin160px protects source footers at966px; minimum recipe margin80px retained as a minimum. No narration, caption words/times or source graphics changed.',
                  'Component encodes and final caption/mux encode are stages of review render01, not separate reviewed-output versions.'],
              'new_provider_calls': 0, 'publishing': False, 'human_master_playback_approved': False}
    persist(record)
    def run(command, label):
        assert budget_bytes() < CAP - 64 * 1024**2, 'New-output cap reserve exhausted'
        log = work / f'{label}.log'
        event = {'label': label, 'started_at_utc': now(), 'command': command,
                 'log_path': log.relative_to(ROOT).as_posix()}
        record['component_commands'].append(event)
        persist(record)
        with log.open('xb') as sink:
            process = subprocess.Popen(command, cwd=work, stdout=sink, stderr=sink)
            while process.poll() is None:
                if budget_bytes() >= CAP:
                    process.terminate()
                    process.wait(timeout=15)
                    raise RuntimeError('5GiB aggregate new-output ceiling reached')
                time.sleep(1)
            event['returncode'] = process.returncode
        event['finished_at_utc'] = now()
        persist(record)
        if process.returncode:
            raise RuntimeError(f'{label} failed; see preserved log. No automatic retry.')
    try:
        header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Segoe UI,44,&H00E4ECF1,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,0,2,100,100,160,1
Style: Label,Segoe UI,24,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,9,64,64,44,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
        events = []
        for segment in read(HERE / 'alignment.json')['segments']:
            events.append(f"Dialogue: 1,{stamp(segment['start'])},{stamp(segment['end'])},Caption,,0,0,0,,{ass_text(segment['text'])}")
        for shot in recipe['shots']:
            if shot['illustrative_label']:
                events.append(f"Dialogue: 0,{stamp(shot['start_seconds'])},{stamp(shot['end_seconds'])},Label,,0,0,0,,Illustrative footage")
        subtitles = work / 'captions.ass'
        subtitles.write_text(header + '\n'.join(events) + '\n', encoding='utf-8')
        record['outputs'].append(describe(subtitles))
        lines = []
        for index, shot in enumerate(recipe['shots'], 1):
            evidence.bound(ROOT, shot['file'])
            segment = work / f'shot_{index:03d}.mp4'
            command = ['ffmpeg', '-v', 'warning', '-nostdin', '-n', '-threads', '2', '-filter_threads', '2']
            if shot['asset_class'] == 'case_graphic':
                command += ['-loop', '1', '-framerate', '30']
            else:
                command += ['-ss', str(shot['source_in_seconds'])]
            command += ['-i', str(ROOT / shot['file']['path']), '-map', '0:v:0', '-an',
                        '-vf', 'fps=30,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p',
                        '-frames:v', str(shot['frames']), '-c:v', 'libx264', '-preset', 'fast',
                        '-crf', '20', '-maxrate', '8M', '-bufsize', '16M', '-threads', '2',
                        '-pix_fmt', 'yuv420p', '-video_track_timescale', '15360', '-fs', str(160 * 1024**2), str(segment)]
            run(command, f'shot_{index:03d}')
            metadata = probe(segment)
            assert int(metadata['streams'][0]['nb_frames']) == shot['frames'], f'Frame mismatch at shot{index}'
            record['outputs'].append(describe(segment))
            lines.append(f"file '{segment.name}'")
            persist(record)
            print(json.dumps({'shot': index, 'of': 56, 'bytes_so_far': budget_bytes()}), flush=True)
        concat = work / 'segments.txt'
        concat.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        record['outputs'].append(describe(concat))
        command = ['ffmpeg', '-v', 'warning', '-nostdin', '-n', '-threads', '2', '-filter_threads', '2',
                   '-f', 'concat', '-safe', '1', '-i', str(concat),
                   '-i', str(ROOT / recipe['inputs']['approved_audio']['path']),
                   '-map', '0:v:0', '-map', '1:a:0', '-vf', 'subtitles=captions.ass',
                   '-frames:v', str(recipe['video_frames']), '-c:v', 'libx264', '-preset', 'fast',
                   '-crf', '20', '-maxrate', '8M', '-bufsize', '16M', '-threads', '2', '-pix_fmt', 'yuv420p',
                   '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-fs', str(900 * 1024**2), str(output)]
        run(command, 'final_caption_mux')
        metadata = probe(output)
        video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in metadata['streams'] if s['codec_type'] == 'audio')
        assert int(video['nb_frames']) == recipe['video_frames'] and video['width'] == 1920 and video['height'] == 1080
        assert abs(float(audio['duration']) - recipe['audio_duration_seconds']) < .05
        probe_path = HERE / 'longform_review_01_probe.json'
        probe_path.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
        record['outputs'] += [describe(output), describe(probe_path)]
        run(['ffmpeg', '-v', 'error', '-nostdin', '-threads', '2', '-i', str(output), '-map', '0:v:0',
             '-map', '0:a:0', '-f', 'null', '-'], 'full_decode')
        assert (work / 'full_decode.log').stat().st_size == 0, 'Decode diagnostics require investigation'
        record.update(status='REVIEW_CUT_RENDERED_TECHNICAL_PASS_HUMAN_PLAYBACK_PENDING', completed_at_utc=now(),
                      aggregate_new_output_bytes=budget_bytes(), full_decode_passed=True)
    except BaseException as error:
        record.update(status='STOPPED_NO_AUTOMATIC_RETRY', error=f'{type(error).__name__}: {error}', stopped_at_utc=now())
        raise
    finally:
        actual = [path for path in sorted(work.rglob('*')) if path.is_file()]
        actual += [path for path in [output, HERE / 'longform_review_01_probe.json'] if path.exists()]
        record['outputs'] = [describe(path) for path in actual]
        persist(record)
    print(json.dumps({'status': record['status'], 'video': str(output), 'receipt': str(RECEIPT)}), flush=True)

if __name__ == '__main__':
    main()
