"""M6 review evidence from existing files; no video output or final approvals."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CASE = HERE.parent
VIS = CASE / 'Visuals'
NOW = datetime.now(timezone.utc).isoformat()

def desc(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
            'sha256': hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()}

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(data, indent=2, ensure_ascii=False) + '\n')

def main():
    selected = read(HERE / 'pexels_selected_sources_2026_10_21.json')['entries']
    qc = read(HERE / 'pexels_visual_qc_01.json')
    excluded = {
        4203565: 'Visible architecture/geographic cues unsuitable for this Bay Village narrative.',
        14388669: 'Derelict interior mall is inappropriate for the known shopping-center context.',
        13529951: 'Actual decoded source is 1280x720, despite API/URL claiming 1080p.',
        5482661: 'Recognizable patterned curtains could be mistaken for the actual case textile.',
    }
    notes = {
        5835776: 'Generic quiet autumn neighborhood. Never label it the actual street or home.',
        5792244: 'Parked bicycles only; not Amy\u2019s actual bicycle or a discovery reconstruction.',
        5792246: 'Restrict to tight bicycle detail; avoid cluttered wider rack/plaza. Final trim pending.',
        6577022: 'Illustrative open landscape only; not the actual recovery site. Review timelapse motion.',
        854698: 'Modern landline/anonymous hand. No actual 1989 call or caller reenactment claim.',
        6550428: 'Generic library catalog. Do not label as actual police evidence or case files.',
        8325857: 'Unoccupied generic lab. Not an actual case sample or test.',
        8325856: 'Unoccupied generic lab. Not an actual case sample or test.',
        7233562: 'Abstract white knit texture only; never a case exhibit or reconstructed curtain.',
        14512668: 'Generic saddled horse for riding context; not Amy\u2019s actual horse.',
    }
    decisions = []
    for source, measurement in zip(selected, qc['entries']):
        path = ROOT / source['output_path']
        result = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-threads', '2',
            '-i', str(path), '-map', '0:v:0', '-an', '-f', 'null', '-'],
            capture_output=True, text=True, timeout=120)
        ident = source['provider_id']
        decoded = result.returncode == 0 and not result.stderr.strip()
        decisions.append({
            'asset_id': source['asset_id'], 'source_identity': source['source_identity'],
            'asset': measurement['file'], 'reviewer': 'Codex', 'reviewed_at_utc': NOW,
            'review_scope': 'Three sampled stills at 10/50/90 percent; full video decode technical check. Not full-motion human review.',
            'technical_decode': {'passed': decoded, 'returncode': result.returncode,
                                 'diagnostics': result.stderr[:4000]},
            'resolution_qualified': measurement['meets_requested_1080p'],
            'editorial_candidate': ident not in excluded and decoded,
            'assistant_assessment': excluded.get(ident, notes.get(ident)),
            'final_trim_review_pending': True, 'human_approved': False,
            'rights_review_pending': True,
        })
        print(json.dumps({'decoded': ident, 'pass': decoded}), flush=True)
    save(HERE / 'visual_candidate_review_01.json', {
        'created_at_utc': NOW, 'reviewer': 'Codex', 'entries': decisions,
        'downloaded': len(decisions), 'editorial_candidates': sum(d['editorial_candidate'] for d in decisions),
        'excluded': len(excluded), 'assembly_allowed': False})

    rights = VIS / 'Longform/rights/pexels_license_evidence_2026_10_21.json'
    save(rights, {'checked_at_utc': NOW, 'checked_by': 'Codex',
        'sources': ['https://www.pexels.com/license/', 'https://www.pexels.com/terms-of-service/'],
        'retrieval': 'Official pages read with web tool on 2026-10-21',
        'summary': 'Pexels permits free use and editing, including commercial use. Attribution is optional. Restrictions cover offensive depiction of identifiable people, implied endorsements, unaltered resale and stock redistribution; additional third-party rights may apply.',
        'usage_conditions': ['Use only in edited factual episode, as illustrative stock.',
            'No stock person, home, street, vehicle or object identified as case evidence.',
            'Drop all stock audio. Review actual trims for people, logos and misleading context.',
            'Retain source-page/creator/file provenance. Credit creators voluntarily in release package.'],
        'individual_sources': desc(HERE / 'pexels_selected_sources_2026_10_21.json'),
        'human_approved': False, 'status': 'EVIDENCE_CAPTURED_FINAL_USE_REVIEW_PENDING'})
    save(VIS / 'Longform/rights/original_case_graphics_01.json', {
        'created_at_utc': NOW, 'creator': 'Cold Truth / Codex',
        'method': 'Original typography and SVG/Pillow layout; system Segoe UI font used for rendered lettering.',
        'third_party_case_images_used': False, 'ledger_and_claim_map': 'Approved Amy narration and source-bound claim map',
        'graphics_record': desc(HERE / 'case_graphics_01.json'),
        'status': 'ORIGINAL_TEXT_CARDS_PENDING_CONTENT_AND_FINAL_USE_REVIEW', 'human_approved': False})

    gameplay = read(HERE / 'orbital_file_verification_2026_10_21.json')
    history = read(HERE / 'orbital_source_assessment_2026_10_21.json')
    sqc = VIS / 'Shorts/qc'
    sqc.mkdir(parents=True, exist_ok=True)
    frames = []
    for index, when in enumerate([1, 600, 1200, 1800], 1):
        path = sqc / f'orbital_sample_{index:02d}.jpg'
        subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-threads', '2', '-ss', str(when),
            '-i', str(ROOT / gameplay['file']['path']), '-frames:v', '1', '-vf', 'scale=640:360',
            '-q:v', '3', str(path)], check=True, capture_output=True, timeout=60)
        frames.append({'time_seconds': when, 'file': desc(path)})
    sheet = Image.new('RGB', (1320, 790), '#11161c')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 22)
    for index, frame in enumerate(frames):
        x, y = 10 + (index % 2) * 660, 10 + (index // 2) * 390
        draw.text((x, y), f"Shorts only | source {frame['time_seconds']}s", font=font, fill='white')
        with Image.open(ROOT / frame['file']['path']) as image:
            sheet.paste(image, (x, y + 28))
    path = sqc / 'orbital_contact_sheet.jpg'
    sheet.save(path, quality=90)
    save(HERE / 'orbital_sampled_frame_qc_01.json', {
        'created_at_utc': NOW, 'source': gameplay['file'], 'samples': frames,
        'contact_sheet': desc(path), 'full_motion_review': False,
        'vertical_crop_review': False, 'video_rendered': False, 'human_approved': False})
    save(VIS / 'Shorts/rights/orbital_license_evidence_2026_10_21.json', {
        'checked_at_utc': NOW, 'checked_by': 'Codex', 'asset': gameplay['file'],
        'historical_acquisition_record': history['historical_record'],
        'historical_event': history['historical_acquisition_event'],
        'matching_public_listing': history['current_matching_creator_listing'],
        'required_credit': history['required_credit_from_historical_record'],
        'conditions': ['Shorts-only source under project rules.', 'Reference existing file in place; do not duplicate 12GB.',
            'Disable original gameplay audio.', 'Review chosen crop and actual trim before assembly.'],
        'limitation': 'Original purchased item URL and separate purchase/license receipt are not preserved. Matching public listing is supporting evidence, not proof of exact original item.',
        'human_approved': False, 'status': 'PURCHASE_HISTORY_AND_CREATOR_PERMISSION_BOUND_FOR_NAMED_REVIEW'})

    cards = read(HERE / 'case_graphics_01.json')['entries']
    sheet = Image.new('RGB', (1280, 4 * 390), '#11161c')
    draw = ImageDraw.Draw(sheet)
    for index, card in enumerate(cards):
        x, y = (index % 2) * 640, (index // 2) * 390
        draw.text((x + 12, y + 6), card['asset_id'], font=font, fill='white')
        with Image.open(ROOT / card['png']['path']) as image:
            sheet.paste(image.resize((640, 360)), (x, y + 30))
    path = VIS / 'Longform/qc/case_graphics_contact_sheet.jpg'
    sheet.save(path, quality=94)
    print(json.dumps({'graphics_contact_sheet': desc(path), 'gameplay_contact_sheet': desc(sqc / 'orbital_contact_sheet.jpg')}))

if __name__ == '__main__':
    main()
