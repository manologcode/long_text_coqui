# Long Text Coqui

**Long Text Coqui** es un artefacto que permite sintetizar texto largo a voz utilizando el proyecto Coqui. Coqui es una excelente herramienta para convertir texto a voz en múltiples idiomas, pero tiene la limitación de procesar solo textos de hasta 239 caracteres. Este proyecto soluciona ese inconveniente al recibir textos largos, fragmentarlos, generar audios parciales y finalmente unirlos para crear un audio completo.

## Características

- Convierte textos largos a voz.
- Soporta múltiples idiomas.
- Utiliza Docker para facilitar la implementación y ejecución.

## Servicios externos de dependencia

En general, en mi servidor self-hosted, todos los servicios corren en Docker. Esta aplicación depende de que tengas ejecutándose servicios como los siguientes ejemplos:
   - Generador de texto a audio: [lxtts-streaming-server GitHub](https://github.com/manologcode/xtts-streaming-server)

## Instrucciones de Uso

Para llamarlos el archivo test proporciona un ejemplo de como usarlo con python 

### Ejecutar con Docker

1. **Correr el contenedor Docker:**

   ```bash
    docker run -d \
    --name long_text_coqui \
    -v ./:/app/audio_files \
    -p 5008:5008 \
    -e SERVER_URL_COQUI_XTTS=http://192.168.1.69:8820 \
    manologcode/long_text_coqui

   ```

   Asegúrate de reemplazar `http://192.168.1.69:8820` con la URL o nombre del servicio de tu servidor Coqui XTTS.

2. **Probar la conversión de texto a voz:**

   Una vez que el contenedor esté en marcha, puedes probar la conversión de texto a voz ejecutando el siguiente comando:

   ```bash
   docker exec long_text_coqui python test.py "esto es un texto de prueba para que lo leas"
   ```

   Esto debería generar un audio con el texto proporcionado.

## extras

  Se ha añadido para poder forzar efectos y silencios añadiendo las etiquetas <silence1>, <click1> <click2> a modo. de experimento para la locución de noticias 



