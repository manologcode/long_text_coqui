#!/usr/bin/env python3
"""
Pruebas para la conversión de números a texto en español
"""

from num2words import num2words
import re

def number_to_text_spanish(number: int) -> str:
    """
    Convierte un número entero a su representación en texto en español usando num2words.
    
    Args:
        number (int): Número entero a convertir
        
    Returns:
        str: Representación en texto del número en español
    """
    try:
        return num2words(number, lang='es')
    except Exception as e:
        # Si hay algún error, devolver el número como string
        print(f"Error al convertir número {number} a texto: {e}")
        return str(number)

def convert_numbers_to_text(text: str) -> str:
    """
    Convierte todos los números encontrados en el texto a su representación en español.
    
    Args:
        text (str): Texto que puede contener números
        
    Returns:
        str: Texto con los números convertidos a palabras en español
    """
    def replace_number(match):
        number_str = match.group(0)
        try:
            # Manejar números con comas como separador de miles (ej: 1,000)
            clean_number = number_str.replace(',', '')
            number = int(clean_number)
            return number_to_text_spanish(number)
        except ValueError:
            # Si no se puede convertir, devolver el número original
            return number_str
    
    # Patrón para encontrar números enteros (incluye números con comas)
    pattern = r'\b\d{1,3}(?:,\d{3})*\b|\b\d+\b'
    
    return re.sub(pattern, replace_number, text)

def test_number_conversion():
    """Función de prueba para verificar la conversión de números"""
    
    print("=== PRUEBAS DE CONVERSIÓN DE NÚMEROS A TEXTO ===\n")
    
    # Casos de prueba
    test_cases = [
        ("Tengo 5 años", "Tengo cinco años"),
        ("Necesito 100 pesos", "Necesito cien pesos"),
        ("El año 2023 fue bueno", "El año dos mil veintitrés fue bueno"),
        ("Hay 1,500 personas", "Hay mil quinientos personas"),
        ("Mi número es 42", "Mi número es cuarenta y dos"),
        ("Cuesta 999 euros", "Cuesta novecientos noventa y nueve euros"),
        ("El 1 de enero", "El uno de enero"),
        ("Capítulo 7 del libro", "Capítulo siete del libro"),
        ("Página 234 de 500", "Página doscientos treinta y cuatro de quinientos"),
        ("Son las 3:30", "Son las tres:treinta"),
    ]
    
    print("Pruebas individuales de números:")
    for i in [0, 1, 5, 13, 21, 42, 100, 101, 999, 1000, 1500, 2023]:
        converted = number_to_text_spanish(i)
        print(f"{i} -> {converted}")
    
    print("\nPruebas de conversión en texto:")
    for original, expected in test_cases:
        result = convert_numbers_to_text(original)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{original}' -> '{result}'")
        if result != expected:
            print(f"   Esperado: '{expected}'")
    
    print("\nPrueba con texto complejo:")
    complex_text = """En el año 2024, una empresa vendió 1,250 productos por un valor de 50,000 euros. 
    El CEO, de 45 años, anunció que esperan triplicar las ventas en los próximos 3 años.
    La sede principal tiene 8 pisos y 150 empleados trabajan en el edificio número 42."""
    
    converted_complex = convert_numbers_to_text(complex_text)
    print(f"Original: {complex_text}")
    print(f"Convertido: {converted_complex}")

if __name__ == "__main__":
    test_number_conversion()