import subprocess
import numpy as np

def compile_pdf(tex_file):
    subprocess.run(["pdflatex", tex_file], check=True)

def convert_to_serializable(obj):
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)

