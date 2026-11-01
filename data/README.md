# Datos del sitio

`articulos.json` es la fuente de verdad del archivo de publicaciones y del contador "N noticias disponibles" de index.html.

Para agregar una nota, añade una entrada a `notas` con `href` (ruta /actualidad/... o URL completa), `titulo` y `meta` (la línea que se muestra bajo el título, con fuente y fechas de publicación y corrección). Luego ejecuta:

    python3 scripts/generar_archivo.py

Y para verificar sin escribir:

    python3 scripts/generar_archivo.py --check

El script agrupa cada nota por el mes de su movimiento más reciente (publicación o corrección) y valida que no haya URL repetidas.

Campos de cada nota:
- `href`, `titulo`, `meta`: URL, título y línea de fuente/fechas (se muestra en el archivo y en la tarjeta).
- `tag` (opcional): etiqueta visible de la tarjeta.
- `tema`: valor de `data-topic` (filtro del buscador). Obligatorio.
- `buscar`: texto del buscador (`data-search`). Obligatorio.
- `resumen`: párrafo de la tarjeta. Obligatorio.
- `portada`: `"destacada"` (una nota) o `"lateral"` (dos notas). Las demás van a "Lo último", ordenadas por la fecha de movimiento más reciente.

Pruebas del script:

    python3 -I -m unittest discover -s tests -v

Los bloques `<!-- BEGIN:portada -->`, `<!-- BEGIN:lo-ultimo -->` y el archivo se regeneran con el script. No editar esas partes a mano en index.html.

Pendiente de automatizar: el sitemap.xml y el panel de Herramientas.
