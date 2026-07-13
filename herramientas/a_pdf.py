"""
Convierte los reportes Markdown a PDF (Markdown -> HTML -> PDF con Microsoft Edge en modo headless).

    python herramientas/a_pdf.py reporte_grupal.md reporte_individual.md
Requiere: pip install markdown
"""
import os
import pathlib
import re
import subprocess
import sys

import markdown

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
CSS = """
@page { size: Letter; margin: 2cm 1.8cm; }
body { font-family: 'Segoe UI', Calibri, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1d1d1d; }
h1 { color: #0b6b3a; border-bottom: 2px solid #0b6b3a; padding-bottom: 4px; font-size: 20pt; }
h2 { color: #0b6b3a; margin-top: 1.4em; font-size: 15pt; }
h3 { font-size: 12pt; margin-top: 1.2em; }
table { border-collapse: collapse; width: 100%; margin: .8em 0; font-size: 9.5pt; page-break-inside: avoid; }
th { background: #0b6b3a; color: white; text-align: left; }
th, td { border: 1px solid #c9c9c9; padding: 4px 7px; vertical-align: top; }
tr:nth-child(even) td { background: #f3f7f4; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #f1f1f1; padding: 0 3px; }
pre { background: #f6f6f6; border: 1px solid #ddd; padding: 8px; font-size: 8.5pt; white-space: pre-wrap; }
pre code { background: none; padding: 0; }
blockquote { border-left: 4px solid #0b6b3a; margin: 0; padding: 4px 12px; background: #f3f7f4; }
img { max-width: 100%; border: 1px solid #ccc; margin: 6px 0; page-break-inside: avoid; }
"""


PENDIENTE = re.compile(r'^📷 Captura pendiente: `([^`]+\.png)`(?: \(opcional\))?\.?\s*(.*)$')


def insertar_capturas(texto, carpeta):
    """Reemplaza cada línea '📷 Captura pendiente: `ruta.png` ...' por la imagen si el archivo ya existe."""
    lineas = []
    for linea in texto.splitlines():
        m = PENDIENTE.match(linea)
        if m and (carpeta / m.group(1)).exists():
            descripcion = m.group(2).removeprefix('Debe mostrar ').rstrip('.') or m.group(1)
            lineas += ['', f'![{descripcion}]({m.group(1)})', '', f'*Figura: {descripcion}.*', '']
        elif m and '(opcional)' in linea:
            continue
        else:
            lineas.append(linea)
    return '\n'.join(lineas)


ITEM = re.compile(r'\s*([-*]|\d+\.) ')


def separar_listas(texto):
    """Python-Markdown exige una línea en blanco entre un párrafo y la lista que le sigue."""
    salida = []
    en_codigo = False
    for linea in texto.splitlines():
        if linea.startswith('```'):
            en_codigo = not en_codigo
        anterior = salida[-1] if salida else ''
        if (not en_codigo and ITEM.match(linea) and anterior.strip()
                and not ITEM.match(anterior) and not anterior.startswith(' ')):
            salida.append('')
        salida.append(linea)
    return '\n'.join(salida)


def convertir(ruta_md):
    ruta_md = pathlib.Path(ruta_md).resolve()
    texto = separar_listas(insertar_capturas(ruta_md.read_text(encoding='utf-8'), ruta_md.parent))
    cuerpo = markdown.markdown(texto, extensions=['tables', 'fenced_code', 'sane_lists'])
    html = ruta_md.with_suffix('.tmp.html')
    html.write_text(f'<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{CSS}</style>'
                    f'</head><body>{cuerpo}</body></html>', encoding='utf-8')
    pdf = ruta_md.with_suffix('.pdf')
    subprocess.run([EDGE, '--headless', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={pdf}', html.as_uri()], check=True, capture_output=True)
    os.remove(html)
    print(f'{pdf.name}: {pdf.stat().st_size / 1024:.0f} KB')


if __name__ == '__main__':
    for ruta in sys.argv[1:]:
        convertir(ruta)
