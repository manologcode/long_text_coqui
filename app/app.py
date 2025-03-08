from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import os
import json
import uuid
import re
import base64
from pydub import AudioSegment
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Text-to-Speech API")

class TextToSpeechRequest(BaseModel):
    text: str
    voice: str = "Xavier Hayasaka"
    lang: str = "es"

class TextToSpeechResponse(BaseModel):
    audio_url: str
    job_id: str
    status: str

class Config:
    AUDIO_FILES_DIR = "audio_files"
    TEMP_DIR = "temp_audio"
    SERVER_URL = os.getenv("SERVER_URL_VOICE_XTTS", "http://192.168.1.69:8820")
    SPEAKERS_JSON_PATH = 'studio_speakers.json'
    MAX_CHUNK_SIZE = 230

# Crear directorios si no existen
os.makedirs(Config.AUDIO_FILES_DIR, exist_ok=True)
os.makedirs(Config.TEMP_DIR, exist_ok=True)

tasks_status = {}

def split_text_by_punctuation(text: str, max_length: int = Config.MAX_CHUNK_SIZE):
    signos_puntuacion = re.compile(r'([.,;:!?])')
    palabras = signos_puntuacion.split(text)
    trozos = []
    actual = ""
    
    for i in range(0, len(palabras), 2):
        segmento = palabras[i] + (palabras[i+1] if i+1 < len(palabras) else "")
        
        if len(actual) + len(segmento) <= max_length:
            actual += segmento
        else:
            if actual:
                trozos.append(actual.strip())
            actual = segmento
    
    if actual:
        trozos.append(actual.strip())
    
    return trozos

def process_text_chunk(text_chunk: str, voice: str, lang: str, chunk_id: int, job_id: str):
    """Procesa un fragmento de texto y lo convierte en audio."""
    try:
        with open(Config.SPEAKERS_JSON_PATH, 'r') as archivo:
            studio_speakers = json.load(archivo)
        
        speaker_embeddings = studio_speakers.get(voice)
        if not speaker_embeddings:
            raise ValueError(f"Voz {voice} no encontrada en el archivo JSON")
        
        payload = {
            "text": text_chunk,
            "language": lang,
            "speaker_embedding": speaker_embeddings["speaker_embedding"],
            "gpt_cond_latent": speaker_embeddings["gpt_cond_latent"]
        }
        
        chunk_filename = f"{Config.TEMP_DIR}/{job_id}_{chunk_id}.mp3"
        response = requests.post(f"{Config.SERVER_URL}/tts", json=payload)

        if response.status_code != 200:
            raise Exception(f"Error en la API TTS: {response.text}")

        with open(chunk_filename, "wb") as f:
            f.write(base64.b64decode(response.content))
        
        return chunk_filename
    except Exception as e:
        logger.error(f"Error en fragmento {chunk_id}: {str(e)}")
        tasks_status[job_id]["errors"].append(f"Error en fragmento {chunk_id}: {str(e)}")
        return None

def merge_audio_files(filenames: list, output_filename: str):
    """Une múltiples archivos de audio en uno solo."""
    try:
        combined = AudioSegment.from_file(filenames[0])
        for archivo in filenames[1:]:
            sound = AudioSegment.from_file(archivo)
            combined += sound
        combined.export(output_filename, format="mp3", bitrate="256k")
        return output_filename
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al unir archivos: {str(e)}")

async def process_text_to_speech(text: str, voice: str, lang: str, job_id: str):
    """Procesa el texto dividiéndolo si es necesario."""
    try:
        tasks_status[job_id]["status"] = "processing"
        chunks = split_text_by_punctuation(text) if len(text) > Config.MAX_CHUNK_SIZE else [text]
        path_files = [process_text_chunk(chunk, voice, lang, i, job_id) for i, chunk in enumerate(chunks)]
        path_files = [p for p in path_files if p]
        
        if not path_files:
            raise Exception("No se generaron archivos de audio")

        output_filename = f"{Config.AUDIO_FILES_DIR}/{job_id}_complete.mp3"
        merge_audio_files(path_files, output_filename)
        
        tasks_status[job_id].update({
            "status": "completed",
            "audio_url": f"/audio/{job_id}",
            "output_file": output_filename
        })
        
        for file in path_files:
            os.remove(file)
    except Exception as e:
        logger.error(f"Error en trabajo {job_id}: {str(e)}")
        tasks_status[job_id]["status"] = "failed"
        tasks_status[job_id]["error_message"] = str(e)

@app.post("/text-to-speech", response_model=TextToSpeechResponse)
async def text_to_speech(request: TextToSpeechRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    tasks_status[job_id] = {"status": "queued", "errors": [], "output_file": None, "audio_url": None}
    background_tasks.add_task(process_text_to_speech, request.text, request.voice, request.lang, job_id)
    return TextToSpeechResponse(job_id=job_id, status="queued", audio_url=f"/status/{job_id}")

@app.get("/status/{job_id}", response_model=dict)
def get_job_status(job_id: str):
    if job_id not in tasks_status:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tasks_status[job_id]

@app.get("/audio/{job_id}")
async def get_audio(job_id: str):
    if job_id not in tasks_status:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    if tasks_status[job_id]["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Audio aún no listo. Estado: {tasks_status[job_id]['status']}")
    output_file = tasks_status[job_id]["output_file"]
    if not output_file or not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(path=output_file, media_type="audio/mpeg", filename=f"audio_{job_id}.mp3")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
