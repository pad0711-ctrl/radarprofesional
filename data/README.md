# Datos del sitio

`articulos.json` es la fuente de verdad del archivo de publicaciones y del contador "N noticias disponibles" de index.html.

Para agregar una nota, añade una entrada a `notas` con `href` (ruta /actualidad/... o URL completa), `titulo` y `meta` (la línea que se muestra bajo el título, con fuente y fechas de publicación y corrección). Luego ejecuta:

    python3 scripts/generar_archivo.py

Y para verificar sin escribir:

    python3 scripts/generar_archivo.py --check

El script agrupa cada nota por el mes de su movimiento más reciente (publicación o corrección) y valida que no haya URL repetidas.

Pendiente de automatizar: las tarjetas de "Lo último", la portada destacada (hero), el sitemap.xml y el panel de Herramientas. Hoy siguen editándose a mano.
