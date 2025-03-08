#long_text_coqui

este proyecto es un artefacto que permite sintetizar a voz texto largo con el proyecto de 

el proycto coqui es un estupendo poreyecto para pasa texto a voz en multiples idiomas, el unico incoveniente es que solo permite textow hast 239 caracteres.

Este proyecto es un artefacto que recive texto largos, lo fragmenta genera los audis parciale y finalment lo une para genera un completo



para correrlo con docker 

docker run -d -p 5008:5008 -e SERVER_URL_COQUI_XTTS=http://192.168.1.69:8820 manologcode/long_text_coqui


vez este en marcha para hacer una prueba de texto

docker exec long_text_coqui python test.py "esto es un texto de prueba para que lo leas" 



# Long Text Coqui

**Long Text Coqui** es un artefacto que permite sintetizar texto largo a voz utilizando el proyecto Coqui. Coqui es una excelente herramienta para convertir texto a voz en múltiples idiomas, pero tiene la limitación de procesar solo textos de hasta 239 caracteres. Este proyecto soluciona ese inconveniente al recibir textos largos, fragmentarlos, generar audios parciales y finalmente unirlos para crear un audio completo.

## Características

- Convierte textos largos a voz.
- Soporta múltiples idiomas.
- Utiliza Docker para facilitar la implementación y ejecución.

## Requisitos

- Docker instalado en tu máquina.
- Acceso a una instancia de Coqui XTTS.

## Instrucciones de Uso

Para llamarlos el archivo test proporciona un ejemplo de como usarlo con python 

### Ejecutar con Docker

1. **Correr el contenedor Docker:**

   ```bash
   docker run -d -p 5008:5008 -e SERVER_URL_COQUI_XTTS=http://192.168.1.69:8820 manologcode/long_text_coqui
   ```

   Asegúrate de reemplazar `http://192.168.1.69:8820` con la URL de tu servidor Coqui XTTS.

2. **Probar la conversión de texto a voz:**

   Una vez que el contenedor esté en marcha, puedes probar la conversión de texto a voz ejecutando el siguiente comando:

   ```bash
   docker exec long_text_coqui python test.py "esto es un texto de prueba para que lo leas"
   ```

   Esto debería generar un audio con el texto proporcionado.

