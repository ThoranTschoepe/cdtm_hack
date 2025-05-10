
from openai import OpenAI

client = OpenAI(api_key="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")
import uuid
import os
import io


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def synthesize_speech(text: str, voice: str = "alloy") -> io.BytesIO:
    """Generate speech audio from text using OpenAI and return audio as BytesIO stream."""
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )

    audio_stream = io.BytesIO()
    for chunk in response.iter_bytes():
        audio_stream.write(chunk)
    audio_stream.seek(0)

    return audio_stream


def transcribe_audio_file(upload_file):
    """Transcribe an audio UploadFile using OpenAI Whisper, converting to MP3 if needed."""
    filename = f"{uuid.uuid4()}_{upload_file.filename}"
    path = os.path.join(UPLOAD_FOLDER, filename)

    # Save the uploaded file
    with open(path, "wb") as f:
        f.write(upload_file.file.read())

    # Transcribe using OpenAI
    with open(path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )

    print("Transcript:", response.text)
    print("Language:", response.language)

    return response.text


class FakeUploadFile:
    """Simulates FastAPI's UploadFile for testing"""
    def __init__(self, filepath):
        self.filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            self.file = io.BytesIO(f.read())


if __name__ == "__main__":
    test_audio_path = os.path.join(UPLOAD_FOLDER, "test3_MP3.mp3")  # Replace with your real file name

    if not os.path.exists(test_audio_path):
        print(f"Test audio file not found at {test_audio_path}")
    else:
        fake_upload = FakeUploadFile(test_audio_path)
        try:
            result = transcribe_audio_file(fake_upload)
            print("✅ Transcription result:\n", result)
        except Exception as e:
            print("❌ Error during transcription:", e)
