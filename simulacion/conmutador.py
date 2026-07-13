"""
Conmutador de mensajes (parte 3.3) sobre TCP, con el protocolo descrito en el reporte.

Protocolo (una línea de texto por mensaje):
    cliente -> conmutador   HOLA <dir>                 registra la dirección del cliente (A, B, C)
    conmutador -> cliente   BIENVENIDO <dir>
    cliente -> conmutador   S?                         ¿está listo el conmutador?
    conmutador -> cliente   LISTO | OCUPADO            OCUPADO si su cola está llena
    cliente -> conmutador   DATA <esquema> <código>    código de "<DESTINO> <ORIGEN> <MENSAJE>"
    conmutador -> cliente   RECIBIDO | OCUPADO
    conmutador -> destino   DATA <esquema> <código>    reenvío del paquete tal como llegó
    destino -> conmutador   OK <origen> | REP <origen> confirmación o pedido de repetición
    conmutador -> origen    ENTREGADO <destino> | REP <destino> | NODEST <destino>

Uso:
    python conmutador.py                 # servidor; luego abrir 3 terminales con cliente.py A/B/C
    python conmutador.py --demo          # conmutador + 3 clientes automáticos en un solo proceso
Para verlo en Wireshark: interfaz "Adapter for loopback traffic capture", filtro tcp.port == 5050.
"""
import argparse
import datetime
import os
import queue
import socket
import sys
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'herramientas'))
sys.path.insert(0, AQUI)
import codificador as cod  # noqa: E402

HOST, PUERTO = '127.0.0.1', 5050
_impresion = threading.Lock()


def log(texto):
    with _impresion:
        print(f'{datetime.datetime.now():%H:%M:%S.%f}'[:-3], texto, flush=True)


def decodificar(esquema, codigo):
    return cod.decodificar_morse(codigo) if esquema == 'morse' else cod.decodificar_baudot(codigo)


class Conmutador:
    def __init__(self, capacidad=1, retardo=2.0):
        self.clientes = {}
        self.cola = queue.Queue(maxsize=capacidad)
        self.retardo = retardo
        self.envio = threading.Lock()
        self.listo = threading.Event()

    def enviar(self, conn, linea):
        with self.envio:
            conn.sendall((linea + '\n').encode())

    def iniciar(self, host=HOST, puerto=PUERTO):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, puerto))
        srv.listen()
        threading.Thread(target=self.reenviar, daemon=True).start()
        log(f'[S] conmutador escuchando en {host}:{puerto} (cola de {self.cola.maxsize}, '
            f'{self.retardo:.1f} s por reenvío)')
        self.listo.set()
        while True:
            conn, _ = srv.accept()
            threading.Thread(target=self.atender, args=(conn,), daemon=True).start()

    def atender(self, conn):
        direccion = None
        try:
            for linea in conn.makefile('r', encoding='utf-8'):
                cmd, _, resto = linea.strip().partition(' ')
                if cmd == 'HOLA':
                    direccion = resto.upper()
                    self.clientes[direccion] = conn
                    log(f'[S] cliente {direccion} conectado')
                    self.enviar(conn, f'BIENVENIDO {direccion}')
                elif cmd == 'S?':
                    estado = 'OCUPADO' if self.cola.full() else 'LISTO'
                    log(f'[S] {direccion} pregunta el estado -> {estado}')
                    self.enviar(conn, estado)
                elif cmd == 'DATA':
                    try:
                        self.cola.put_nowait((resto, direccion))
                        log(f'[S] paquete de {direccion} en cola ({self.cola.qsize()}/{self.cola.maxsize})')
                        self.enviar(conn, 'RECIBIDO')
                    except queue.Full:
                        self.enviar(conn, 'OCUPADO')
                elif cmd in ('OK', 'REP'):
                    origen = self.clientes.get(resto.upper())
                    log(f'[S] {direccion} responde {cmd} para {resto}')
                    if origen:
                        self.enviar(origen, f"{'ENTREGADO' if cmd == 'OK' else 'REP'} {direccion}")
        except OSError:
            pass
        finally:
            if direccion and self.clientes.get(direccion) is conn:
                del self.clientes[direccion]
                log(f'[S] cliente {direccion} desconectado')

    def reenviar(self):
        while True:
            dato, remitente = self.cola.get()
            esquema, _, codigo = dato.partition(' ')
            destino = decodificar(esquema, codigo).split(' ')[0]
            log(f'[S] procesando paquete de {remitente}: primer carácter -> destino {destino}')
            time.sleep(self.retardo)  # tiempo que tarda el conmutador en escuchar y reenviar
            conn = self.clientes.get(destino)
            if conn:
                self.enviar(conn, f'DATA {dato}')
                log(f'[S] reenviado a {destino}')
            elif remitente in self.clientes:
                self.enviar(self.clientes[remitente], f'NODEST {destino}')
                log(f'[S] destino {destino} desconocido, se avisa a {remitente}')


def demo(args):
    from cliente import Cliente

    conmutador = Conmutador(capacidad=args.capacidad, retardo=args.retardo)
    threading.Thread(target=conmutador.iniciar, args=(HOST, args.puerto), daemon=True).start()
    conmutador.listo.wait()

    clientes = {d: Cliente(d, args.esquema, puerto=args.puerto, log=log) for d in 'ABC'}
    plan = {
        'A': [('B', 'HOLA DESDE A'), ('C', 'PAQUETE NUMERO DOS')],
        'B': [('C', 'REDES DE DATOS'), ('A', 'CONMUTADOR LISTO')],
        'C': [('A', 'MENSAJE URGENTE'), ('D', 'DESTINO INEXISTENTE')],
    }
    hilos = [threading.Thread(target=lambda c=clientes[o], ms=ms: [c.enviar(d, m) for d, m in ms])
             for o, ms in plan.items()]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    esperados = sum(1 for ms in plan.values() for d, _ in ms if d in clientes)
    entregados = 0
    for _ in range(esperados):
        try:
            entregados += bool(Cliente.confirmaciones.get(timeout=args.retardo * 10))
        except queue.Empty:
            break
    time.sleep(args.retardo + 0.5)  # deja terminar los reenvíos que no generan confirmación (NODEST)
    log(f'[demo] mensajes entregados y confirmados: {entregados}/{esperados}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--demo', action='store_true')
    ap.add_argument('--puerto', type=int, default=PUERTO)
    ap.add_argument('--capacidad', type=int, default=1, help='paquetes que caben en la cola del conmutador')
    ap.add_argument('--retardo', type=float, default=2.0, help='segundos que tarda cada reenvío')
    ap.add_argument('--esquema', choices=['morse', 'baudot'], default='morse', help='solo para --demo')
    args = ap.parse_args()
    if args.demo:
        demo(args)
    else:
        try:
            Conmutador(args.capacidad, args.retardo).iniciar(HOST, args.puerto)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
