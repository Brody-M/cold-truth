"""Probe, fully decode and sample free-stock candidates; never approves their use."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CASE = HERE.parent
SELECTION = HERE / 'pexels_broll_revision_05_selected.json'
QC = CASE / 'Visuals/Longform/revision_05/qc'
RECEIPT = HERE / 'broll_revision_05_technical_qc.json'
FONT = 'C:/Windows/Fonts/segoeui.ttf'

def describe(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def run(command):
    return subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, timeout=180)

if __name__ == '__main__':
    assert not RECEIPT.exists(), 'Refusing to replace original QC evidence'
    entries = json.loads(SELECTION.read_text(encoding='utf-8'))['entries']
    QC.mkdir(parents=True, exist_ok=True)
    result = {'schema_version': 'cold_truth.broll_revision_qc.v1',
              'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'selection': describe(SELECTION), 'processor': describe(Path(__file__)),
              'human_approved': False, 'assembly_allowed': False, 'video_rendered': False,
              'entries': [], 'contact_sheets': []}
    sheets = []
    font = ImageFont.truetype(FONT, 22)
    for index, entry in enumerate(entries):
        path = ROOT / entry['output_path']
        ident = entry['provider_id']
        probe_cmd = ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]
        probe = run(probe_cmd)
        assert probe.returncode == 0, probe.stderr
        metadata = json.loads(probe.stdout)
        stream = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
        duration = float(metadata['format']['duration'])
        assert duration > 0 and stream['width'] > 0 and stream['height'] > 0
        decode_cmd = ['ffmpeg', '-v', 'error', '-nostdin', '-threads', '2', '-i', str(path),
                      '-map', '0:v:0', '-an', '-f', 'null', '-']
        decoded = run(decode_cmd)
        log = QC / f'{ident}_decode.log'
        log.write_bytes(decoded.stderr)
        row = Image.new('RGB', (1440, 330), '#121820')
        draw = ImageDraw.Draw(row)
        draw.text((10, 275), f'{ident} | {duration:.2f}s | {stream["width"]}x{stream["height"]} | ' + ','.join(entry['candidate_paragraphs']), font=font, fill='white')
        samples = []
        for i, fraction in enumerate((.1, .5, .9)):
            at = fraction * duration
            frame = QC / f'{ident}_{i+1}.jpg'
            cmd = ['ffmpeg', '-v', 'error', '-nostdin', '-n', '-ss', str(at), '-i', str(path),
                   '-frames:v', '1', '-q:v', '2', str(frame)]
            sampled = run(cmd)
            assert sampled.returncode == 0 and frame.exists(), sampled.stderr
            image = Image.open(frame).convert('RGB')
            image.thumbnail((480, 270))
            row.paste(image, (i*480+(480-image.width)//2, (270-image.height)//2))
            samples.append({'at_seconds': at, 'frame': describe(frame), 'command': cmd})
        sheets.append(row)
        result['entries'].append({'asset_id': entry['asset_id'], 'source_identity': entry['source_identity'],
            'file': describe(path), 'probe': metadata, 'probe_command': probe_cmd,
            'width': stream['width'], 'height': stream['height'], 'duration_seconds': duration,
            'actual_at_least1080': min(stream['width'], stream['height']) >= 1080,
            'full_video_decode_returncode': decoded.returncode, 'decode_log': describe(log),
            'decode_command': decode_cmd, 'sampled_frames': samples,
            'content_decision': 'PENDING_ACTUAL_FRAME_REVIEW', 'human_rights_approved': False})
        assert decoded.returncode == 0 and decoded.stderr == b'', f'Decode failed {ident}'
        print(json.dumps({'probed_decoded_sampled': ident}), flush=True)
    for i in range(0, len(sheets), 4):
        page = Image.new('RGB', (1440, 330*len(sheets[i:i+4])), '#121820')
        for j, row in enumerate(sheets[i:i+4]):
            page.paste(row, (0, j*330))
        output = QC / f'contact_sheet_{i//4+1:02d}.jpg'
        page.save(output, quality=92)
        result['contact_sheets'].append(describe(output))
    result.update(completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  status='TECHNICAL_QC_COMPLETE_CONTENT_AND_RIGHTS_REVIEW_PENDING')
    RECEIPT.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
