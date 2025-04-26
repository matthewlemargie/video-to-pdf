import re

def combine_segments_by_sentence(segments):
    combined = []
    buffer = ""
    start_time = None
    end_time = None
    current_speaker = None

    for seg in segments:
        text = seg["text"].strip()
        speaker = seg["speaker"]

        if buffer == "":
            start_time = seg["start"]
            current_speaker = speaker

        buffer += (" " if buffer else "") + text
        end_time = seg["end"]

        # If sentence ends, flush it
        if re.search(r'[.!?]["\']?$|["\']?[.!?]$', text.strip()):
            combined.append({
                "speaker": current_speaker,
                "start": start_time,
                "end": end_time,
                "text": buffer.strip()
            })
            buffer = ""
            start_time = None
            end_time = None
            current_speaker = None

    # Handle any leftover buffer (e.g. if no punctuation at end)
    if buffer:
        combined.append({
            "speaker": current_speaker,
            "start": start_time,
            "end": end_time,
            "text": buffer.strip()
        })

    return combined

def assign_speakers_to_whisper(whisper_segments, diarization_segments):

    labeled = []

    for seg in whisper_segments:
        w_start = seg['start']
        w_end = seg['end']
        mid = (w_start + w_end) / 2

        # Find diarization segment whose start <= mid < end
        speaker = None
        for spk_label, spk_start, spk_end in diarization_segments:
            if spk_start <= mid < spk_end:
                speaker = spk_label
                break

        # If not found (edge case), assign speaker with closest start time
        if speaker is None:
            speaker = min(diarization_segments, key=lambda x: abs(mid - ((x[1] + x[2]) / 2)))[0]

        labeled.append({
            'speaker': speaker,
            'start': w_start,
            'end': w_end,
            'text': seg['text']
        })

    return labeled


def merge_consecutive_speaker_segments(segments):
    merged = []
    buffer = []

    segments = combine_segments_by_sentence(segments)

    for seg in segments:
        if not buffer or seg['speaker'] == buffer[-1]['speaker']:
            buffer.append(seg)
        else:
            merged.append({
                'speaker': buffer[0]['speaker'],
                'start': buffer[0]['start'],
                'end': buffer[-1]['end'],
                'text': " ".join(s['text'].strip() for s in buffer)
            })
            buffer = [seg]

    if buffer:
        merged.append({
            'speaker': buffer[0]['speaker'],
            'start': buffer[0]['start'],
            'end': buffer[-1]['end'],
            'text': " ".join(s['text'].strip() for s in buffer)
        })

    return merged
