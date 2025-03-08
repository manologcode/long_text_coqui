import requests
import time
import sys

BASE_URL = "http://localhost:5008"  # Cambia esto si la API está en otro servidor

def text_to_speech(text, voice="Xavier Hayasaka", lang="es"):
    """Envía una solicitud a la API para convertir texto a voz."""
    url = f"{BASE_URL}/text-to-speech"
    payload = {"text": text, "voice": voice, "lang": lang}

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        job_id = response.json()["job_id"]
        print(f"Tarea enviada con éxito. Job ID: {job_id}")
        return job_id
    else:
        print(f"Error: {response.text}")
        return None

def check_status(job_id):
    """Consulta el estado de la tarea de conversión."""
    url = f"{BASE_URL}/status/{job_id}"
    while True:
        response = requests.get(url)
        data = response.json()
        print(f"Estado actual: {data['status']}")

        if data["status"] == "completed":
            print(f"Audio listo en: {BASE_URL}{data['audio_url']}")
            return f"{BASE_URL}{data['audio_url']}"
        elif data["status"] == "failed":
            print(f"Error en la conversión: {data.get('error_message', 'Desconocido')}")
            return None
        
        time.sleep(2)  # Esperar antes de consultar nuevamente

def download_audio(audio_url, output_file="output.mp3"):
    """Descarga el archivo de audio generado."""
    response = requests.get(audio_url)
    if response.status_code == 200:
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"Audio descargado como {output_file}")
    else:
        print(f"Error al descargar audio: {response.text}")


if __name__ == "__main__":
    default_text = "En un lugar de la Mancha, de cuyo nombre no quiero acordarme..."

    # Si se pasa un argumento por línea de comandos, usarlo como texto
    if len(sys.argv) > 1:
        input_text = " ".join(sys.argv[1:])
    else:
        input_text = default_text

    job_id = text_to_speech(input_text)

    if job_id:
        audio_url = check_status(job_id)
        if audio_url:
            download_audio(audio_url)