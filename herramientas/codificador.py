"""
Codificador / decodificador de Morse y Baudot (código original, patente 1888)
y medidor de errores para la Parte 1 del Laboratorio 1 de Redes.

Uso:
    python codificador.py morse  "hola como estas"        # codificar
    python codificador.py baudot "hola como estas"
    python codificador.py morse  -d ".... --- .-.. .- / -.-. --- -- ---"   # decodificar
    python codificador.py baudot -d "01011 11100 11011 10000"
    python codificador.py errores registro.csv            # resumen de errores

Convenciones de transmisión:
    Morse : '.' punto, '-' raya, espacio entre letras, ' / ' entre palabras.
    Baudot: grupos de 5 bits (columnas I-V de la Imagen 2), separados por espacio.
            El espacio entre palabras se envía como el blanco de letras '*' = 00001.
"""
import csv
import sys
import unicodedata

MORSE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
}

# Código de Baudot original (patente US 388,244, Fig. 24). Columnas I II III IV V,
# '1' = '+' y '0' = '-' en la tabla de la patente.
BAUDOT = {
    'A': '10000', 'E': '01000', 'É': '11000', 'I': '01100', 'O': '11100',
    'U': '10100', 'Y': '00100',
    'B': '00110', 'C': '10110', 'D': '11110', 'F': '01110', 'G': '01010',
    'H': '11010', 'J': '10010', 'K': '10011', 'L': '11011', 'M': '01011',
    'N': '01111', 'P': '11111', 'Q': '10111', 'R': '00111', 'S': '00101',
    'T': '10101', 'V': '11101', 'W': '01101', 'X': '01001', 'Z': '11001',
    ' ': '00001',
}

MORSE_INV = {v: k for k, v in MORSE.items()}
BAUDOT_INV = {v: k for k, v in BAUDOT.items()}


def normalizar(texto, conservar_e_aguda=False):
    """Mayúsculas y sin tildes (Ñ -> N). Opcionalmente conserva la É de Baudot."""
    salida = []
    for c in texto.upper():
        if conservar_e_aguda and c == 'É':
            salida.append(c)
            continue
        base = unicodedata.normalize('NFD', c)[0]
        salida.append(base)
    return ' '.join(''.join(salida).split())


def codificar_morse(texto):
    palabras = normalizar(texto).split(' ')
    return ' / '.join(' '.join(MORSE.get(c, '?') for c in p) for p in palabras)


def decodificar_morse(codigo):
    palabras = codigo.strip().split('/')
    return ' '.join(''.join(MORSE_INV.get(s, '?') for s in p.split()) for p in palabras)


def codificar_baudot(texto):
    return ' '.join(BAUDOT.get(c, '?????') for c in normalizar(texto, conservar_e_aguda=True))


def decodificar_baudot(codigo):
    bits = ''.join(ch for ch in codigo if ch in '01')
    grupos = [bits[i:i + 5] for i in range(0, len(bits), 5)]
    return ''.join(BAUDOT_INV.get(g, '?') for g in grupos)


def distancia(a, b):
    """Distancia de Levenshtein (inserciones, eliminaciones y sustituciones)."""
    previa = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        actual = [i]
        for j, cb in enumerate(b, 1):
            actual.append(min(previa[j] + 1, actual[j - 1] + 1, previa[j - 1] + (ca != cb)))
        previa = actual
    return previa[-1]


def resumen_errores(ruta):
    """
    Lee un CSV con columnas: esquema,parte,emisor,enviado,recibido
    y muestra errores por mensaje y la tasa de error por carácter (CER) por esquema.
    """
    totales = {}
    with open(ruta, newline='', encoding='utf-8') as f:
        filas = list(csv.DictReader(f))
    print(f"{'esquema':8} {'parte':5} {'emisor':12} {'enviado':24} {'recibido':24} {'err':>3} {'CER':>6}")
    for fila in filas:
        enviado = normalizar(fila['enviado'])
        recibido = normalizar(fila['recibido'])
        err = distancia(enviado, recibido)
        cer = err / max(len(enviado), 1)
        clave = (fila['esquema'], fila['parte'])
        t = totales.setdefault(clave, [0, 0, 0, 0])
        t[0] += err
        t[1] += len(enviado)
        t[2] += 1
        t[3] += enviado == recibido
        print(f"{fila['esquema']:8} {fila['parte']:5} {fila['emisor']:12} {enviado:24} {recibido:24} {err:3} {cer:6.1%}")
    print('\nResumen por esquema y parte:')
    print(f"{'esquema':8} {'parte':5} {'mensajes':>8} {'perfectos':>9} {'errores':>7} {'caracteres':>10} {'CER':>6}")
    for (esquema, parte), (err, chars, n, ok) in sorted(totales.items()):
        print(f"{esquema:8} {parte:5} {n:8} {ok:9} {err:7} {chars:10} {err / max(chars, 1):6.1%}")


def main(args):
    if len(args) >= 2 and args[0] == 'errores':
        resumen_errores(args[1])
    elif len(args) >= 3 and args[1] == '-d':
        fn = decodificar_morse if args[0] == 'morse' else decodificar_baudot
        print(fn(' '.join(args[2:])))
    elif len(args) >= 2 and args[0] in ('morse', 'baudot'):
        fn = codificar_morse if args[0] == 'morse' else codificar_baudot
        print(fn(' '.join(args[1:])))
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
