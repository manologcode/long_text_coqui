#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para la función de limpieza de texto español.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import clean_spanish_text, extract_tags_and_clean_text

def test_clean_spanish_text():
    """Prueba la función de limpieza de texto español."""
    
    # Casos de prueba
    test_cases = [
        {
            "input": "Hola 😀 mundo 🌟 esto es una prueba 🎉",
            "description": "Texto con emojis básicos"
        },
        {
            "input": "¡Hola! ¿Cómo estás? 👋 Me llamo José 🇪🇸",
            "description": "Texto en español con emojis y acentos"
        },
        {
            "input": "Texto con ♠️♣️♦️♥️ símbolos y 🔥⚡️✨ efectos",
            "description": "Texto con símbolos y efectos especiales"
        },
        {
            "input": "Email: usuario@ejemplo.com 📧 Teléfono: +34 666 777 888 📱",
            "description": "Texto con información de contacto y emojis"
        },
        {
            "input": "Precio: 15€ 💰 Descuento: 50% 📊 ¡Oferta especial! 🎁",
            "description": "Texto con precios y emojis"
        },
        {
            "input": "Texto normal sin iconos para verificar que no se altere.",
            "description": "Texto limpio sin modificaciones necesarias"
        },
        {
            "input": "Múltiples    espacios   y\n\n\nsaltos de línea",
            "description": "Texto con espacios y saltos múltiples"
        },
        {
            "input": "Puntuación........ excesiva!!!!!! ¿¿¿verdad???",
            "description": "Texto con puntuación duplicada"
        },
        {
            "input": """\"Comillas curvas\" y 'apostrofes curvos' y guiones –—""",
            "description": "Texto con caracteres tipográficos especiales"
        },
        {
            "input": "<click1> Texto con etiquetas 🎵 y emojis <silence2>",
            "description": "Texto con etiquetas y emojis mezclados"
        }
    ]
    
    print("=== Pruebas de limpieza de texto español ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Prueba {i}: {test_case['description']}")
        print(f"Entrada: {test_case['input']}")
        
        # Limpiar solo el texto
        cleaned = clean_spanish_text(test_case['input'])
        print(f"Limpio:  {cleaned}")
        
        # Probar también con extracción de etiquetas
        if '<' in test_case['input'] and '>' in test_case['input']:
            elements = extract_tags_and_clean_text(test_case['input'])
            print(f"Elementos extraídos: {elements}")
        
        print("-" * 80)
        print()

def test_extract_tags_and_clean():
    """Prueba específicamente la extracción de etiquetas con limpieza."""
    
    test_cases = [
        "Hola 😀 <click1> mundo <silence2> con emojis 🌟",
        "<intro> ¡Bienvenidos! 🎉 Este es un texto <pause1> con múltiples 📱 emojis <outro>",
        "Texto sin etiquetas pero con emojis 😊🎵🔥",
        "<music> Solo etiquetas sin emojis <end>",
        "Texto normal sin nada especial"
    ]
    
    print("=== Pruebas de extracción de etiquetas con limpieza ===\n")
    
    for i, text in enumerate(test_cases, 1):
        print(f"Prueba {i}:")
        print(f"Entrada: {text}")
        elements = extract_tags_and_clean_text(text)
        print(f"Elementos: {elements}")
        
        # Reconstruir texto para verificar
        reconstructed = ""
        for element in elements:
            if element['type'] == 'text':
                reconstructed += element['content']
            else:
                reconstructed += f"<{element['content']}>"
        
        print(f"Reconstruido: {reconstructed}")
        print("-" * 60)
        print()

if __name__ == "__main__":
    test_clean_spanish_text()
    test_extract_tags_and_clean()
    print("✅ Pruebas completadas!")