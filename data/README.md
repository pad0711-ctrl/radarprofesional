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
- `vence` (opcional, AAAA-MM-DD): fecha límite de un plazo. La tarjeta muestra "Plazo: D mes AAAA" hasta ese día, "Plazo vencido: ..." durante 7 días después, y luego no muestra nada. La fecha se calcula con la hora de Bogotá cuando corre el workflow.

Pruebas del script:

    python3 -I -m unittest discover -s tests -v

Herramientas: `herramientas.json` es la fuente del panel "Herramientas" del menú. Cada entrada lleva `href` (ruta absoluta del sitio), `titulo` y `descripcion`. Para agregar una herramienta, añádela ahí y ejecuta el script.

Qué regenera el script:
- index.html: portada (`BEGIN/END:portada`), "Lo último" (`BEGIN/END:lo-ultimo`), panel Herramientas (`BEGIN/END:herramientas`), archivo de publicaciones y contador.
- sitemap.xml: página de inicio, herramientas y todas las notas.

No editar esas partes a mano en index.html ni sitemap.xml: el script las sobrescribe.

Automatización: el workflow `.github/workflows/regenerar-sitio.yml` corre las pruebas y el script en cada cambio de `data/`, `scripts/` o `tests/` en main, y todos los días a las 6:00 a. m. (Bogotá). Si el resultado cambia, hace commit de index.html y sitemap.xml directo en main. Las etiquetas de plazo cambian con la fecha, así que la corrida diaria actualiza la portada y "Lo último" cuando un plazo entra en "vencido" o sale de la vista. Las corridas en pull requests solo ejecutan las pruebas.
