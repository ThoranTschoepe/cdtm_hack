import subprocess
import os

def convert_webm_to_wav(input_path: str) -> str:
    """
    Converts a .webm file to .wav using ffmpeg.
    Returns the path to the output .wav file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    output_path = input_path.rsplit('.', 1)[0] + '.wav'

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, output_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg conversion failed: {e}")

    return output_path
