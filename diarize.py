from resemblyzer import VoiceEncoder
from sklearn.cluster import AgglomerativeClustering
import numpy as np
import ffmpeg
import soundfile as sf
import io


def split_audio(wav, sr, chunk_duration=60):
    chunk_len = chunk_duration * sr
    return [wav[i:i + chunk_len] for i in range(0, len(wav), chunk_len)]


def extract_audio_np(video_path, target_sr=16000):
    out, _ = (
        ffmpeg.input(video_path)
        .output("pipe:", format="wav", ac=1, ar=str(target_sr))
        .run(capture_stdout=True, capture_stderr=True)
    )
    audio, sr = sf.read(io.BytesIO(out))
    assert sr == target_sr
    return audio, sr


def diarize(video_path, n_speakers=2):
    wav, sr = extract_audio_np(video_path)
    encoder = VoiceEncoder()

    chunks = split_audio(wav, sr, chunk_duration=60)
    all_embeds = None
    all_wav_splits = []
    offset = 0

    for chunk in chunks:
        chunk_start_sample = int(offset * sr)

        _, cont_embeds, wav_splits = encoder.embed_utterance(
            chunk, return_partials=True, rate=8
        )

        if all_embeds is None:
            all_embeds = cont_embeds
        else:
            all_embeds = np.vstack([all_embeds, cont_embeds])

        all_wav_splits.extend([
            ((chunk_start_sample + slc.start) / sr, (chunk_start_sample + slc.stop) / sr)
            for slc in wav_splits
        ])

        offset += len(chunk) / sr

    labels = AgglomerativeClustering(n_clusters=n_speakers).fit_predict(all_embeds)

    # Get average embeddings per speaker
    speaker_embeds = {}
    for label in set(labels):
        idx = np.where(labels == label)[0]
        speaker_embeds[label] = np.mean(all_embeds[idx], axis=0)

    # Group contiguous segments with same speaker
    segments = []
    current_speaker = labels[0]
    start_time = all_wav_splits[0][0]
    for i in range(1, len(labels)):
        if labels[i] != current_speaker:
            end_time = all_wav_splits[i][0]
            segments.append((current_speaker, start_time, end_time))
            current_speaker = labels[i]
            start_time = all_wav_splits[i][0]
    segments.append((current_speaker, start_time, all_wav_splits[-1][1]))

    # Clip final segment if it's slightly too long
    audio_duration = len(wav) / sr
    last_speaker, last_start, last_end = segments[-1]
    segments[-1] = (last_speaker, last_start, min(last_end, audio_duration))

    return segments

