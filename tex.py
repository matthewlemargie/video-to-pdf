import whisper
import ffmpeg
import os
import subprocess
import torch
import re

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

# Extract audio from video
def extract_audio(video_path, audio_path):
    ffmpeg.input(video_path).output(audio_path, ac=1, ar='16000').run(overwrite_output=True)

# Transcribe audio with Whisper using GPU
def transcribe_audio_whisper(audio_path):
    print(f"[•] Loading Whisper on {'CUDA' if torch.cuda.is_available() else 'CPU'}...")
    model = whisper.load_model("base", device="cuda" if torch.cuda.is_available() else "cpu")
    result = model.transcribe(audio_path)
    return result['segments']

# Format timestamp
def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02}:{mins:02}:{secs:02}"

# Create LaTeX transcript with clean breaks every ~30s, not mid-sentence
def create_latex_file(whisper_segments, tex_filename, chunk_duration=30):
    with open(tex_filename, 'w', encoding='utf-8') as tex_file:
        tex_file.write(r"""\documentclass[12pt]{article}
                       \usepackage[utf8]{inputenc}
                       \usepackage{geometry}
                       \geometry{margin=1in}
                       \title{Transcript}
                       \begin{document}
                       \maketitle
                       """)

        current_chunk_start = 0
        chunk_text = ""
        last_timestamp = 0

        for segment in whisper_segments:
            start = segment['start']
            text = segment['text'].strip()
            chunk_text += text + " "

            # If past time threshold AND sentence seems to end
            if (start - current_chunk_start) >= chunk_duration:
                if re.search(r'[.!?]"?\s*$', text):  # Looks for sentence-ending punctuation
                    timestamp = format_time(current_chunk_start)
                    tex_file.write(r"\textbf{" + timestamp + "} " + chunk_text.strip() + r"\par" + "\n\n")
                    current_chunk_start = start
                    chunk_text = ""

        # Final flush
        if chunk_text:
            timestamp = format_time(current_chunk_start)
            tex_file.write(r"\textbf{" + timestamp + "} " + chunk_text.strip() + r"\par" + "\n")

        tex_file.write(r"\end{document}")

# Compile .tex to PDF
def compile_pdf(tex_file):
    subprocess.run(["pdflatex", tex_file], check=True)

# Main process pipeline
def process_video(video_path):
    audio_path = "extracted_audio.wav"
    tex_path = "output.tex"

    print("[1] Extracting audio...")
    extract_audio(video_path, audio_path)

    print("[2] Transcribing with Whisper...")
    whisper_segments = transcribe_audio_whisper(audio_path)

    print("[3] Creating LaTeX transcript...")
    create_latex_file(whisper_segments, tex_path)

    print("[4] Compiling PDF...")
    compile_pdf(tex_path)

    os.remove(audio_path)
    print(f"[✓] Done! PDF transcript generated.")

# Example run
video_path = "../ai-video-editor/inputvids/rhettandlink.mp4"
process_video(video_path)

