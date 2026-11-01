"""Pruebas de scripts/generar_archivo.py. Ejecutar desde la raíz del repo:

    python3 -I -m unittest discover -s tests -v
"""
import copy
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import generar_archivo as g  # noqa: E402

NOTAS = json.loads((RAIZ / "data" / "articulos.json").read_text(encoding="utf-8"))["notas"]
HERRAMIENTAS = json.loads((RAIZ / "data" / "herramientas.json").read_text(encoding="utf-8"))["herramientas"]
INDEX_HTML = (RAIZ / "index.html").read_text(encoding="utf-8")
HTML_MINIMO = ('<p id="result-count" aria-live="polite">0</p>\n'
               '<section class="archive" id="archivo">\n  </section>')


class EscapeHTML(unittest.TestCase):
    def test_titulo_y_tag_con_ampersand_se_escapan(self):
        n = copy.deepcopy(NOTAS[0])
        n["titulo"] = "Impuestos & auditoría"
        n["tag"] = "Riesgos & tecnología"
        g.validar([n] + NOTAS[1:])  # antes esto fallaba por la regla de caracteres prohibidos
        tarjeta = g.tarjeta(n, 0, "news-card", "h3")
        self.assertIn("Impuestos &amp; auditoría", tarjeta)
        self.assertIn('<span class="tag">Riesgos &amp; tecnología</span>', tarjeta)
        self.assertNotIn("Impuestos & auditoría", tarjeta)
        archivo = g.render_archivo([n] + NOTAS[1:])
        self.assertIn("Impuestos &amp; auditoría", archivo)

    def test_atributos_escapan_comillas(self):
        n = copy.deepcopy(NOTAS[0])
        n["buscar"] = 'frase "entre comillas" y <etiqueta>'
        tarjeta = g.tarjeta(n, 0, "news-card", "h3")
        self.assertIn('data-search="frase &quot;entre comillas&quot; y &lt;etiqueta&gt;"', tarjeta)

    def test_texto_sin_caracteres_especiales_no_cambia(self):
        self.assertEqual(g.texto("Impuestos y auditoría"), "Impuestos y auditoría")
        self.assertEqual(g.atributo("Impuestos y auditoría"), "Impuestos y auditoría")


class Plural(unittest.TestCase):
    def test_total_de_uno_usa_singular(self):
        html = g.reemplazar_archivo_y_contador(HTML_MINIMO, g.render_archivo(NOTAS[:1]), 1)
        self.assertIn('aria-live="polite">1 noticia disponible</p>', html)

    def test_total_de_varios_usa_plural(self):
        html = g.reemplazar_archivo_y_contador(HTML_MINIMO, g.render_archivo(NOTAS), len(NOTAS))
        self.assertIn('aria-live="polite">26 noticias disponibles</p>', html)

    def test_resumen_de_mes_con_una_nota(self):
        archivo = g.render_archivo(NOTAS[:1])
        self.assertIn("· 1 noticia</summary>", archivo)
        self.assertNotIn("1 noticias", archivo)


class Duplicados(unittest.TestCase):
    def test_relativa_y_absoluta_son_la_misma_url(self):
        notas = copy.deepcopy(NOTAS)
        absoluta = notas[0]["href"]
        self.assertTrue(absoluta.startswith(g.BASE))
        notas[1]["href"] = absoluta[len(g.BASE):]  # misma nota, en forma relativa
        with self.assertRaisesRegex(ValueError, "repetidas"):
            g.validar(notas)

    def test_datos_actuales_no_tienen_duplicados(self):
        g.validar(copy.deepcopy(NOTAS))

    def test_url_relativa_se_normaliza(self):
        self.assertEqual(g.url_absoluta("/actualidad/x/"), g.BASE + "/actualidad/x/")
        self.assertEqual(g.url_absoluta(g.BASE + "/actualidad/x/"), g.BASE + "/actualidad/x/")


class IndexActual(unittest.TestCase):
    def test_generar_sobre_index_actual_no_cambia_nada(self):
        self.assertEqual(g.generar(INDEX_HTML, NOTAS), INDEX_HTML)


if __name__ == "__main__":
    unittest.main()


class Herramientas(unittest.TestCase):
    def test_render_incluye_enlaces_y_descripcion(self):
        salida = g.render_herramientas(HERRAMIENTAS)
        self.assertIn("<summary>Herramientas</summary>", salida)
        for h in HERRAMIENTAS:
            self.assertIn(f'<a href="{h["href"]}">{h["titulo"]}</a>', salida)
            self.assertIn(f'<small>{h["descripcion"]}</small>', salida)

    def test_ampersand_se_escapa(self):
        h = [{"href": "/x/", "titulo": "Impuestos & aduanas", "descripcion": "d"}]
        self.assertIn("Impuestos &amp; aduanas", g.render_herramientas(h))

    def test_ruta_relativa_se_rechaza(self):
        h = [{"href": "calendario/", "titulo": "t", "descripcion": "d"}]
        with self.assertRaises(ValueError):
            g.validar_herramientas(h)

    def test_index_actual_tiene_marcadores(self):
        self.assertIn("<!-- BEGIN:herramientas -->", INDEX_HTML)
        self.assertIn("<!-- END:herramientas -->", INDEX_HTML)


class Sitemap(unittest.TestCase):
    def test_incluye_home_herramientas_y_todas_las_notas(self):
        salida = g.render_sitemap(NOTAS, HERRAMIENTAS)
        self.assertIn(f"<loc>{g.BASE}/</loc>", salida)
        for h in HERRAMIENTAS:
            self.assertIn(f"<loc>{g.BASE}{h['href']}</loc>", salida)
        for n in NOTAS:
            self.assertIn(f"<loc>{g.url_absoluta(n['href'])}</loc>", salida)

    def test_sitemap_versionado_coincide_con_los_datos(self):
        generado = g.render_sitemap(NOTAS, HERRAMIENTAS)
        actual = (RAIZ / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(generado, actual)

    def test_url_repetida_entre_notas_y_herramientas_falla(self):
        herr = [{"href": NOTAS[0]["href"], "titulo": "t", "descripcion": "d"}]
        with self.assertRaises(ValueError):
            g.render_sitemap(NOTAS, herr)

