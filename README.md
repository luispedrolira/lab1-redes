# Laboratorio 1 – Esquemas de comunicación e introducción a Wireshark

CC3067 Redes · Universidad del Valle de Guatemala · Semestre II 2026

## Contenido

| Archivo / carpeta | Descripción |
|---|---|
| `reporte_grupal.pdf` / `.md` | Parte 1: esquemas de comunicación (Morse, Baudot, conmutación). Realizada de forma individual |
| `reporte_individual.pdf` / `.md` | Parte 2: introducción a Wireshark — Luis Pedro Lira (23669) |
| `herramientas/registro_intento1.csv` | Registro de la práctica de recepción (partes 3.1 y 3.2) |
| `simulacion/audios/` | Audios `.wav` de los mensajes transmitidos (las "notas de voz" de 3.2) |
| `simulacion/demo_conmutador.log` | Registro de la demo del conmutador (3.3) |
| [herramientas/a_pdf.py](herramientas/a_pdf.py) | Genera los PDF a partir de los reportes Markdown |
| [herramientas/codificador.py](herramientas/codificador.py) | Codificador/decodificador Morse y Baudot + cálculo de errores |
| [simulacion/practica.py](simulacion/practica.py) | Partes 3.1 y 3.2: la computadora transmite el mensaje como audio y uno lo decodifica |
| [simulacion/conmutador.py](simulacion/conmutador.py), [simulacion/cliente.py](simulacion/cliente.py) | Parte 3.3: conmutador y clientes sobre TCP |
| [simulacion/canal_ruidoso.py](simulacion/canal_ruidoso.py) | Comparación de errores Morse vs. Baudot en un canal con ruido |
| [herramientas/captura_ring_buffer.ps1](herramientas/captura_ring_buffer.ps1) | Captura con ring buffer (10 archivos × 5 MB) |
| [analisis/analizar_pcap.py](analisis/analizar_pcap.py) | Análisis de la traza HTTP proporcionada |
| `capturas/` | Capturas de pantalla y archivos `.pcapng` de HTTP, intento HTTPS y conmutador |
| `capturas_ring_buffer/` | 10 archivos `lab1_23669_*.pcapng` del ring buffer + comando y salida |
| `intro-wireshark-trace1.pcap` | Traza proporcionada en Canvas |

## Uso de las herramientas

```bash
python herramientas/codificador.py morse "hola como estas"
python herramientas/codificador.py baudot "hola como estas"
python herramientas/codificador.py baudot -d "11010 11100 11011 10000"
python herramientas/codificador.py errores herramientas/registro.csv
python analisis/analizar_pcap.py intro-wireshark-trace1.pcap

python simulacion/practica.py morse                 # 3.1 (también: baudot)
python simulacion/practica.py morse --parte 3.2     # 3.2, genera los .wav en simulacion/audios/
python simulacion/conmutador.py --demo              # 3.3 automático
python simulacion/conmutador.py                     # 3.3 manual: + 3 terminales con
python simulacion/cliente.py A                      #   cliente.py A, B y C
python simulacion/canal_ruidoso.py
```
