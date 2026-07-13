"""
Cliente del conmutador (parte 3.3). Ver el protocolo en conmutador.py.

    python cliente.py A                  # cliente A en Morse
    python cliente.py B --esquema baudot
Luego escribir "<DESTINO> <mensaje>", por ejemplo:  C hola como estas
"""
import argparse
import os
import queue
import socket
import sys
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'herramientas'))
import codificador as cod  # noqa: E402

HOST, PUERTO = '127.0.0.1', 5050


class Cliente:
    confirmaciones = queue.Queue()  # compartida para que la demo sepa cuántos mensajes se entregaron

    def __init__(self, direccion, esquema='morse', host=HOST, puerto=PUERTO, log=print):
        self.dir = direccion.upper()
        self.esquema = esquema
        self.log = log
        self.respuestas = queue.Queue()
        self.ultimo = {}
        self.sock = socket.create_connection((host, puerto))
        threading.Thread(target=self.escuchar, daemon=True).start()
        self.linea(f'HOLA {self.dir}')
        self.respuestas.get(timeout=5)

    def linea(self, texto):
        self.sock.sendall((texto + '\n').encode())

    def codificar(self, texto):
        return cod.codificar_morse(texto) if self.esquema == 'morse' else cod.codificar_baudot(texto)

    def enviar(self, destino, mensaje, intentos=30):
        destino = destino.upper()
        self.ultimo[destino] = mensaje
        paquete = self.codificar(f'{destino} {self.dir} {mensaje}')
        for _ in range(intentos):
            self.linea('S?')
            if self.respuestas.get(timeout=10) == 'LISTO':
                self.linea(f'DATA {self.esquema} {paquete}')
                if self.respuestas.get(timeout=10) == 'RECIBIDO':
                    self.log(f'[{self.dir}] -> S: "{mensaje}" para {destino}: {paquete}')
                    return True
            self.log(f'[{self.dir}] conmutador OCUPADO, se reintenta en 1 s')
            time.sleep(1)
        self.log(f'[{self.dir}] no se pudo enviar "{mensaje}"')
        return False

    def escuchar(self):
        try:
            for linea in self.sock.makefile('r', encoding='utf-8'):
                cmd, _, resto = linea.strip().partition(' ')
                if cmd == 'DATA':
                    esquema, _, codigo = resto.partition(' ')
                    texto = cod.decodificar_morse(codigo) if esquema == 'morse' else cod.decodificar_baudot(codigo)
                    _, origen, mensaje = (texto.split(' ', 2) + ['', ''])[:3]
                    self.log(f'[{self.dir}] <- de {origen}: "{mensaje}"')
                    self.linea(f"{'REP' if '?' in texto else 'OK'} {origen}")
                elif cmd == 'ENTREGADO':
                    self.log(f'[{self.dir}] confirmación: {resto} recibió el mensaje')
                    Cliente.confirmaciones.put(resto)
                elif cmd == 'REP':
                    self.log(f'[{self.dir}] {resto} pide repetir, se reenvía')
                    threading.Thread(target=self.enviar, args=(resto, self.ultimo.get(resto, '')),
                                     daemon=True).start()
                elif cmd == 'NODEST':
                    self.log(f'[{self.dir}] el conmutador no conoce al destino {resto}')
                else:
                    self.respuestas.put(linea.strip())
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('direccion')
    ap.add_argument('--esquema', choices=['morse', 'baudot'], default='morse')
    ap.add_argument('--puerto', type=int, default=PUERTO)
    args = ap.parse_args()

    cliente = Cliente(args.direccion, args.esquema, puerto=args.puerto)
    print(f'Cliente {cliente.dir} conectado. Escriba "<DESTINO> <mensaje>" o "salir".')
    while True:
        try:
            entrada = input().strip()
        except (EOFError, KeyboardInterrupt):
            break
        if entrada.lower() == 'salir':
            break
        destino, _, mensaje = entrada.partition(' ')
        if mensaje:
            cliente.enviar(destino, mensaje)


if __name__ == '__main__':
    main()
