import torch
import whisper
from resemblyzer.hparams import sampling_rate
import numpy as np
import os
import time
import ffmpeg
import subprocess
import tempfile
import argparse
import json
import shutil
from pathlib import Path

from diarize import diarize
from transcribe import assign_speakers_to_whisper, merge_consecutive_speaker_segments
from utils import compile_pdf, convert_to_serializable

parser = argparse.ArgumentParser(description="AI-video-editor")
parser.add_argument("--video-path", type=str, default="", help="Path to video to be edited")
parser.add_argument("--n-speakers", type=int, default=2, help="number of speakers in the video")

args = parser.parse_args()

# Generate LaTeX pdf from segments
def segments_to_pdf(filename, speaker_segments):
    tex_filename = f"{filename}.tex"
    with open(tex_filename, "w") as f:
        f.write(r"""\documentclass[12pt]{article}
                \usepackage[margin=1in]{geometry}
                \usepackage{parskip}
                \usepackage{titlesec}
                \usepackage{lmodern}
                \titleformat{\section}{\normalfont\Large\bfseries}{}{0em}{}
                \renewcommand{\familydefault}{\sfdefault}
                \begin{document}
                \title{Video Transcript}
                \author{}
                \date{}
                \maketitle
                """)
        for seg in speaker_segments:
            f.write(f"\\section*{{{seg['speaker']}}}\n")
            f.write(seg['text'].replace("\n", " ") + "\n\n")
        f.write("\\end{document}")

    print(f"LaTeX file saved as {tex_filename}")
    compile_pdf(tex_filename)
    shutil.move(f"{filename}.pdf", os.path.join("output", f"{filename}.pdf"))
    os.remove(f"{filename}.tex")
    os.remove(f"{filename}.log")
    os.remove(f"{filename}.aux")

# Paths
video_path = args.video_path
filename = Path(video_path).stem

segments = diarize(video_path, n_speakers=args.n_speakers)

# Transcribe with Whisper
os.makedirs("cache", exist_ok=True)
segments_path = os.path.join("cache", f"{filename}.json")
if os.path.exists(segments_path):
    with open(segments_path, "r") as f:
        speaker_segments = json.load(f)
else:
    # Extract audio for Whisper and Resemblyzer
    audio_path = "temp_audio.wav"
    ffmpeg.input(video_path).output(audio_path, ac=1, ar=sampling_rate).run(quiet=True, overwrite_output=True)
    model = whisper.load_model("medium", device="cuda" if torch.cuda.is_available() else "cpu")
    result = model.transcribe(audio_path, word_timestamps=True, verbose=True)
    os.remove(audio_path)
    combined = assign_speakers_to_whisper(result["segments"], segments)
    speaker_segments = merge_consecutive_speaker_segments(combined)
    with open(segments_path, "w") as f:
        json.dump(speaker_segments, f, indent=4, default=convert_to_serializable)

segments_to_pdf(filename, speaker_segments)

