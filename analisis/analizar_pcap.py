"""
Analizador mínimo de archivos .pcap (formato clásico, Ethernet) sin dependencias.
Cuenta protocolos, paquetes TCP con SYN=1 y muestra los encabezados HTTP.

Uso:
    python analizar_pcap.py ../intro-wireshark-trace1.pcap
"""
import collections
import datetime
import struct
import sys

UTC = datetime.timezone.utc


def leer_pcap(ruta):
    datos = open(ruta, 'rb').read()
    magia = datos[:4]
    if magia == b'\xd4\xc3\xb2\xa1':
        orden = '<'
    elif magia == b'\xa1\xb2\xc3\xd4':
        orden = '>'
    else:
        sys.exit('No es un pcap clásico (¿pcapng?). Ábralo en Wireshark y guárdelo como .pcap.')
    enlace = struct.unpack(orden + 'I', datos[20:24])[0]
    off = 24
    paquetes = []
    while off + 16 <= len(datos):
        seg, useg, incl, _ = struct.unpack(orden + 'IIII', datos[off:off + 16])
        off += 16
        paquetes.append((seg + useg / 1e6, datos[off:off + incl]))
        off += incl
    return enlace, paquetes


def main(ruta):
    enlace, paquetes = leer_pcap(ruta)
    hora = lambda ts: datetime.datetime.fromtimestamp(ts, UTC)
    print(f'Paquetes: {len(paquetes)}')
    print(f'Inicio : {hora(paquetes[0][0])}  Fin: {hora(paquetes[-1][0])}')

    protocolos = collections.Counter()
    syn = []
    http = []
    for n, (ts, p) in enumerate(paquetes, 1):
        if enlace != 1 or len(p) < 14:
            protocolos['otro enlace'] += 1
            continue
        etype = struct.unpack('>H', p[12:14])[0]
        if etype != 0x0800:
            protocolos.update([{0x0806: 'ARP', 0x86dd: 'IPv6'}.get(etype, 'otro L2')])
            continue
        ip = p[14:]
        ihl = (ip[0] & 0xf) * 4
        src = '.'.join(map(str, ip[12:16]))
        dst = '.'.join(map(str, ip[16:20]))
        seg = ip[ihl:]
        if ip[9] == 6:
            sp, dp = struct.unpack('>HH', seg[:4])
            if seg[13] & 0x02:
                syn.append((n, src, sp, dst, dp, 'SYN,ACK' if seg[13] & 0x10 else 'SYN'))
            carga = seg[(seg[12] >> 4) * 4:]
            if carga[:4] in (b'GET ', b'POST', b'HTTP', b'HEAD'):
                protocolos['HTTP'] += 1
                http.append((n, ts, src, sp, dst, dp, carga))
            else:
                protocolos['TCP'] += 1
        elif ip[9] == 17:
            protocolos['UDP'] += 1
        else:
            protocolos[f'IP proto {ip[9]}'] += 1

    print('Protocolos:', ', '.join(f'{k}={v}' for k, v in protocolos.most_common()))
    print(f'\nPaquetes TCP con SYN=1 ({len(syn)}):')
    for n, src, sp, dst, dp, flags in syn:
        print(f'  #{n:<4} {src}:{sp} -> {dst}:{dp}  [{flags}]')

    for n, ts, src, sp, dst, dp, carga in http:
        encabezado, _, cuerpo = carga.partition(b'\r\n\r\n')
        print(f'\n=== Paquete #{n}  {hora(ts).time()} UTC  {src}:{sp} -> {dst}:{dp}')
        print(encabezado.decode('latin1').replace('\r\n', '\n'))
        if cuerpo:
            print(f'--- cuerpo ({len(cuerpo)} bytes) ---')
            print(cuerpo.decode('latin1').replace('\r\n', '\n'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'intro-wireshark-trace1.pcap')
