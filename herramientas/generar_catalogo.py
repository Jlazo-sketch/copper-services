"""Catálogo público de productos en copper-services.cl.

El catálogo vive en Copper OS (app.copper-services.cl/cotizar), pero esa página
se arma con JavaScript y los buscadores y asistentes de IA (Google, ChatGPT/Bing,
Gemini, Claude) la ven vacía. Este script la "copia" como páginas fijas:

    /productos/                  índice con todas las familias
    /productos/<familia>/        cada familia con sus productos, foto y botón Cotizar

Uso (desde la raíz del repo):
    python herramientas/generar_catalogo.py --actualizar   # baja catálogo y fotos de la API y genera
    python herramientas/generar_catalogo.py                # genera desde herramientas/catalogo.json

generar_paginas.py lo llama para incluir estas URLs en el sitemap.
"""
from __future__ import annotations

import io
import json
import re
import shutil
import sys
import unicodedata
import urllib.request
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generar_paginas import (  # noqa: E402
    COTIZADOR, DIRECCION, E, ICONO_WA, RAIZ, SITIO, TELEFONO, TELEFONO_WA, ZONA,
    cabecera, json_ld, pie, recortar,
)

API = "https://api.copper-services.cl"
DATOS = RAIZ / "herramientas" / "catalogo.json"
FOTOS = RAIZ / "IMAGENES" / "productos"
SALIDA = RAIZ / "productos"
FOTO_FAMILIA = "/IMAGENES/web/suministro-materiales.webp"

# Textos por familia (clave = prefijo de SKU en Copper OS). Solo describen lo
# que de verdad hay en el catálogo; si aparece una familia nueva sin texto, se
# usa uno genérico y la página igual se genera.
FAMILIAS = {
    "PRO": ("protecciones-electricas", "Protecciones eléctricas: automáticos, diferenciales, contactores y guardamotores",
            "Interruptores automáticos curva C de 6 kA (1, 2 y 3 polos), diferenciales de 30 mA, contactores, guardamotores, relés térmicos, relés de control de voltaje y temporizados para tableros industriales y domiciliarios."),
    "TAB": ("accesorios-de-tablero", "Accesorios para tableros eléctricos",
            "Luces piloto, pulsadores de 22 mm, selectores, canaleta ranurada, riel DIN, borneras, barras de conexión y barras de puesta a tierra para armar y mantener tableros."),
    "EIN": ("enchufes-industriales", "Enchufes industriales IEC 60309 y conectores",
            "Enchufes industriales macho y hembra IP44 de 16 y 32 A en 220 V y 380 V (2P+T, 3P+T y 3P+N+T), hydrobox para ambientes húmedos, enchufes volantes pesados y conectores para faena y talleres."),
    "CIN": ("cables-industriales", "Cables industriales: cordón RV-K, libre de halógeno, concéntrico y preensamblado",
            "Cordón RV-K y cordón eléctrico en rollo, cable libre de halógeno H07Z1-K, cable concéntrico y preensamblado para instalaciones industriales y empalmes. Venta por rollo o por metro según el producto."),
    "CAN": ("canalizacion-electrica", "Canalización eléctrica: tubería EMT, conduit PVC y accesorios",
            "Tubería EMT y conduit PVC de 16 a 32 mm con sus coplas, curvas, terminales, salidas de caja y abrazaderas, además de cabezas de servicio, grampas y conectores para empalmes."),
    "CTE": ("consumibles-electricos", "Consumibles eléctricos: terminales, prensaestopas, mangas y cintas",
            "Terminales de compresión, ferrules, prensaestopas, mangas termocontraíbles, cinta aislante, cinta autofundente y amarras plásticas para terminar instalaciones."),
    "IIN": ("iluminacion-industrial", "Iluminación industrial y de emergencia",
            "Proyectores LED IP65, lámparas de emergencia, señalética de salida, tortugas con rejilla y portalámparas para talleres, bodegas e instalaciones de faena."),
    "AMP": ("ampolletas-led", "Ampolletas LED",
            "Ampolletas LED E27 clásicas y dicroicas GU10, en luz fría y cálida."),
    "LUM": ("luminarias", "Paneles LED y luminarias",
            "Paneles LED sobrepuestos redondos y cuadrados y portalámparas para oficinas, casas y recintos de faena."),
    "AEM": ("artefactos-electricos-embutidos", "Interruptores, enchufes y artefactos embutidos",
            "Interruptores simples, dobles y conmutadores, enchufes simples, dobles, bipaso y triples, adaptadores y tablero embutido de 6 puestos."),
    "ASO": ("artefactos-sobrepuestos-y-medidores", "Cajas estancas, medidores y cajas de empalme",
            "Cajas estancas IP65, medidor electrónico monofásico y caja de empalme para medidor, para instalaciones a la vista y empalmes."),
    "EAD": ("alargadores-y-adaptadores", "Alargadores y adaptadores",
            "Alargadores con interruptor y adaptadores para conectar equipos en oficina, taller y faena."),
    "CDO": ("cables-domiciliarios", "Cables domiciliarios EVA y libres de halógeno",
            "Cable EVA de 1,5 mm² y cable libre de halógeno de 2,5 mm² en rollos, y alargadores, para instalaciones domiciliarias y de oficinas."),
}


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def actualizar() -> None:
    """Baja el catálogo público y las fotos (WebP 480 px) desde Copper OS."""
    from PIL import Image

    with urllib.request.urlopen(API + "/publico/catalogo", timeout=60) as r:
        productos = json.load(r)
    if not productos:
        raise SystemExit("La API devolvió el catálogo vacío: no se actualiza (evita borrar las páginas).")
    FOTOS.mkdir(parents=True, exist_ok=True)
    vigentes = set()
    for p in productos:
        if not p.get("foto"):
            continue
        nombre = f"{slug(p['sku'])}.webp"
        vigentes.add(nombre)
        version = p["foto"].split("v=")[-1]
        marca = FOTOS / f".{slug(p['sku'])}.{version}"
        if (FOTOS / nombre).exists() and marca.exists():
            continue  # misma foto que la última vez
        with urllib.request.urlopen(API + p["foto"], timeout=60) as r:
            im = Image.open(io.BytesIO(r.read())).convert("RGB")
        im.thumbnail((480, 480))
        im.save(FOTOS / nombre, "WEBP", quality=74, method=6)
        for viejo in FOTOS.glob(f".{slug(p['sku'])}.*"):
            viejo.unlink()
        marca.touch()
    for archivo in FOTOS.glob("*.webp"):
        if archivo.name not in vigentes:
            archivo.unlink()
    for marca in FOTOS.glob(".*"):
        if f"{marca.name.split('.')[1]}.webp" not in vigentes:
            marca.unlink()
    DATOS.write_text(json.dumps(productos, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"Catálogo actualizado: {len(productos)} productos.")


def cargar() -> list[dict]:
    """Familias con sus productos, en el orden de Copper OS."""
    if not DATOS.exists():
        return []
    productos = json.loads(DATOS.read_text(encoding="utf-8"))
    familias: dict[int, dict] = {}
    for p in productos:
        f = p["familia"]
        if f["id"] not in familias:
            texto = FAMILIAS.get(f["prefijo"])
            familias[f["id"]] = {
                "prefijo": f["prefijo"],
                "nombre": f["nombre"],
                "orden": f["orden"],
                "slug": texto[0] if texto else slug(f["nombre"]),
                "titulo": texto[1] if texto else f["nombre"],
                "intro": texto[2] if texto else f"{f['nombre']} disponibles para cotizar con despacho en Salamanca y faenas del valle del Choapa.",
                "productos": [],
            }
        foto = f"/IMAGENES/productos/{slug(p['sku'])}.webp" if p.get("foto") and (FOTOS / f"{slug(p['sku'])}.webp").exists() else None
        familias[f["id"]]["productos"].append({**p, "foto_web": foto})
    lista = sorted(familias.values(), key=lambda f: f["orden"])
    for f in lista:
        f["foto"] = next((p["foto_web"] for p in f["productos"] if p["foto_web"]), FOTO_FAMILIA)
    return lista


def rutas() -> list[str]:
    familias = cargar()
    return (["/productos/"] + [f"/productos/{f['slug']}/" for f in familias]) if familias else []


def unidad(p: dict) -> str:
    return "por metro" if p["unidad_base"] == "m" else "por unidad"


def documento(*, titulo: str, descripcion: str, url: str, imagen: str, grafo: dict, cuerpo: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es-CL">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- Generado por herramientas/generar_catalogo.py desde el catálogo de Copper OS — no editar a mano. -->
<title>{E(titulo)}</title>
<meta name="description" content="{E(descripcion)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Copper Services SPA">
<meta property="og:locale" content="es_CL">
<meta property="og:title" content="{E(titulo)}">
<meta property="og:description" content="{E(descripcion)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITIO + imagen}">
<meta name="twitter:card" content="summary_large_image">
<meta name="geo.region" content="CL-CO">
<meta name="geo.placename" content="Salamanca">
<link rel="icon" type="image/png" href="/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@300;400;600;700&family=Barlow+Condensed:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/paginas.css">
{json_ld(grafo)}
</head>
<body>
{cabecera()}
<main>
{cuerpo}
</main>
{pie()}
</body>
</html>
"""


def hero(migas: str, titulo: str, resumen: str, wa_texto: str, cotizar: str) -> str:
    wa = f"https://wa.me/{TELEFONO_WA}?text=" + quote(wa_texto)
    return f"""  <section class="pg-hero pg-hero-corto" style="background-image:url('{FOTO_FAMILIA}')">
    <div class="pg-wrap">
      <nav aria-label="Ruta" class="pg-migas">{migas}</nav>
      <h1>{E(titulo)}</h1>
      <p class="pg-resumen">{E(resumen)}</p>
      <div class="pg-botones">
        <a class="pg-btn" href="{cotizar}">Cotizar en línea</a>
        <a class="pg-btn pg-btn-2" href="{wa}" target="_blank" rel="noopener">{ICONO_WA} WhatsApp</a>
      </div>
    </div>
  </section>"""


COMO_COMPRAR = f"""  <section class="pg-sec pg-gris">
    <div class="pg-wrap pg-dos">
      <div>
        <p class="pg-lbl">Cómo comprar</p>
        <h2>Cotice en minutos</h2>
        <ol class="pg-pasos pg-pasos-col">
          <li><strong>Arme su pedido.</strong> Elija los productos y cantidades en el <a href="{COTIZADOR}">cotizador en línea</a> o envíenos la lista por WhatsApp.</li>
          <li><strong>Reciba la cotización.</strong> Le respondemos con precios netos, disponibilidad y plazo.</li>
          <li><strong>Retiro o despacho.</strong> Retire en Salamanca o coordine la entrega en su obra o faena.</li>
        </ol>
      </div>
      <div class="pg-caja">
        <p class="pg-lbl">Cobertura</p>
        <h2>Dónde entregamos</h2>
        <p>Base en {E(DIRECCION)}. Atendemos {E(', '.join(ZONA[:-2]))}, el {E(ZONA[-2])} y la {E(ZONA[-1])}.</p>
        <p>¿Necesita un material que no está en la lista? Pídalo igual: lo conseguimos.</p>
        <p>Lunes a viernes, 08:00 – 18:00 hrs · <a href="tel:+{TELEFONO_WA}">{TELEFONO}</a></p>
      </div>
    </div>
  </section>"""


def tarjeta_producto(p: dict) -> str:
    foto = (f'<img src="{p["foto_web"]}" alt="{E(p["descripcion"])}" loading="lazy" width="240" height="240">'
            if p["foto_web"] else '<span class="pg-sinfoto" aria-hidden="true"></span>')
    marca = f'<span class="pg-marca">{E(p["marca"])}</span>' if p.get("marca") else ""
    detalle = f'<p class="pg-det">{E(recortar(p["detalle"].strip(), 220))}</p>' if p.get("detalle") else ""
    return f"""      <article class="pg-prod" id="{slug(p['sku'])}">
        {foto}
        <div>
          <h3>{E(p['descripcion'])}</h3>
          <p class="pg-meta">SKU {E(p['sku'])} · {unidad(p)}{' · ' if marca else ''}{marca}</p>
          {detalle}
          <a class="pg-prod-btn" href="{COTIZADOR}?p={quote(p['sku'])}">Cotizar</a>
        </div>
      </article>"""


def pagina_familia(f: dict, familias: list[dict]) -> str:
    u = f"{SITIO}/productos/{f['slug']}/"
    titulo = f"{f['titulo'].split(':')[0]} en Salamanca | Copper Services"
    descripcion = recortar(f"{f['intro']} Cotice en línea con despacho a obra y faena en el valle del Choapa.")
    productos = "\n".join(tarjeta_producto(p) for p in f["productos"])
    otras = "\n".join(
        f'        <li><a href="/productos/{o["slug"]}/">{E(o["nombre"])}</a></li>' for o in familias if o["slug"] != f["slug"]
    )
    grafo = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "name": f["titulo"],
                "url": u,
                "description": f["intro"],
                "isPartOf": {"@id": SITIO + "/#website"},
                "about": {"@id": SITIO + "/#business"},
            },
            {
                "@type": "OfferCatalog",
                "name": f"{f['nombre']} — Copper Services",
                "url": u,
                "itemListElement": [
                    {
                        "@type": "Offer",
                        "url": f"{u}#{slug(p['sku'])}",
                        "seller": {"@id": SITIO + "/#business"},
                        "areaServed": [{"@type": "Place", "name": z} for z in ZONA],
                        "itemOffered": {
                            "@type": "Product",
                            "name": p["descripcion"],
                            "sku": p["sku"],
                            "category": f["nombre"],
                            **({"brand": {"@type": "Brand", "name": p["marca"]}} if p.get("marca") else {}),
                            **({"image": SITIO + p["foto_web"]} if p["foto_web"] else {}),
                            **({"description": p["detalle"].strip()} if p.get("detalle") else {}),
                        },
                    }
                    for p in f["productos"]
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITIO + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Productos", "item": SITIO + "/productos/"},
                    {"@type": "ListItem", "position": 3, "name": f["nombre"], "item": u},
                ],
            },
        ],
    }
    cuerpo = f"""{hero(
        f'<a href="/">Inicio</a> / <a href="/productos/">Productos</a> / <span>{E(f["nombre"])}</span>',
        f["titulo"], f["intro"], f"Hola, quisiera cotizar {f['nombre'].lower()}.", f"{COTIZADOR}?f={quote(f['prefijo'])}",
    )}

  <section class="pg-sec">
    <div class="pg-wrap">
      <p class="pg-lbl">{len(f['productos'])} productos</p>
      <h2>{E(f['nombre'])}</h2>
      <div class="pg-prods">
{productos}
      </div>
    </div>
  </section>

{COMO_COMPRAR}

  <section class="pg-sec">
    <div class="pg-wrap">
      <p class="pg-lbl">Más productos</p>
      <h2>Otras familias del catálogo</h2>
      <ul class="pg-fams-lista">
{otras}
      </ul>
    </div>
  </section>"""
    return documento(titulo=titulo, descripcion=descripcion, url=u, imagen=f["foto"], grafo=grafo, cuerpo=cuerpo)


def pagina_indice(familias: list[dict]) -> str:
    u = SITIO + "/productos/"
    total = sum(len(f["productos"]) for f in familias)
    titulo = "Catálogo de materiales eléctricos en Salamanca | Copper Services"
    resumen = (f"{total} materiales eléctricos para obras, faenas e instalaciones: protecciones, cables, canalización, "
               "enchufes industriales, accesorios de tablero e iluminación. Cotice en línea y retire en Salamanca o reciba en su faena.")
    tarjetas = "\n".join(
        f"""      <a class="pg-otro pg-fam" href="/productos/{f['slug']}/">
        <img src="{f['foto']}" alt="{E(f['nombre'])}" loading="lazy" width="240" height="240">
        <span>{E(f['nombre'])}<small>{len(f['productos'])} productos</small></span>
      </a>"""
        for f in familias
    )
    grafo = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "name": "Catálogo de materiales eléctricos",
                "url": u,
                "description": resumen,
                "isPartOf": {"@id": SITIO + "/#website"},
                "about": {"@id": SITIO + "/#business"},
                "mainEntity": {
                    "@type": "ItemList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": i + 1, "name": f["nombre"], "url": f"{SITIO}/productos/{f['slug']}/"}
                        for i, f in enumerate(familias)
                    ],
                },
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITIO + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Productos", "item": u},
                ],
            },
        ],
    }
    cuerpo = f"""{hero('<a href="/">Inicio</a> / <span>Productos</span>', "Materiales eléctricos en Salamanca",
              resumen, "Hola, quisiera cotizar materiales eléctricos.", COTIZADOR)}

  <section class="pg-sec">
    <div class="pg-wrap">
      <p class="pg-lbl">Catálogo</p>
      <h2>Familias de productos</h2>
      <div class="pg-otros">
{tarjetas}
      </div>
      <p class="pg-nota">Además del catálogo, conseguimos materiales a pedido. Vea también nuestro servicio de <a href="/suministro-de-materiales/">suministro de materiales</a> para obras y faenas.</p>
    </div>
  </section>

{COMO_COMPRAR}"""
    return documento(titulo=titulo, descripcion=recortar(resumen), url=u, imagen=FOTO_FAMILIA, grafo=grafo, cuerpo=cuerpo)


def generar() -> int:
    """Escribe /productos/. Devuelve la cantidad de páginas."""
    familias = cargar()
    if not familias:
        print("Sin catálogo (herramientas/catalogo.json): corre con --actualizar.")
        return 0
    vigentes = {f["slug"] for f in familias}
    if SALIDA.exists():
        for carpeta in SALIDA.iterdir():
            if carpeta.is_dir() and carpeta.name not in vigentes:
                shutil.rmtree(carpeta)  # familia que ya no está en el catálogo
    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "index.html").write_text(pagina_indice(familias), encoding="utf-8", newline="\n")
    for f in familias:
        destino = SALIDA / f["slug"] / "index.html"
        destino.parent.mkdir(exist_ok=True)
        destino.write_text(pagina_familia(f, familias), encoding="utf-8", newline="\n")
    print(f"Catálogo: índice + {len(familias)} familias ({sum(len(f['productos']) for f in familias)} productos).")
    return len(familias) + 1


if __name__ == "__main__":
    if "--actualizar" in sys.argv:
        actualizar()
    generar()
    # El sitemap lo arma generar_paginas.py (servicios + catálogo).
    import generar_paginas

    generar_paginas.escribir_sitemap()
