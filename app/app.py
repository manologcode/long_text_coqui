from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las origins en desarrollo. En producción, limita esto.
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todos los headers
)

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
    AUDIO_TAGS_DIR = "effects"  
    SERVER_URL = os.getenv("SERVER_URL_VOICE_XTTS", "http://192.168.1.69:8820")
    SPEAKERS_JSON_PATH = 'studio_speakers.json'
    MAX_CHUNK_SIZE = 230

# Crear directorios si no existen
os.makedirs(Config.AUDIO_FILES_DIR, exist_ok=True)
os.makedirs(Config.TEMP_DIR, exist_ok=True)
os.makedirs(Config.AUDIO_TAGS_DIR, exist_ok=True)

tasks_status = {}

def extract_tags_and_clean_text(text: str):
    """
    Extrae las etiquetas del texto y devuelve una lista de elementos ordenados.
    Cada elemento es un diccionario con 'type' ('text' o 'tag') y 'content'.
    """
    # Patrón para encontrar etiquetas como <click2>, <silence1>, etc.
    tag_pattern = r'<([^>]+)>'
    
    elements = []
    last_end = 0
    
    for match in re.finditer(tag_pattern, text):
        # Agregar texto antes de la etiqueta
        if match.start() > last_end:
            text_content = text[last_end:match.start()].strip()
            if text_content:
                elements.append({'type': 'text', 'content': text_content})
        
        # Agregar la etiqueta
        tag_name = match.group(1)
        elements.append({'type': 'tag', 'content': tag_name})
        
        last_end = match.end()
    
    # Agregar texto restante después de la última etiqueta
    if last_end < len(text):
        text_content = text[last_end:].strip()
        if text_content:
            elements.append({'type': 'text', 'content': text_content})
    
    return elements

def split_text_by_punctuation(text: str, max_length: int = Config.MAX_CHUNK_SIZE):
    """Divide el texto por puntuación manteniendo el tamaño máximo."""
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

def get_tag_audio_file(tag_name: str):
    """Obtiene la ruta del archivo de audio para una etiqueta específica."""
    tag_file = os.path.join(Config.AUDIO_TAGS_DIR, f"{tag_name}.mp3")
    if os.path.exists(tag_file):
        return tag_file
    else:
        logger.warning(f"Archivo de etiqueta no encontrado: {tag_file}")
        return None

def merge_audio_elements(audio_files: list, output_filename: str):
    """Une múltiples archivos de audio en uno solo."""
    try:
        if not audio_files:
            raise Exception("No hay archivos de audio para unir")
        
        # Filtrar archivos que no existen
        existing_files = [f for f in audio_files if f and os.path.exists(f)]
        
        if not existing_files:
            raise Exception("No se encontraron archivos de audio válidos")
        
        combined = AudioSegment.from_file(existing_files[0])
        for archivo in existing_files[1:]:
            sound = AudioSegment.from_file(archivo)
            combined += sound
        
        combined.export(output_filename, format="mp3", bitrate="256k")
        return output_filename
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al unir archivos: {str(e)}")

async def process_text_to_speech(text: str, voice: str, lang: str, job_id: str):
    """Procesa el texto dividiéndolo si es necesario y manejando las etiquetas."""
    try:
        tasks_status[job_id]["status"] = "processing"
        
        # Extraer etiquetas y limpiar texto
        elements = extract_tags_and_clean_text(text)
        
        if not elements:
            raise Exception("No hay contenido para procesar")
        
        audio_files = []
        text_chunk_counter = 0
        
        for element in elements:
            if element['type'] == 'text':
                # Procesar texto
                text_content = element['content']
                
                if len(text_content) > Config.MAX_CHUNK_SIZE:
                    # Dividir texto largo en chunks
                    chunks = split_text_by_punctuation(text_content)
                    for chunk in chunks:
                        if chunk.strip():
                            audio_file = process_text_chunk(chunk, voice, lang, text_chunk_counter, job_id)
                            if audio_file:
                                audio_files.append(audio_file)
                            text_chunk_counter += 1
                else:
                    # Procesar como un solo chunk
                    if text_content.strip():
                        audio_file = process_text_chunk(text_content, voice, lang, text_chunk_counter, job_id)
                        if audio_file:
                            audio_files.append(audio_file)
                        text_chunk_counter += 1
            
            elif element['type'] == 'tag':
                # Procesar etiqueta
                tag_name = element['content']
                tag_audio_file = get_tag_audio_file(tag_name)
                if tag_audio_file:
                    audio_files.append(tag_audio_file)
                    logger.info(f"Agregado archivo de etiqueta: {tag_name}")
                else:
                    logger.warning(f"Archivo de etiqueta no encontrado: {tag_name}")
        
        if not audio_files:
            raise Exception("No se generaron archivos de audio")

        output_filename = f"{Config.AUDIO_FILES_DIR}/{job_id}_complete.mp3"
        merge_audio_elements(audio_files, output_filename)
        
        tasks_status[job_id].update({
            "status": "completed",
            "audio_url": f"/audio/{job_id}",
            "output_file": output_filename
        })
        
        # Limpiar archivos temporales (solo los generados, no los de etiquetas)
        for file in audio_files:
            if file and file.startswith(Config.TEMP_DIR) and os.path.exists(file):
                os.remove(file)
                
    except Exception as e:
        logger.error(f"Error en trabajo {job_id}: {str(e)}")
        tasks_status[job_id]["status"] = "failed"
        tasks_status[job_id]["error_message"] = str(e)

@app.get("/")
async def read_root():
    return RedirectResponse(url="/docs", status_code=302)

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