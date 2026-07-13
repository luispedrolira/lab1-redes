"""
Simulación de un canal con ruido para comparar la robustez de Morse y Baudot.

Cada símbolo transmitido (punto/raya en Morse, bit en Baudot) se altera con probabilidad p:
la mitad de las veces se invierte (punto<->raya, 0<->1) y la otra mitad se pierde.
En Morse, además, cada pausa entre letras se pierde con probabilidad p (las letras se juntan).

    python canal_ruidoso.py              # 2000 mensajes por cada probabilidad
    python canal_ruidoso.py --n 5000 --semilla 7
"""
import argparse
import os
import random
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'herramientas'))
sys.path.insert(0, AQUI)
import codificador as cod  # noqa: E402
from practica import MENSAJES  # noqa: E402


def canal_morse(texto, p, rng):
    salida = []
    for s in cod.codificar_morse(texto):
        r = rng.random()
        if s in '.-':
            if r < p / 2:
                s = '-' if s == '.' else '.'
            elif r < p:
                s = ''
        elif s == ' ' and r < p:
            s = ''
        salida.append(s)
    return cod.decodificar_morse(''.join(salida))


def canal_baudot(texto, p, rng, perder_bits=True):
    salida = []
    for b in cod.codificar_baudot(texto).replace(' ', ''):
        r = rng.random()
        if r < p / 2:
            b = '1' if b == '0' else '0'
        elif r < p:
            # Bit perdido: desfasa todos los grupos de 5 bits siguientes.
            # Sin pérdida, el error se cuenta como otra inversión.
            b = '' if perder_bits else ('1' if b == '0' else '0')
        salida.append(b)
    return cod.decodificar_baudot(''.join(salida))


def cer(canal, mensajes, p, n, rng):
    errores = caracteres = perfectos = 0
    for _ in range(n):
        m = rng.choice(mensajes)
        recibido = canal(m, p, rng)
        e = cod.distancia(cod.normalizar(m), cod.normalizar(recibido))
        errores += e
        caracteres += len(m)
        perfectos += e == 0
    return errores / caracteres, perfectos / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=2000)
    ap.add_argument('--semilla', type=int, default=2026)
    args = ap.parse_args()
    rng = random.Random(args.semilla)
    mensajes = MENSAJES['3.1'] + MENSAJES['3.2']

    simbolos_morse = sum(sum(c in '.-' for c in cod.codificar_morse(m)) for m in mensajes) / len(mensajes)
    bits_baudot = sum(len(cod.codificar_baudot(m).replace(' ', '')) for m in mensajes) / len(mensajes)
    print(f'Símbolos promedio por mensaje: Morse {simbolos_morse:.1f} (puntos/rayas), Baudot {bits_baudot:.1f} bits\n')

    canales = [
        ('Morse', canal_morse),
        ('Baudot', canal_baudot),
        ('Baudot sin pérdida de bits', lambda t, p, r: canal_baudot(t, p, r, perder_bits=False)),
    ]
    print('| p (error por símbolo) | ' + ' | '.join(f'{nombre}: CER / msj. perfectos' for nombre, _ in canales) + ' |')
    print('|---' * (len(canales) + 1) + '|')
    for p in (0.01, 0.02, 0.05, 0.10):
        celdas = []
        for _, canal in canales:
            tasa, ok = cer(canal, mensajes, p, args.n, rng)
            celdas.append(f'{tasa:6.1%} / {ok:6.1%}')
        print(f'| {p:.0%} | ' + ' | '.join(celdas) + ' |')


if __name__ == '__main__':
    main()
