"""
Práctica de recepción (partes 3.1 y 3.2) para hacer el laboratorio de forma individual.

La computadora hace de emisor: genera el mensaje como audio y lo reproduce; uno lo
decodifica de oído y escribe lo que entendió. Cada intento se guarda en
herramientas/registro.csv para luego calcular errores con codificador.py.

    python practica.py morse              # 3.1 en vivo: se puede pedir "repite"
    python practica.py baudot
    python practica.py morse --parte 3.2  # 3.2 empaquetada: audio único, sin repetir

Audio:
    Morse : tono de 700 Hz; punto = 1 unidad, raya = 3 unidades (--wpm controla la velocidad).
    Baudot: cada bit es un tono de --bit-ms milisegundos, 1 = 880 Hz (agudo), 0 = 440 Hz (grave),
            con una pausa larga entre grupos de 5 bits.
Los .wav quedan en simulacion/audios/ para poder enviarlos como nota de voz (3.2).
"""
import argparse
import csv
import math
import os
import random
import struct
import sys
import time
import wave

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'herramientas'))
import codificador as cod  # noqa: E402

FS = 8000
REGISTRO = os.path.join(AQUI, '..', 'herramientas', 'registro.csv')
CAMPOS = ['esquema', 'parte', 'emisor', 'enviado', 'recibido', 'repeticiones', 'segundos']

MENSAJES = {
    '3.1': ['HOLA COMO ESTAS', 'REDES DE DATOS', 'BUENAS NOCHES', 'PAQUETE PERDIDO',
            'TELEGRAFO VIEJO', 'CODIGO BINARIO', 'MENSAJE URGENTE', 'VALLE DE GUATEMALA'],
    '3.2': ['NOTA DE VOZ', 'CONMUTADOR LISTO', 'ENLACE CAIDO', 'ROUTER OCUPADO',
            'LATENCIA ALTA', 'CAPA DE ENLACE', 'FIN DEL MENSAJE', 'SEGUNDO SEMESTRE'],
}


def tono(freq, ms):
    n = int(FS * ms / 1000)
    rampa = min(80, n // 4)  # evita "clics" al inicio y fin del tono
    return [int(12000 * math.sin(2 * math.pi * freq * i / FS) * min(1, i / rampa, (n - i) / rampa))
            for i in range(n)]


def silencio(ms):
    return [0] * int(FS * ms / 1000)


def audio_morse(texto, wpm, farnsworth):
    u = 1200 / wpm
    g = u * farnsworth  # espaciado extendido entre letras y palabras (método Farnsworth)
    muestras = []
    for palabra in cod.codificar_morse(texto).split(' / '):
        for letra in palabra.split():
            for s in letra:
                muestras += tono(700, u if s == '.' else 3 * u) + silencio(u)
            muestras += silencio(3 * g)
        muestras += silencio(4 * g)
    return muestras


def audio_baudot(texto, bit_ms, pausa_ms):
    muestras = []
    for grupo in cod.codificar_baudot(texto).split():
        for b in grupo:
            muestras += tono(880 if b == '1' else 440, bit_ms) + silencio(bit_ms / 3)
        muestras += silencio(pausa_ms)
    return muestras


def guardar_wav(muestras, ruta):
    with wave.open(ruta, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(FS)
        w.writeframes(struct.pack('<%dh' % len(muestras), *muestras))


def reproducir(ruta):
    try:
        import winsound
        winsound.PlaySound(ruta, winsound.SND_FILENAME)
    except ImportError:
        input(f'Reproduzca {ruta} y presione Enter...')


def registrar(fila):
    nuevo = not os.path.exists(REGISTRO)
    with open(REGISTRO, 'a', newline='', encoding='utf-8') as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        if nuevo:
            escritor.writeheader()
        escritor.writerow(fila)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('esquema', choices=['morse', 'baudot'])
    p.add_argument('--parte', choices=['3.1', '3.2'], default='3.1')
    p.add_argument('-n', type=int, default=3, help='cantidad de mensajes (mínimo 3)')
    p.add_argument('--wpm', type=float, default=10, help='palabras por minuto en Morse')
    p.add_argument('--farnsworth', type=float, default=2, help='factor de pausa entre letras en Morse')
    p.add_argument('--bit-ms', type=float, default=250, help='duración de cada bit en Baudot')
    p.add_argument('--pausa-ms', type=float, default=900, help='pausa entre caracteres en Baudot')
    args = p.parse_args()

    carpeta = os.path.join(AQUI, 'audios')
    os.makedirs(carpeta, exist_ok=True)
    mensajes = random.sample(MENSAJES[args.parte], min(args.n, len(MENSAJES[args.parte])))
    en_vivo = args.parte == '3.1'

    print(f'Esquema: {args.esquema} · Parte {args.parte} · {len(mensajes)} mensajes')
    print('Tenga a mano la tabla del código y papel para anotar los símbolos.')
    if args.esquema == 'morse':
        print('Puede responder con el texto o con los símbolos: letras separadas por espacio y palabras por " / ",')
        print('por ejemplo  .... --- .-.. .- / -- ..- -. -.. ---\n')
    else:
        print('Puede responder con el texto o con los bits (grupos de 5, el espacio entre palabras es 00001),')
        print('por ejemplo  11010 11100 11011 10000\n')
    for i, mensaje in enumerate(mensajes, 1):
        if args.esquema == 'morse':
            muestras = audio_morse(mensaje, args.wpm, args.farnsworth)
        else:
            muestras = audio_baudot(mensaje, args.bit_ms, args.pausa_ms)
        ruta = os.path.join(carpeta, f'{args.parte}_{args.esquema}_{i}.wav')
        guardar_wav(muestras, ruta)

        input(f'[{i}/{len(mensajes)}] Enter para recibir el mensaje ({len(muestras) / FS:.0f} s de audio)...')
        inicio = time.time()
        repeticiones = 0
        reproducir(ruta)
        while en_vivo and input('  "r" + Enter para pedir que se repita, Enter para seguir: ').strip().lower() == 'r':
            repeticiones += 1
            reproducir(ruta)
        recibido = input('  Mensaje decodificado (o los símbolos tal como los escuchó): ')
        segundos = round(time.time() - inicio, 1)
        simbolos = '.-' if args.esquema == 'morse' else '01'
        if recibido.strip() and set(recibido.replace(' ', '').replace('/', '')) <= set(simbolos):
            recibido = (cod.decodificar_morse if args.esquema == 'morse' else cod.decodificar_baudot)(recibido)
            print(f'  Símbolos traducidos con la tabla: {recibido}')

        errores = cod.distancia(cod.normalizar(mensaje), cod.normalizar(recibido))
        print(f'  Enviado: {mensaje} | Recibido: {cod.normalizar(recibido)} | errores: {errores} | {segundos} s\n')
        registrar({'esquema': args.esquema, 'parte': args.parte, 'emisor': 'Computadora',
                   'enviado': mensaje, 'recibido': recibido, 'repeticiones': repeticiones,
                   'segundos': segundos})

    print(f'Resultados agregados a {os.path.normpath(REGISTRO)}')
    print('Resumen: python herramientas/codificador.py errores herramientas/registro.csv')


if __name__ == '__main__':
    main()
