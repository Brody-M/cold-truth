"""Create authorized source-bound text cards and still contact sheets. No video render."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
from xml.sax.saxutils import escape
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
VIS = HERE.parent / 'Visuals'
GRAPHICS = VIS / 'Longform/graphics'
QC = VIS / 'Longform/qc'
FONT = Path('C:/Windows/Fonts/segoeui.ttf')
BOLD = Path('C:/Windows/Fonts/seguisb.ttf')
RESUME = '--resume-reviewed-qc' in sys.argv

def desc(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def save(path, data):
    assert not path.exists() or (RESUME and path.name == 'case_graphics_01.json'), path
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def make_card(ident, title, lines, sources, cues, columns=False):
    source_reference = sources
    sources = {
        'CG01_Amy': 'Sources: FBI; attributed family interviews',
        'CG02_October_1989': 'Sources: FBI; Bay Village Police',
        'CG03_February_1990': 'Sources: FBI; Bay Village Police',
        'CG04_Belongings': 'Source: FBI public information appeal',
        'CG05_Textile_Appeal': 'Sources: News 5 reports, 2016 and 2021',
        'CG06_Different_Samples': 'Sources: News 5; Cleveland 19, January 9, 2026',
        'CG07_Public_Status': 'Sources: FBI; Bay Village Police',
        'CG08_Remembering_Amy': 'Cold Truth',
    }[ident]
    image = Image.new('RGB', (1920, 1080), '#11161c')
    draw = ImageDraw.Draw(image)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">',
           '<rect width="1920" height="1080" fill="#11161c"/>']
    def text(x, y, value, size, color='#f1ece4', bold=False):
        font = ImageFont.truetype(str(BOLD if bold else FONT), size)
        assert draw.textbbox((x, y), value, font=font)[2] < 1850, value
        draw.text((x, y), value, font=font, fill=color)
        svg.append(f'<text x="{x}" y="{y + size}" fill="{color}" font-size="{size}" font-family="Segoe UI, sans-serif" font-weight="{600 if bold else 400}">{escape(value)}</text>')
    text(128, 80, 'COLD TRUTH', 32, '#b47673', True)
    text(128, 220, title, 64 if len(title) > 30 else 78, bold=True)
    draw.line((128, 338, 1792, 338), fill='#343e49', width=2)
    svg.append('<path d="M128 338H1792" stroke="#343e49" stroke-width="2"/>')
    if columns:
        for col, body in enumerate(lines):
            for row, value in enumerate(body):
                text(128 + col * 864, 396 + row * 84, value, 42 if row else 38,
                     '#b47673' if row == 0 else '#f1ece4', row == 0)
    else:
        for row, value in enumerate(lines):
            text(128, 396 + row * 94, value, 46)
    text(128, 966, sources, 25, '#aeb9c4')
    svg.append('</svg>')
    png = GRAPHICS / (ident + '.png')
    vector = GRAPHICS / (ident + '.svg')
    assert RESUME or (not png.exists() and not vector.exists())
    image.save(png)
    vector.write_text('\n'.join(svg) + '\n', encoding='utf-8')
    return {'asset_id': 'AMY-LF-' + ident, 'source_identity': 'coldtruth:amy:longform:' + ident,
            'asset_class': 'case_graphic', 'track': 'youtube-longform', 'title': title,
            'narration_cues': cues, 'png': desc(png), 'svg': desc(vector),
            'sources_displayed': sources, 'source_reference': source_reference,
            'created_from': 'Original typography/layout; no third-party case photograph or exhibit reproduction',
            'content_review': 'Source-bound text, pending final asset review; no suspect, reenactment or graphic depiction'}

def main():
    GRAPHICS.mkdir(parents=True, exist_ok=True)
    QC.mkdir(parents=True, exist_ok=True)
    cards = [
        make_card('CG01_Amy', 'Amy Mihaljevic', ['Age 10 | Bay Village, Ohio', 'A daughter. A sister.'], 'Sources: FBI S01 | Approved narration P02 / P19', ['P02', 'P19']),
        make_card('CG02_October_1989', 'October 27, 1989', ['Bay Village, Ohio', 'An arranged after-school meeting'], 'Sources: FBI S01 | Bay Village Police S02', ['P03', 'P04']),
        make_card('CG03_February_1990', 'February 8, 1990', ['Amy’s body was found in rural Ashland County.'], 'Sources: FBI S01 | Bay Village Police S02', ['P08']),
        make_card('CG04_Belongings', 'Three unrecovered belongings', ['Turquoise horse earring', 'Black ankle boots', 'Black leather binder'], 'Source: FBI S01 | Public information appeal', ['P09']),
        make_card('CG05_Textile_Appeal', 'A request for recognition', ['2016 | Curtain displayed publicly', '2021 | Reported hair association', 'No owner or origin established in the public account'], 'Sources: News 5 S04 / S08 | Reported official statements', ['P10', 'P11', 'P13']),
        make_card('CG06_Different_Samples', 'Different samples. Different results.', [['2024 | Clothing DNA', 'Male DNA detected', 'Too little for a profile'], ['January 2026 | Hairs', 'No profile obtained', 'Reported testing setback']], 'Sources: News 5 S09 / S11 | Cleveland 19 S12 | Separate samples', ['P14', 'P15', 'P16'], True),
        make_card('CG07_Public_Status', 'Public appeal remains open', ['Source check: October 16, 2026', 'Bay Village Police: ongoing investigation', 'FBI reward: up to $25,000*', '*Information leading to arrest and conviction'], 'Sources: FBI S01 | Bay Village Police S02 | Matches approved audio date', ['P18']),
        make_card('CG08_Remembering_Amy', 'Remembering Amy', ['Her life belongs beyond the evidence.'], 'Approved narration P19 | Family context attributed in episode', ['P19']),
    ]
    save(HERE / 'case_graphics_01.json', {'created_at_utc': datetime.now(timezone.utc).isoformat(),
         'tool': 'Pillow typography and original SVG source', 'resolution': [1920, 1080],
         'video_rendered': False, 'entries': cards, 'processor': desc(Path(__file__))})
    selected = json.loads((HERE / 'pexels_selected_sources_2026_10_21.json').read_text(encoding='utf-8'))['entries']
    measurements = []
    for index, asset in enumerate(selected):
        video = ROOT / asset['output_path']
        probe = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name,width,height,r_frame_rate,duration', '-of', 'json', str(video)],
            check=True, capture_output=True, text=True).stdout)
        stream = probe['streams'][0]
        meets_requested_quality = stream['width'] == 1920 and stream['height'] == 1080
        duration = float(stream['duration'])
        frames = []
        for frame_index, fraction in enumerate([.1, .5, .9]):
            output = QC / f"{asset['provider_id']}_{frame_index + 1}.jpg"
            if not output.exists():
                subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-threads', '2', '-ss', str(duration*fraction),
                    '-i', str(video), '-frames:v', '1', '-vf', 'scale=360:202', '-q:v', '3', str(output)], check=True, capture_output=True)
            frames.append(desc(output))
        measurements.append({'asset_id': asset['asset_id'], 'source_identity': asset['source_identity'],
            'file': desc(video), 'probe': probe, 'sampled_frames': frames,
            'meets_requested_1080p': meets_requested_quality,
            'technical_quality_status': 'PASS_1080P' if meets_requested_quality else 'EXCLUDE_RESOLUTION_DIFFERS_FROM_API_METADATA',
            'sample_times_seconds': [duration*f for f in [.1, .5, .9]],
            'content_review': 'Three sampled frames prepared; not a full-motion or final-trim approval'})
        print(json.dumps({'frames_prepared': asset['provider_id']}), flush=True)
    sheets = []
    for number, start in enumerate(range(0, len(measurements), 7), 1):
        sheet = Image.new('RGB', (1120, 7*248+24), '#11161c')
        draw = ImageDraw.Draw(sheet)
        for row, (measurement, asset) in enumerate(zip(measurements[start:start+7], selected[start:start+7])):
            label = f"{asset['provider_id']} | {asset['title'][:68]}"
            draw.text((16, row*248+12), label, font=ImageFont.truetype(str(FONT), 19), fill='#f1ece4')
            for col, frame in enumerate(measurement['sampled_frames']):
                with Image.open(ROOT / frame['path']) as image:
                    sheet.paste(image, (16+col*368, row*248+40))
        path = QC / f'pexels_contact_sheet_{number:02d}.jpg'
        sheet.save(path, quality=90)
        sheets.append(desc(path))
    save(HERE / 'pexels_visual_qc_01.json', {'created_at_utc': datetime.now(timezone.utc).isoformat(),
         'status': 'SAMPLED_FRAME_REVIEW_PENDING', 'entries': measurements, 'contact_sheets': sheets,
         'video_rendered': False, 'assembly_allowed': False})
    print(json.dumps({'cards': len(cards), 'clips': len(measurements), 'contact_sheets': sheets}), flush=True)

if __name__ == '__main__':
    main()
