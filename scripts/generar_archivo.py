"""Regenera el archivo de publicaciones y el contador de index.html desde data/articulos.json.

Uso:
  python3 scripts/generar_archivo.py          # escribe index.html
  python3 scripts/generar_archivo.py --check  # no escribe; falla si index.html no coincide
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INDEX = RAIZ / "index.html"
DATOS = RAIZ / "data" / "articulos.json"

MESES = {m: i for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
     "agosto", "septiembre", "octubre", "noviembre", "diciembre"], start=1)}
NOMBRE_MES = {v: k.capitalize() for k, v in MESES.items()}


def mes_publicacion(meta):
    """Devuelve (año, mes) del movimiento más reciente de la nota: la última fecha de
    'Publicada', 'Corregida' o 'Actualizada en el sitio' dentro del texto meta."""
    fechas = []
    for m in re.finditer(r"(?:Publicada|Corregida|Actualizada) en el sitio:\s*\d{1,2} ([a-záéíóú]+) (\d{4})", meta):
        mes = MESES.get(m.group(1).lower())
        if not mes:
            raise ValueError(f"Mes desconocido: {m.group(1)}")
        fechas.append((int(m.group(2)), mes))
    if not fechas:
        raise ValueError(f"Falta 'Publicada en el sitio' en: {meta}")
    return max(fechas)


def validar(notas):
    hrefs = [n["href"] for n in notas]
    if len(hrefs) != len(set(hrefs)):
        raise ValueError("Hay URL repetidas en data/articulos.json")
    for n in notas:
        if not n["href"].startswith(("/actualidad/", "https://radarprofesional.online/actualidad/")):
            raise ValueError(f"URL fuera de /actualidad/: {n['href']}")
        mes_publicacion(n["meta"])


def render_archivo(notas):
    grupos = {}
    for n in notas:
        grupos.setdefault(mes_publicacion(n["meta"]), []).append(n)
    bloques = []
    for (anio, mes) in sorted(grupos, reverse=True):
        items = grupos[(anio, mes)]
        lis = "".join(
            f'        <li>\n          <a href="{n["href"]}">{n["titulo"]}</a><br>\n'
            f'          <small>{n["meta"]}</small>\n        </li>\n' for n in items)
        bloques.append(
            f"    <details>\n      <summary>{NOMBRE_MES[mes]} de {anio} · {len(items)} noticias</summary>\n"
            f"      <ul>\n{lis}      </ul>\n    </details>")
    cabecera = ('<section class="archive" id="archivo">\n'
                '    <h2 class="section-heading">Archivo de publicaciones</h2>\n'
                '    <p>Consulta todas las notas. Las fechas originales y las actualizaciones se conservan.</p>\n\n')
    return cabecera + "\n\n".join(bloques) + "\n  </section>"


def reemplazar(html, nuevo_archivo, total):
    html, n1 = re.subn(r'<section class="archive" id="archivo">.*?</section>',
                       lambda _: nuevo_archivo, html, count=1, flags=re.S)
    html, n2 = re.subn(r'(<p id="result-count" aria-live="polite">)[^<]*(</p>)',
                       lambda m: f"{m.group(1)}{total} noticias disponibles{m.group(2)}", html, count=1)
    if n1 != 1 or n2 != 1:
        raise ValueError("No se encontró la sección de archivo o el contador en index.html")
    return html


def main():
    notas = json.loads(DATOS.read_text(encoding="utf-8"))["notas"]
    validar(notas)
    actual = INDEX.read_text(encoding="utf-8")
    nuevo = reemplazar(actual, render_archivo(notas), len(notas))
    if "--check" in sys.argv:
        if nuevo != actual:
            print("index.html NO coincide con data/articulos.json. Ejecuta el script sin --check.")
            return 1
        print(f"OK: index.html coincide con {len(notas)} notas.")
        return 0
    INDEX.write_text(nuevo, encoding="utf-8")
    print(f"index.html actualizado con {len(notas)} notas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
