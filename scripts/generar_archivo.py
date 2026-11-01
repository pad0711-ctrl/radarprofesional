"""Regenera desde data/ las partes automáticas del sitio:
- index.html: la portada destacada (BEGIN/END:portada), la lista "Lo último"
  (BEGIN/END:lo-ultimo), el panel Herramientas (BEGIN/END:herramientas), el archivo de
  publicaciones y el contador de noticias.
- sitemap.xml: home, herramientas y todas las notas.

Uso:
  python3 scripts/generar_archivo.py          # escribe index.html y sitemap.xml
  python3 scripts/generar_archivo.py --check  # no escribe; falla si algo no coincide
"""
import json
import re
import sys
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
INDEX = RAIZ / "index.html"
DATOS = RAIZ / "data" / "articulos.json"
DATOS_HERRAMIENTAS = RAIZ / "data" / "herramientas.json"
SITEMAP = RAIZ / "sitemap.xml"
BASE = "https://radarprofesional.online"

MESES = {m: i for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
     "agosto", "septiembre", "octubre", "noviembre", "diciembre"], start=1)}
NOMBRE_MES = {v: k.capitalize() for k, v in MESES.items()}
SEPARADOR = " · "


def atributo(s):
    return escape(s, quote=True)


def texto(s):
    return escape(s, quote=False)


def plural(n, singular, plural_):
    return f"{n} {singular if n == 1 else plural_}"


def url_absoluta(href):
    return BASE + href if href.startswith("/") else href


def fecha_movimiento(meta):
    """Fecha (año, mes, día) del movimiento más reciente de la nota: la última fecha de
    'Publicada', 'Corregida' o 'Actualizada en el sitio' dentro del texto meta."""
    fechas = []
    for m in re.finditer(r"(?:Publicada|Corregida|Actualizada) en el sitio:\s*(\d{1,2}) ([a-záéíóú]+) (\d{4})", meta):
        mes = MESES.get(m.group(2).lower())
        if not mes:
            raise ValueError(f"Mes desconocido: {m.group(2)}")
        fechas.append((int(m.group(3)), mes, int(m.group(1))))
    if not fechas:
        raise ValueError(f"Falta 'Publicada en el sitio' en: {meta}")
    return max(fechas)


ZONA = ZoneInfo("America/Bogota")
DIAS_PLAZO_VENCIDO = 7


def hoy_bogota():
    return datetime.now(ZONA).date()


def fecha_corta(d):
    mes = next(k for k, v in MESES.items() if v == d.month)
    return f"{d.day} {mes} {d.year}"


def etiqueta_plazo(n, hoy):
    """'Plazo: D mes AAAA' hasta el día de vencimiento; 'Plazo vencido: ...' durante
    los 7 días siguientes; después no se muestra."""
    if not n.get("vence"):
        return None
    vence = date.fromisoformat(n["vence"])
    if hoy <= vence:
        return f"Plazo: {fecha_corta(vence)}"
    if hoy <= vence + timedelta(days=DIAS_PLAZO_VENCIDO):
        return f"Plazo vencido: {fecha_corta(vence)}"
    return None


def validar(notas):
    hrefs = [url_absoluta(n["href"]) for n in notas]
    if len(hrefs) != len(set(hrefs)):
        raise ValueError("Hay URL repetidas en data/articulos.json (comparadas como URL absolutas)")
    for n in notas:
        if not n["href"].startswith(("/actualidad/", "https://radarprofesional.online/actualidad/")):
            raise ValueError(f"URL fuera de /actualidad/: {n['href']}")
        for campo in ("titulo", "meta", "tema", "buscar", "resumen"):
            if campo not in n:
                raise ValueError(f"Falta '{campo}' en {n['href']}")
        fecha_movimiento(n["meta"])
        if "vence" in n:
            try:
                date.fromisoformat(n["vence"])
            except ValueError:
                raise ValueError(f"'vence' debe ser AAAA-MM-DD en {n['href']}")
        if n.get("portada") not in (None, "destacada", "lateral"):
            raise ValueError(f"'portada' inválida en {n['href']}")
    if sum(1 for n in notas if n.get("portada") == "destacada") != 1:
        raise ValueError("Debe haber exactamente una nota con portada 'destacada'")
    if sum(1 for n in notas if n.get("portada") == "lateral") != 2:
        raise ValueError("Debe haber exactamente dos notas con portada 'lateral'")


def tarjeta(n, sangria, clase, encabezado, hoy=None):
    i = " " * sangria
    hoy = hoy or hoy_bogota()
    lineas = [f'{i}<div class="{clase}" data-topic="{atributo(n["tema"])}" data-search="{atributo(n["buscar"])}">',
              f'{i}  <div class="meta">']
    if n.get("tag"):
        lineas.append(f'{i}    <span class="tag">{texto(n["tag"])}</span>')
    lineas += [f'{i}    <span>{texto(parte)}</span>' for parte in n["meta"].split(SEPARADOR)]
    plazo = etiqueta_plazo(n, hoy)
    if plazo:
        lineas.append(f'{i}    <span class="plazo">{texto(plazo)}</span>')
    lineas += [f'{i}  </div>',
               f'{i}  <{encabezado}><a href="{atributo(n["href"])}">{texto(n["titulo"])}</a></{encabezado}>',
               f'{i}  <p>{texto(n["resumen"])}</p>',
               f'{i}  <a class="read-more" href="{atributo(n["href"])}">Leer noticia →</a>',
               f'{i}</div>']
    return "\n".join(lineas)


def validar_herramientas(herramientas):
    hrefs = [url_absoluta(h["href"]) for h in herramientas]
    if len(hrefs) != len(set(hrefs)):
        raise ValueError("Hay herramientas con la misma URL en data/herramientas.json")
    for h in herramientas:
        if not h["href"].startswith("/"):
            raise ValueError(f"La herramienta debe usar ruta absoluta del sitio: {h['href']}")
        for campo in ("titulo", "descripcion"):
            if campo not in h:
                raise ValueError(f"Falta '{campo}' en la herramienta {h['href']}")


def render_herramientas(herramientas):
    enlaces = "".join(
        f'<a href="{atributo(h["href"])}">{texto(h["titulo"])}</a>'
        f'<small>{texto(h["descripcion"])}</small>' for h in herramientas)
    return (f'        <details class="tools"><summary>Herramientas</summary>'
            f'<div class="panel">{enlaces}</div></details>')


def render_sitemap(notas, herramientas):
    urls = [BASE + "/"]
    urls += [url_absoluta(h["href"]) for h in herramientas]
    urls += [url_absoluta(n["href"]) for n in notas]
    if len(urls) != len(set(urls)):
        raise ValueError("Hay URL repetidas al generar sitemap.xml")
    lineas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lineas += [f'  <url><loc>{texto(u)}</loc></url>' for u in urls]
    lineas.append("</urlset>")
    return "\n".join(lineas) + "\n"


def render_portada(notas, hoy=None):
    destacada = next(n for n in notas if n.get("portada") == "destacada")
    laterales = [n for n in notas if n.get("portada") == "lateral"]
    return ('  <section class="hero" aria-label="Noticias destacadas">\n'
            + tarjeta(destacada, 4, "feature", "h2", hoy) + "\n\n"
            + '    <div class="hero-side">\n'
            + "\n\n".join(tarjeta(n, 6, "news-card", "h3", hoy) for n in laterales) + "\n"
            + "    </div>\n"
            + "  </section>")


def ordenar_lo_ultimo(notas):
    # Orden estable: a igual fecha, se conserva el orden de data/articulos.json.
    resto = [n for n in notas if not n.get("portada")]
    return sorted(resto, key=lambda n: fecha_movimiento(n["meta"]), reverse=True)


def render_lo_ultimo(notas, hoy=None):
    return "\n\n".join(tarjeta(n, 8, "news-card", "h3", hoy) for n in ordenar_lo_ultimo(notas))


def render_archivo(notas):
    grupos = {}
    for n in notas:
        anio, mes, _ = fecha_movimiento(n["meta"])
        grupos.setdefault((anio, mes), []).append(n)
    bloques = []
    for (anio, mes) in sorted(grupos, reverse=True):
        items = grupos[(anio, mes)]
        lis = "".join(
            f'        <li>\n          <a href="{atributo(n["href"])}">{texto(n["titulo"])}</a><br>\n'
            f'          <small>{texto(n["meta"])}</small>\n        </li>\n' for n in items)
        bloques.append(
            f"    <details>\n      <summary>{NOMBRE_MES[mes]} de {anio} · {plural(len(items), 'noticia', 'noticias')}</summary>\n"
            f"      <ul>\n{lis}      </ul>\n    </details>")
    cabecera = ('<section class="archive" id="archivo">\n'
                '    <h2 class="section-heading">Archivo de publicaciones</h2>\n'
                '    <p>Consulta todas las notas. Las fechas originales y las actualizaciones se conservan.</p>\n\n')
    return cabecera + "\n\n".join(bloques) + "\n  </section>"


def reemplazar_bloque(html, nombre, contenido):
    patron = re.compile(
        rf"^([ ]*)<!-- BEGIN:{nombre} -->\n.*?^[ ]*<!-- END:{nombre} -->", re.M | re.S)
    html, n = patron.subn(
        lambda m: f"{m.group(1)}<!-- BEGIN:{nombre} -->\n{contenido}\n{m.group(1)}<!-- END:{nombre} -->",
        html, count=1)
    if n != 1:
        raise ValueError(f"Falta el bloque <!-- BEGIN:{nombre} --> ... <!-- END:{nombre} --> en index.html")
    return html


def reemplazar_archivo_y_contador(html, nuevo_archivo, total):
    html, n1 = re.subn(r'<section class="archive" id="archivo">.*?</section>',
                       lambda _: nuevo_archivo, html, count=1, flags=re.S)
    html, n2 = re.subn(r'(<p id="result-count" aria-live="polite">)[^<]*(</p>)',
                       lambda m: f"{m.group(1)}{plural(total, 'noticia disponible', 'noticias disponibles')}{m.group(2)}",
                       html, count=1)
    if n1 != 1 or n2 != 1:
        raise ValueError("No se encontró la sección de archivo o el contador en index.html")
    return html


def cargar_herramientas():
    herramientas = json.loads(DATOS_HERRAMIENTAS.read_text(encoding="utf-8"))["herramientas"]
    validar_herramientas(herramientas)
    return herramientas


def generar(html, notas, herramientas=None, hoy=None):
    if herramientas is None:
        herramientas = cargar_herramientas()
    hoy = hoy or hoy_bogota()
    html = reemplazar_bloque(html, "portada", render_portada(notas, hoy))
    html = reemplazar_bloque(html, "lo-ultimo", render_lo_ultimo(notas, hoy))
    html = reemplazar_bloque(html, "herramientas", render_herramientas(herramientas))
    return reemplazar_archivo_y_contador(html, render_archivo(notas), len(notas))


def main():
    notas = json.loads(DATOS.read_text(encoding="utf-8"))["notas"]
    validar(notas)
    herramientas = cargar_herramientas()
    actual = INDEX.read_text(encoding="utf-8")
    nuevo = generar(actual, notas, herramientas)
    sitemap_nuevo = render_sitemap(notas, herramientas)
    sitemap_actual = SITEMAP.read_text(encoding="utf-8")
    if "--check" in sys.argv:
        if nuevo != actual or sitemap_nuevo != sitemap_actual:
            print("index.html o sitemap.xml NO coinciden con data/. Ejecuta el script sin --check.")
            return 1
        print(f"OK: index.html y sitemap.xml coinciden con {len(notas)} notas y {len(herramientas)} herramientas.")
        return 0
    INDEX.write_text(nuevo, encoding="utf-8")
    SITEMAP.write_text(sitemap_nuevo, encoding="utf-8")
    print(f"index.html y sitemap.xml actualizados con {len(notas)} notas y {len(herramientas)} herramientas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
