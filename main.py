from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import speech_recognition as sr
import shutil
from pathlib import Path
from pydub import AudioSegment
import os
import tempfile

app = FastAPI()

# Create a temporary directory for file processing
TEMP_DIR = Path(tempfile.gettempdir()) / "speech_recognition"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def convert_to_wav(input_path: str) -> str:
    """Convert audio file to WAV format"""
    output_path = input_path.rsplit('.', 1)[0] + '.wav'
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="wav")
    return output_path

# دالة لتحليل الصوت إلى نص
def recognize_speech(audio_path: str):
    recognizer = sr.Recognizer()
    
    try:
        # Convert to WAV if the file is not already WAV
        if not audio_path.lower().endswith('.wav'):
            wav_path = convert_to_wav(audio_path)
        else:
            wav_path = audio_path

        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)  # قراءة الصوت من الملف
            try:
                text = recognizer.recognize_google(audio_data, language="ar-EG")  # تحليل النص بالعربية
                print("دا الكلام اللى جاى من الصوت بعد تحليله ")
                return text
            except sr.UnknownValueError:
                return "تعذر التعرف على الصوت"
            except sr.RequestError:
                return "حدث خطأ في الاتصال بـ Google Speech API"
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return "حدث خطأ أثناء معالجة الملف الصوتي"
    finally:
        # Clean up the temporary WAV file if it was created
        if wav_path != audio_path and os.path.exists(wav_path):
            os.remove(wav_path)

@app.post("/process_audio/")
async def process_audio(file: UploadFile = File(...), expected_text: str = Form(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Generate a unique filename
    temp_file = TEMP_DIR / f"{os.urandom(8).hex()}_{file.filename}"
    
    try:
        # Save the uploaded file
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the audio
        recognized_text = recognize_speech(str(temp_file))

        # Compare the recognized text with expected text
        is_match = recognized_text.strip() == expected_text.strip()

        return {
            "recognized_text": recognized_text,
            "expected_text": expected_text,
            "match": is_match
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)


