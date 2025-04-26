# Video-to-PDF Converter

This is a script I wrote that takes a video as input and performs speaker diarization and
speech-to-text transcription and combines the results to create a LaTeX document with the
transcription of the video and then compile into a PDF.

## How to Use

Create conda environment with:

`conda env create -f environment.yml`

Then run main.py on a video specifying number of speakers:

`python main.py --video-path path/to/video.mp4 --n-speakers 2`

The output pdf can be found in the output folder

The whisper segments are cached in case the script has to be repeated to save time

