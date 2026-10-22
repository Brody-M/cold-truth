"""Offline timing preparation only; human audio/timing gates remain pending."""
from pathlib import Path
from datetime import datetime, timezone
import json
import math
import os
import socket
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from automation import pilot_evidence as evidence
HERE = Path(__file__).resolve().parent

def blocked(*args, **kwargs):
    raise RuntimeError('Network/model download prohibited in this offline timing run')

def describe(path):
    return evidence.describe(ROOT, path.relative_to(ROOT).as_posix())

def main():
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['OMP_NUM_THREADS'] = '2'
    checkpoint = Path('C:/Users/brody/.cache/torch/hub/checkpoints/wav2vec2_fairseq_base_ls960_asr_ls960.pth')
    assert checkpoint.exists() and checkpoint.stat().st_size == 377664473
    socket.socket.connect = blocked
    import torch
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.hub.download_url_to_file = blocked
    import whisperx
    model, metadata = whisperx.load_align_model(language_code='en', device='cpu', model_name='WAV2VEC2_ASR_BASE_960H')
    proposal = json.loads((HERE / 'next_production_scope_2026_10_21.json').read_text(encoding='utf-8'))
    summary = []
    for index, branch in enumerate(proposal['shorts_branches'], 1):
        base = (ROOT / branch['script']['path']).parent
        automation = base / 'Automation'
        output = automation / 'alignment_draft.json'
        assert not output.exists()
        evidence.approval(ROOT, branch['script_approval']['path'])
        processing = json.loads((automation / 'audio_processing_01.json').read_text(encoding='utf-8'))
        assert processing['duration_within_30_to60'] is True
        audio_path = ROOT / branch['canonical_audio_paths'][1]
        text = (ROOT / branch['narration_text']['path']).read_text(encoding='utf-8')
        audio = whisperx.load_audio(str(audio_path))
        result = whisperx.align([{'start': 0.0, 'end': processing['duration_seconds'], 'text': text}],
            model, metadata, audio, 'cpu', interpolate_method='nearest', return_char_alignments=False)
        words = result['word_segments']
        sequence = evidence.words(' '.join(word['word'] for word in words)) == evidence.words(text)
        invalid = [i for i, w in enumerate(words) if not all(isinstance(w.get(k), (int, float)) and math.isfinite(w[k]) for k in ['start', 'end'])
                   or not (0 <= w.get('start', -1) < w.get('end', -1) <= processing['duration_seconds'])]
        low = [dict(index=i, **w) for i, w in enumerate(words) if w.get('score', 0) < .5]
        record = dict(schema_version='cold_truth.machine_short_alignment_draft.v1',
            case_id=branch['case_id'], target_format='shorts', recorded_at_utc=datetime.now(timezone.utc).isoformat(),
            status='MACHINE_DRAFT_AUDIO_AND_TIMING_HUMAN_REVIEW_PENDING',
            tool='Existing WhisperX3.4.5 + cached torchaudio WAV2VEC2_ASR_BASE_960H, CPU2 threads, offline',
            bindings=dict(audio=describe(audio_path), script=branch['script'], narration_text=branch['narration_text'],
                script_approval=branch['script_approval'], audio_processing=describe(automation / 'audio_processing_01.json'),
                phase_2_scope=describe(automation / 'approvals/phase_2_narration_and_review_2026_10_21.json')),
            source_text=text, duration_seconds=processing['duration_seconds'], segments=result['segments'], word_segments=words,
            qa=dict(approved_word_sequence_preserved=sequence, source_words=len(evidence.words(text)), timed_words=len(words),
                invalid_word_indices=invalid, low_confidence_words=low, human_review_required=True),
            human_audio_approved=False, timing_review=dict(human_approved=False, full_listen_passed=False),
            narration_requests=0, model_downloads=0, network_connections_permitted=False, assembly_allowed=False)
        output.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        summary.append(dict(short=index, alignment=describe(output), sequence_preserved=sequence,
            invalid_word_intervals=len(invalid), low_confidence_words=len(low)))
        print(json.dumps(summary[-1]), flush=True)
    (HERE / 'shorts_timing_drafts_01.json').write_text(json.dumps(dict(
        created_at_utc=datetime.now(timezone.utc).isoformat(), tool_source=describe(Path(__file__)),
        checkpoint=str(checkpoint), cached_model_only=True, cpu_threads=2, entries=summary,
        actual_audio_and_timing_reviews_pending=True, assembly_allowed=False), indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
