import torch
import os
import ffmpeg
import argparse
import json
from pathlib import Path
import whisper
from resemblyzer.hparams import sampling_rate
import time

from diarize import diarize
from transcribe import combine_segments_by_sentence, assign_speakers_to_whisper, merge_consecutive_speaker_segments
from pdf import segments_to_pdf
from utils import convert_to_serializable

parser = argparse.ArgumentParser(description="AI-video-editor")
parser.add_argument("--video-path", type=str, default="", help="Path to video to be edited")
parser.add_argument("--n-speakers", type=int, default=2, help="number of speakers in the video")

args = parser.parse_args()

video_path = args.video_path
filename = Path(video_path).stem

# Create speaker diarization segments
diarize_segments = diarize(video_path, n_speakers=args.n_speakers)

# Transcribe with Whisper
# Create cache to avoid repeating long transcribe process
os.makedirs("cache", exist_ok=True)
# Load cache if it exists
segments_path = os.path.join("cache", f"{filename}.json")
if os.path.exists(segments_path):
    with open(segments_path, "r") as f:
        result = json.load(f)
else:
    # Extract audio and transcribe speech to text then cache result
    audio_path = "temp_audio.wav"
    ffmpeg.input(video_path).output(audio_path, ac=1, ar=sampling_rate).run(quiet=True, overwrite_output=True)
    model = whisper.load_model("medium", device="cuda" if torch.cuda.is_available() else "cpu")
    result = model.transcribe(audio_path, word_timestamps=True, verbose=True)
    os.remove(audio_path)
    with open(segments_path, "w") as f:
        json.dump(result, f, indent=4, default=convert_to_serializable)

whisper_segments = result["segments"]

# Combine speaker diarization with audio transcription
assigned = assign_speakers_to_whisper(whisper_segments, diarize_segments)
speaker_segments = merge_consecutive_speaker_segments(assigned)

segments_to_pdf(filename, speaker_segments)

