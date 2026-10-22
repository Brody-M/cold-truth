"""One offline plosive/level correction candidate. Does not approve or render video."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import numpy as np
import scipy
from scipy import signal, ndimage
import soundfile as sf

HERE = Path(__file__).resolve().parent
CASE = HERE.parent.parent
ROOT = CASE.parents[2]
SOURCE = HERE.parent / 'Amy_Mihaljevic_Mia_attempt_01_processed.wav'
RAW = HERE.parent / 'Amy_Mihaljevic_Mia_attempt_01.mp3'
MASTER = HERE / 'Amy_Mihaljevic_Mia_correction_02.wav'
PREVIEW = HERE / 'Amy_Mihaljevic_Mia_correction_02.mp3'
EVENTS = HERE / 'candidate_plosive_events.csv'
RECEIPT = HERE / 'audio_correction_02_receipt.json'
REPORT = HERE / 'Audio_Correction_02_Report.md'
SOURCE_HASH = '4996c3afaaf3f728b694487256fa49beb036ed68daaf0b26a9f42829d6c25f9b'
RAW_HASH = 'd328526697bae6d55cd3342edd9e01505aa8c6d8231ec138be832a0236c89f02'
RATE = 44100
HOP = 441
GLOBAL_GAIN_DB = -6.0
EXAMPLE_START = 300.0
EXAMPLE_SECONDS = 40.0
EXAMPLE_BEFORE = HERE / 'example_300_340_before.mp3'
EXAMPLE_AFTER = HERE / 'example_300_340_after.mp3'
EXAMPLE_GAIN_ONLY = HERE / 'example_300_340_before_minus6db_gain_only.mp3'
COMMANDS = []

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def descriptor(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def run(argv):
    COMMANDS.append(argv)
    return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, check=True)

def pcm(path):
    return np.frombuffer(run(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(path), '-f', 'f32le', '-ac', '1', '-ar', str(RATE), 'pipe:1']).stdout, dtype='<f4')

def envelope_db(y, frequencies):
    filtered = signal.sosfiltfilt(signal.butter(3, frequencies, btype='bandpass', fs=RATE, output='sos'), y)
    return 10 * np.log10(ndimage.uniform_filter1d(filtered * filtered, size=1765, mode='nearest')[::HOP] + 1e-20)

def measure(path):
    probe = json.loads(run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=codec_name,sample_rate,channels,duration,bits_per_raw_sample:format=duration,size', '-of', 'json', str(path)]).stdout)
    y = pcm(path)
    log = run(['ffmpeg', '-hide_banner', '-nostdin', '-i', str(path), '-af', 'loudnorm=I=-20:TP=-2:LRA=7:print_format=json', '-f', 'null', '-']).stderr.decode('utf-8', errors='replace')
    loudness, _ = json.JSONDecoder().raw_decode(log[log.rfind('{'):])
    return {**descriptor(path), 'probe': probe, 'decoded_samples': len(y), 'decoded_duration_seconds': len(y) / RATE, 'sample_peak_dbfs': float(20 * np.log10(np.max(np.abs(y)) + 1e-20)), 'samples_at_or_above_full_scale': int(np.sum(np.abs(y) >= 1)), 'loudnorm_input_measurements': {k: v for k, v in loudness.items() if k.startswith('input_')}}

def encode_mp3(source, output, extra=None):
    run(['ffmpeg', '-hide_banner', '-nostdin', '-n', '-i', str(source), '-map', '0:a:0', *(extra or []), '-ar', str(RATE), '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '192k', str(output)])

if __name__ == '__main__':
    started = datetime.now(timezone.utc).isoformat()
    outputs = [MASTER, PREVIEW, EVENTS, RECEIPT, REPORT, EXAMPLE_BEFORE, EXAMPLE_AFTER, EXAMPLE_GAIN_ONLY]
    for output in outputs:
        if output.exists():
            raise SystemExit('Refusing to overwrite ' + str(output))
    assert sha(SOURCE) == SOURCE_HASH
    assert sha(RAW) == RAW_HASH
    source, rate = sf.read(SOURCE, dtype='float64')
    raw = pcm(RAW)
    assert rate == RATE and source.ndim == 1 and len(source) == len(raw)
    low_db = envelope_db(raw, [20, 110])
    mid_db = envelope_db(raw, [350, 4000])
    baseline_db = ndimage.median_filter(low_db, size=61, mode='nearest')
    excess_db = low_db - baseline_db
    peaks, _ = signal.find_peaks(excess_db, height=16, prominence=4, distance=18)
    candidates = [int(i) for i in peaks if low_db[i] > -23 and low_db[i] - mid_db[i] > 12]
    assert candidates, 'No candidate events; stop rather than apply an indiscriminate filter'
    words = json.loads((CASE / 'Automation/alignment_draft.json').read_text(encoding='utf-8'))['word_segments']
    def context(t):
        return ' '.join(w['word'] for w in words if w.get('end', -1) > t - 0.9 and w.get('start', 1e9) < t + 0.9)
    # A zero-phase low-pass and exact residual reconstruct the original outside
    # smoothly localized attenuation windows; there is no broadband EQ cut.
    low_component = signal.sosfiltfilt(signal.butter(4, 180, btype='lowpass', fs=RATE, output='sos'), source)
    attenuation_db = np.zeros(len(source), dtype=np.float64)
    events = []
    for index in candidates:
        left = index
        right = index
        while left > max(0, index - 8) and low_db[left] > low_db[index] - 6:
            left -= 1
        while right < min(len(low_db) - 1, index + 8) and low_db[right] > low_db[index] - 6:
            right += 1
        core_start = max(0, left * HOP)
        core_end = min(len(source), (right + 1) * HOP)
        begin = max(0, core_start - round(0.015 * RATE))
        finish = min(len(source), core_end + round(0.080 * RATE))
        strength = float(np.clip(12 + 0.5 * (excess_db[index] - 16), 12, 20))
        envelope = np.ones(finish - begin)
        attack_length = core_start - begin
        release_length = finish - core_end
        if attack_length:
            envelope[:attack_length] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, attack_length))
        if release_length:
            envelope[-release_length:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, release_length))
        attenuation_db[begin:finish] = np.maximum(attenuation_db[begin:finish], strength * envelope)
        events.append({'time_seconds': index * 0.01, 'core_start_seconds': core_start / RATE, 'core_end_seconds': core_end / RATE, 'window_start_seconds': begin / RATE, 'window_end_seconds': finish / RATE, 'raw_20_110_rms_dbfs': float(low_db[index]), 'raw_low_above_350_4000_db': float(low_db[index] - mid_db[index]), 'raw_low_excess_over_local_median_db': float(excess_db[index]), 'low_component_attenuation_db': strength, 'spoken_context_machine_timing': context(index * 0.01), 'audibly_confirmed_plosive': False})
    low_gain = np.power(10.0, -attenuation_db / 20)
    corrected_before_global = source + (low_gain - 1) * low_component
    corrected = corrected_before_global * np.power(10.0, GLOBAL_GAIN_DB / 20)
    assert len(corrected) == len(source)
    assert np.isfinite(corrected).all() and np.max(np.abs(corrected)) < 1
    untouched = attenuation_db == 0
    assert np.max(np.abs(corrected_before_global[untouched] - source[untouched])) == 0
    processed_low = envelope_db(source, [20, 110])
    corrected_low = envelope_db(corrected, [20, 110])
    reductions = []
    for event, index in zip(events, candidates):
        reduction = float(corrected_low[index] - processed_low[index] - GLOBAL_GAIN_DB)
        event['processed_before_20_110_rms_dbfs'] = float(processed_low[index])
        event['corrected_20_110_rms_dbfs'] = float(corrected_low[index])
        event['low_band_change_beyond_global_gain_db'] = reduction
        reductions.append(reduction)
    with EVENTS.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(events[0]))
        writer.writeheader()
        writer.writerows(events)
    sf.write(MASTER, corrected, RATE, subtype='PCM_24')
    encode_mp3(MASTER, PREVIEW)
    clip_filter = f'atrim=start_sample={round(EXAMPLE_START * RATE)}:end_sample={round((EXAMPLE_START + EXAMPLE_SECONDS) * RATE)},asetpts=PTS-STARTPTS'
    encode_mp3(SOURCE, EXAMPLE_BEFORE, ['-af', clip_filter])
    encode_mp3(MASTER, EXAMPLE_AFTER, ['-af', clip_filter])
    encode_mp3(SOURCE, EXAMPLE_GAIN_ONLY, ['-af', clip_filter + ',volume=-6dB'])
    print('Preview ready: ' + str(EXAMPLE_AFTER), flush=True)
    before = measure(SOURCE)
    after = measure(MASTER)
    preview = measure(PREVIEW)
    for result in (after, preview):
        assert result['decoded_samples'] == before['decoded_samples']
        assert result['samples_at_or_above_full_scale'] == 0
    for path in (EXAMPLE_BEFORE, EXAMPLE_AFTER, EXAMPLE_GAIN_ONLY):
        assert len(pcm(path)) == round(EXAMPLE_SECONDS * RATE)
    assert sha(SOURCE) == SOURCE_HASH and sha(RAW) == RAW_HASH
    strongest = sorted(events, key=lambda e: e['raw_low_excess_over_local_median_db'] + e['raw_low_above_350_4000_db'], reverse=True)[:20]
    actual_change = float(after['loudnorm_input_measurements']['input_i']) - float(before['loudnorm_input_measurements']['input_i'])
    report = f'''# Amy audio correction 02 — Editor candidate

The correction targets short low-frequency bursts still present in the prior soundtrack, then lowers the entire track by 6 dB. No normalization or makeup gain follows it. This is an unapproved listening candidate; low overall peaks never ruled out the reported P/B thumps.

Detection used the synchronized original provider audio, before the historical high-pass processing. {len(events)} candidate bursts met the numerical thresholds. The method locally reduces a zero-phase low-frequency component below 180 Hz by 12–20 dB with 15 ms attack and 80 ms release. Higher voice content remains in the exact residual. No blanket treble removal, new compression, timing edit, or video render was performed.

Duration is unchanged at {len(source) / RATE:.9f} seconds / {len(source):,} samples. Prior soundtrack: {before['loudnorm_input_measurements']['input_i']} LUFS, {before['loudnorm_input_measurements']['input_tp']} dBTP. Correction: {after['loudnorm_input_measurements']['input_i']} LUFS, {after['loudnorm_input_measurements']['input_tp']} dBTP. Integrated loudness changed {actual_change:.2f} LU; candidate-event 20–110 Hz energy changed a median {np.median(reductions):.2f} dB beyond the global -6 dB gain. Zero decoded full-scale samples were found.

The 40-second before/after examples both use the actual 300–340 second passage, including strong candidate bursts around 304.70, 312.93, 318.88 and 339.55 seconds. The optional gain-only comparison isolates the difference made by localized processing after matching the requested global -6 dB change.

Numerical detection does not prove every event is a plosive. Low voice fundamentals, onset transitions and other short bass sounds can create false positives. The selective treatment can reduce voice body briefly near such events, so audible success and acceptable tone remain unverified until listening. The prior full-listen decision describes the historical soundtrack and does not approve this correction.

Official references: [iZotope De-plosive documentation](https://downloads.izotope.com/docs/rx6/26-de-plosive/index.html) describes low-frequency plosive energy, processing-frequency limits and the benefit of detecting before high-pass filtering. [iZotope voice-cleanup tutorial](https://www.izotope.com/community/blog/how-to-clean-up-voice-recordings-video-podcasts) explains why indiscriminate low cuts also remove voice body. These references inform this offline method; RX software was not installed or used.
'''
    REPORT.write_text(report, encoding='utf-8')
    feedback = CASE / 'Automation/media_feedback_review_01_2026_10_21.json'
    receipt = {'schema_version': 'cold_truth.audio_correction_candidate.v1', 'status': 'TECHNICALLY_VERIFIED_LISTENING_PENDING', 'role': 'Editor', 'started_at_utc': started, 'completed_at_utc': datetime.now(timezone.utc).isoformat(), 'case_id': 'amy-mihaljevic', 'narration_branch': 'youtube-longform', 'user_feedback_record': descriptor(feedback) if feedback.exists() else None, 'source_processed_audio': before, 'synchronized_original_detector_audio': descriptor(RAW), 'corrected_master': after, 'corrected_preview': preview, 'method': {'detector_band_hz': [20,110], 'reference_band_hz': [350,4000], 'bandpass_order':3, 'envelope_window_samples':1765, 'envelope_hop_samples':HOP, 'local_median_frames':61, 'peak_min_excess_db':16, 'peak_min_prominence_db':4, 'peak_min_spacing_frames':18, 'min_raw_low_rms_dbfs':-23, 'min_low_above_reference_db':12, 'component_lowpass_hz':180, 'component_lowpass_order':4, 'filter_phase':'forward/backward zero phase', 'local_reduction_min_db':12, 'local_reduction_max_db':20, 'strength_formula':'clip(12 + 0.5*(excess_db-16),12,20)', 'core_bounds':'nearest detector-envelope -6dB crossings, capped at80ms each side', 'attack_ms':15, 'release_ms':80, 'smoothing':'half cosine envelope; overlapping events take maximum attenuation', 'mix_formula':'(source + (10**(-local_attenuation_db/20)-1)*low_component) * 10**(-6/20)', 'global_gain_db':GLOBAL_GAIN_DB, 'makeup_gain':False, 'loudness_normalization':False, 'new_compression':False}, 'diagnosis': {'candidate_count':len(events), 'candidate_times_are_not_auditory_confirmations':True, 'strongest_events':strongest, 'median_candidate_low_band_change_beyond_global_db':float(np.median(reductions)), 'processed_fraction_with_nonzero_local_attenuation':float(np.mean(attenuation_db>0)), 'global_peak_does_not_rule_out_perceptual_plosives':True}, 'timeline':{'source_samples':len(source), 'corrected_samples':after['decoded_samples'], 'preview_samples':preview['decoded_samples'], 'rate':RATE, 'duration_seconds':len(source)/RATE, 'cuts':False, 'padding':False, 'time_stretching':False, 'alignment_changed':False}, 'examples':{'start_seconds':EXAMPLE_START, 'end_seconds':EXAMPLE_START+EXAMPLE_SECONDS, 'decoded_duration_seconds':EXAMPLE_SECONDS, 'before_original_level':descriptor(EXAMPLE_BEFORE), 'after_correction':descriptor(EXAMPLE_AFTER), 'gain_only_diagnostic':descriptor(EXAMPLE_GAIN_ONLY)}, 'integrated_loudness_change_lu':actual_change, 'originals_preserved':True, 'canonical_preflight_and_alignment_untouched':True, 'video_rendered':False, 'tts_calls':0, 'software_or_model_installs':0, 'provider_spend':0, 'human_listening_approved':False, 'assembly_allowed':False, 'professional_references':[{'title':'iZotope RX De-plosive documentation','url':'https://downloads.izotope.com/docs/rx6/26-de-plosive/index.html'},{'title':'iZotope voice cleanup tutorial','url':'https://www.izotope.com/community/blog/how-to-clean-up-voice-recordings-video-podcasts'}], 'limitations':['Candidate detector is not a phoneme classifier; false positives can occur on voice fundamentals or other low-frequency transients.', 'Human listening has not verified success, naturalness or absence of remaining thumps.', 'Full corrected soundtrack is intentionally at least6dB quieter overall; no loudness restoration was applied.', 'Historical full-listen approval does not approve corrected output.'], 'commands':COMMANDS, 'tool_versions':{'python':sys.version, 'numpy':np.__version__, 'scipy':scipy.__version__, 'soundfile':sf.__version__, 'ffmpeg':run(['ffmpeg','-version']).stdout.decode('utf-8').splitlines()[0], 'ffprobe':run(['ffprobe','-version']).stdout.decode('utf-8').splitlines()[0]}, 'processor':descriptor(Path(__file__)), 'output_files':[descriptor(p) for p in outputs if p != RECEIPT], 'receipt_self_hash_omitted':True, 'output_file_count_including_processor_and_receipt':len(outputs)+1, 'new_output_bytes_excluding_receipt':sum(p.stat().st_size for p in outputs if p!=RECEIPT)+Path(__file__).stat().st_size}
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    total=sum(p.stat().st_size for p in HERE.iterdir() if p.is_file())
    print(json.dumps({'receipt':descriptor(RECEIPT),'master':descriptor(MASTER),'preview':descriptor(PREVIEW),'candidate_count':len(events),'median_extra_low_band_change_db':float(np.median(reductions)),'loudness_before':before['loudnorm_input_measurements'],'loudness_after':after['loudnorm_input_measurements'],'output_file_count':len(list(HERE.glob('*'))),'total_output_bytes':total},indent=2),flush=True)
