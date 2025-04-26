import subprocess
import os
import shutil

def compile_pdf(tex_file):
    subprocess.run(["pdflatex", tex_file], check=True)

# Generate LaTeX pdf from segments
def segments_to_pdf(filename, speaker_segments):
    tex_filename = f"{filename}.tex"
    with open(tex_filename, "w") as f:
        f.write(r"""\documentclass[12pt]{article}
                       \usepackage[utf8]{inputenc}
                       \usepackage{geometry}
                       \geometry{margin=1in}
                       \title{Transcript}
                       \begin{document}
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

