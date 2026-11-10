"""Genera las páginas de servicio, el sitemap y robots.txt de copper-services.cl.

Uso (desde la raíz del repo):
    python herramientas/generar_paginas.py            # páginas + sitemap + robots
    python herramientas/generar_paginas.py --imagenes # además convierte fotos a WebP (requiere Pillow)
    python herramientas/generar_paginas.py --catalogo # además baja el catálogo de Copper OS (ver generar_catalogo.py)

Cada servicio queda en /<slug>/index.html (GitHub Pages lo sirve como
https://copper-services.cl/<slug>/), con su título, descripción, canónica,
Open Graph y datos estructurados. Para cambiar textos, edita SERVICIOS y vuelve
a correr el script. Solo datos verdaderos: nada de cifras ni clientes que no se
puedan respaldar.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parent.parent
SITIO = "https://copper-services.cl"
TELEFONO = "+56 9 7370 6327"
TELEFONO_WA = "56973706327"
EMAIL = "Elazo@copper-services.com"
DIRECCION = "Alejandro Martínez N° 221, Salamanca"
COTIZADOR = "https://app.copper-services.cl/cotizar"
ZONA = ["Salamanca", "Illapel", "Los Vilos", "Canela", "valle del Choapa", "Región de Coquimbo"]

# Fotos originales → versión web (WebP, máx. 1280 px, nombre sin espacios).
IMAGENES = {
    "EQUIPOS EN FAENA.jpeg": "equipos-en-faena",
    "ARRIENDO y TRANSPORTE DE GENERADORES.jpeg": "arriendo-transporte-generadores",
    "CAMION GRUA VOLVO.jpeg": "camion-grua-volvo",
    "CAMION HINO PLANO.jpeg": "camion-hino-plano",
    "CAMIÓN GRUA MAN.jpeg": "camion-grua-man",
    "CITROEN BLANCO.jpeg": "vehiculo-operaciones",
    "PLUMA DAF.jpeg": "camion-pluma-daf",
    "RETROEXCAVADORA JHON DEERE.jpeg": "retroexcavadora-john-deere",
    "Suminstro 11.jpeg": "suministro-materiales",
    "bulldozers-mineria.jpeg": "bulldozers-mineria",
    "camion-agua-industrial.jpeg": "camion-agua-industrial",
    "equipo-proyeccion.jpeg": "equipo-proyeccion",
    "faena-industrial-grua.jpeg": "faena-industrial-grua",
    "faena-minera-maquinaria.jpeg": "faena-minera-maquinaria",
    "generador-portatil.jpeg": "generador-portatil",
    "generador-tablero-electrico.jpeg": "generador-tablero-electrico",
    "generadores-faena-01.jpeg": "generadores-faena-01",
    "generadores-faena-02.jpeg": "generadores-faena-02",
    "infraestructura-industrial.jpeg": "infraestructura-industrial",
    "mantencion-climatizacion.jpeg": "mantencion-climatizacion",
    "tuberias-agua-recuperada.jpeg": "tuberias-agua-recuperada",
}


def img(nombre: str) -> str:
    return f"/IMAGENES/web/{nombre}.webp"


SERVICIOS = [
    {
        "slug": "mantencion-de-generadores",
        "nombre": "Mantención de generadores",
        "titulo": "Mantención y reparación de generadores",
        "seo": "Mantención de generadores y grupos electrógenos en Salamanca",
        "imagen": "generadores-faena-01",
        "resumen": "Mantención preventiva y correctiva de grupos electrógenos en faena, campamentos e instalaciones industriales. Reparamos en terreno y entregamos informe técnico con registro fotográfico de cada intervención.",
        "incluye": [
            "Mantención preventiva según horas de uso y pauta del fabricante",
            "Reparación correctiva en terreno: fallas de arranque, regulación de voltaje (AVR), sistema de carga y combustible",
            "Habilitación y puesta en marcha de equipos nuevos o detenidos",
            "Revisión del tablero de control y de la transferencia",
            "Informe técnico con fotografías, hallazgos y recomendaciones",
        ],
        "faqs": [
            ("¿Atienden generadores en terreno?", "Sí. Nuestro equipo técnico va a la faena, campamento o instalación donde está el equipo, diagnostica y, cuando es posible, repara en el mismo lugar."),
            ("¿Entregan informe de la mantención?", "Sí. Cada intervención se documenta en un informe técnico con registro fotográfico, trabajos realizados y recomendaciones."),
            ("¿En qué zonas trabajan?", "Tenemos base en Salamanca y atendemos el valle del Choapa y la Región de Coquimbo. Para otras zonas, consúltenos según el proyecto."),
        ],
    },
    {
        "slug": "arriendo-de-generadores",
        "nombre": "Arriendo de generadores",
        "titulo": "Arriendo de generadores",
        "seo": "Arriendo de generadores en Salamanca y Región de Coquimbo",
        "imagen": "arriendo-transporte-generadores",
        "resumen": "Arriendo de generadores diésel sin operador para faenas, obras, campamentos y respaldo de energía. Coordinamos el transporte e instalación del equipo y su mantención durante el contrato.",
        "incluye": [
            "Generadores según la potencia que requiere su operación",
            "Arriendo sin operador: el equipo queda instalado y operando para su personal",
            "Transporte del equipo hasta la faena u obra",
            "Mantención del generador durante el periodo de arriendo",
            "Arriendo mensual con orden de compra y estado de pago",
            "Asesoría para dimensionar la potencia necesaria",
        ],
        "faqs": [
            ("¿Qué necesito para cotizar un generador?", "La potencia o los equipos que va a alimentar, el lugar de instalación y el plazo del arriendo. Si no conoce la potencia, le ayudamos a estimarla."),
            ("¿El arriendo incluye operador?", "No. Los generadores se arriendan sin operador: los dejamos instalados y funcionando, y nos encargamos de su mantención durante el contrato."),
            ("¿Incluye el transporte?", "Coordinamos el traslado del equipo hasta su faena u obra; el valor depende de la distancia y se detalla en la cotización."),
        ],
    },
    {
        "slug": "tableros-e-instalaciones-electricas",
        "nombre": "Tableros e instalaciones eléctricas",
        "titulo": "Tableros e instalaciones eléctricas industriales",
        "seo": "Tableros e instalaciones eléctricas industriales en Salamanca",
        "imagen": "generador-tablero-electrico",
        "resumen": "Revisión, habilitación y mantención de tableros eléctricos, e instalaciones eléctricas para faenas, talleres y recintos industriales, con checklist firmado por el eléctrico a cargo.",
        "incluye": [
            "Revisión y habilitación de tableros eléctricos",
            "Instalaciones eléctricas industriales y de faena",
            "Mantención preventiva y correctiva de tableros y circuitos",
            "Conexión de generadores, transferencias y equipos",
            "Checklist e informe de cada trabajo realizado",
        ],
        "faqs": [
            ("¿Revisan tableros que ya están instalados?", "Sí. Revisamos el estado del tablero y sus protecciones, corregimos lo necesario y lo dejamos habilitado, con checklist del trabajo."),
            ("¿Trabajan en faena minera?", "Sí, trabajamos en faenas e instalaciones industriales de la Región de Coquimbo cumpliendo los protocolos de seguridad de cada recinto."),
        ],
    },
    {
        "slug": "arriendo-de-equipos",
        "nombre": "Arriendo de equipos y vehículos",
        "titulo": "Arriendo de equipos, maquinaria y vehículos",
        "seo": "Arriendo de equipos, maquinaria y vehículos para faena en Salamanca",
        "imagen": "retroexcavadora-john-deere",
        "resumen": "Arriendo sin operador de equipos industriales, maquinaria y vehículos para faenas y proyectos: camionetas, camiones, retroexcavadoras, camiones grúa y generadores, con contrato mensual y facturación contra orden de compra.",
        "incluye": [
            "Camionetas y vehículos de apoyo para faena",
            "Retroexcavadoras y maquinaria para movimiento de tierra",
            "Camiones grúa, camiones pluma y camiones planos",
            "Generadores y equipos industriales",
            "Contrato mensual con orden de compra y estado de pago",
            "Arriendo sin operador",
        ],
        "faqs": [
            ("¿Cómo se factura el arriendo?", "El arriendo se factura de forma mensual, contra la orden de compra de su empresa y, cuando corresponde, el estado de pago aprobado."),
            ("¿Qué equipos tienen disponibles?", "La disponibilidad cambia según los contratos vigentes. Revise el catálogo en línea o escríbanos con el equipo y el plazo que necesita."),
        ],
    },
    {
        "slug": "suministro-de-materiales",
        "nombre": "Suministro de materiales",
        "titulo": "Suministro de materiales y repuestos industriales",
        "seo": "Suministro de materiales y repuestos industriales para minería",
        "imagen": "suministro-materiales",
        "resumen": "Suministro de repuestos, insumos industriales y materiales eléctricos para faenas y talleres. Cotice en línea desde nuestro catálogo y coordinamos la entrega en la zona.",
        "incluye": [
            "Repuestos e insumos para equipos industriales y generadores",
            "Materiales eléctricos: cables, protecciones y componentes de tableros",
            "Consumibles y materiales para mantención",
            "Búsqueda de productos especiales a pedido",
            "Despacho coordinado a Salamanca y alrededores",
        ],
        "faqs": [
            ("¿Cómo cotizo materiales?", "Puede armar su solicitud en el catálogo en línea o enviarnos el listado por WhatsApp o correo; le respondemos con la cotización."),
            ("¿Consiguen productos que no están en el catálogo?", "Sí. Si necesita un repuesto o material específico, envíenos la referencia y lo buscamos con nuestros proveedores."),
        ],
        "catalogo": True,
    },
    {
        "slug": "climatizacion-y-compresores",
        "nombre": "Climatización y compresores",
        "titulo": "Instalación de aire acondicionado, compresores y filtros",
        "seo": "Instalación de aire acondicionado y compresores industriales en Salamanca",
        "imagen": "mantencion-climatizacion",
        "resumen": "Instalación y mantención de equipos de aire acondicionado, compresores y filtros de presión en oficinas de faena, salas eléctricas, talleres e instalaciones industriales.",
        "incluye": [
            "Instalación de equipos de aire acondicionado",
            "Instalación de compresores y sus conexiones",
            "Instalación y cambio de filtros de presión",
            "Mantención preventiva de los equipos instalados",
            "Informe del trabajo con registro fotográfico",
        ],
        "faqs": [
            ("¿Hacen la mantención de equipos que ya existen?", "Sí. Además de instalar, realizamos la mantención preventiva y correctiva de equipos de climatización y compresores."),
            ("¿Trabajan en instalaciones de faena?", "Sí, en oficinas de faena, salas eléctricas, talleres y recintos industriales de la Región de Coquimbo."),
        ],
    },
    {
        "slug": "carrozado-minero",
        "nombre": "Carrozado minero",
        "titulo": "Carrozado estándar minero para vehículos",
        "seo": "Carrozado estándar minero para camionetas y vehículos",
        "imagen": "vehiculo-operaciones",
        "resumen": "Equipamos camionetas y vehículos de apoyo con el estándar minero que exige cada faena para autorizar su ingreso, y dejamos registro de los elementos instalados.",
        "incluye": [
            "Revisión del estándar de acceso que pide su faena",
            "Instalación de los elementos exigidos (por ejemplo pértiga, baliza y accesorios de seguridad)",
            "Adaptaciones de carrocería para el trabajo en terreno",
            "Registro fotográfico de la instalación para la acreditación",
        ],
        "faqs": [
            ("¿Qué incluye el estándar minero?", "Cada faena define su propio estándar de acceso. Revisamos el reglamento que le entregan y cotizamos los elementos que faltan en su vehículo."),
            ("¿Cuánto demora el carrozado?", "Depende de los elementos que necesite el vehículo y de la disponibilidad de materiales; el plazo se indica en la cotización."),
        ],
    },
    {
        "slug": "transporte-y-logistica",
        "nombre": "Transporte y logística",
        "titulo": "Transporte de equipos y materiales a faena",
        "seo": "Transporte de equipos y materiales a faena en Región de Coquimbo",
        "imagen": "camion-hino-plano",
        "resumen": "Transporte de equipos, generadores y materiales hacia faenas y proyectos, con camión plano y camión grúa para carga y descarga.",
        "incluye": [
            "Traslado de generadores y equipos industriales",
            "Transporte de materiales y repuestos a faena",
            "Carga y descarga con camión grúa",
            "Coordinación de horarios y accesos con la faena",
        ],
        "faqs": [
            ("¿Qué información necesitan para cotizar un traslado?", "Origen, destino, tipo y peso aproximado de la carga, y la fecha requerida."),
            ("¿Cubren rutas fuera de la Región de Coquimbo?", "Nuestra base es Salamanca; para traslados a otras regiones, consúltenos según la carga y el destino."),
        ],
    },
]

E = html.escape


def url(s: dict) -> str:
    return f"/{s['slug']}/"


def recortar(texto: str, n: int = 158) -> str:
    if len(texto) <= n:
        return texto
    corte = texto[: texto.rfind(" ", 0, n - 1)].rstrip(",.;:")
    return corte + "…"


def json_ld(obj: dict) -> str:
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


ICONO_WA = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 0C5.373 0 0 5.373 0 12c0 2.124.554 4.118 1.528 5.847L.057 23.743a.5.5 0 00.612.612l5.896-1.47A11.952 11.952 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.9 0-3.677-.513-5.2-1.407l-.373-.22-3.864.963.964-3.864-.22-.373A9.952 9.952 0 012 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z"/></svg>'


def cabecera() -> str:
    return f"""<header class="pg-nav">
  <a href="/" class="pg-logo"><img src="/logo.png" alt="Copper Services SPA" width="120" height="48"></a>
  <nav aria-label="Principal">
    <a href="/#servicios">Servicios</a>
    <a href="/productos/">Productos</a>
    <a href="/#nosotros">Nosotros</a>
    <a href="/#ubicacion">Ubicación</a>
    <a href="{COTIZADOR}" class="pg-cotizar">Cotizar</a>
  </nav>
</header>"""


def pie() -> str:
    enlaces = "\n".join(f'        <li><a href="{url(s)}">{E(s["nombre"])}</a></li>' for s in SERVICIOS)
    enlaces += '\n        <li><a href="/productos/">Catálogo de materiales eléctricos</a></li>'
    return f"""<footer class="pg-pie">
  <div class="pg-wrap pg-pie-grid">
    <div>
      <img src="/logo.png" alt="Copper Services SPA" width="140" height="56" loading="lazy">
      <p>Soporte industrial y minero desde Salamanca, Región de Coquimbo.</p>
    </div>
    <div>
      <h2>Servicios</h2>
      <ul>
{enlaces}
      </ul>
    </div>
    <div>
      <h2>Contacto</h2>
      <ul>
        <li><a href="tel:+{TELEFONO_WA}">{TELEFONO}</a></li>
        <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
        <li>{E(DIRECCION)}</li>
        <li>Lunes a viernes, 08:00 – 18:00 hrs</li>
        <li>RUT 77.396.139-5</li>
      </ul>
    </div>
  </div>
  <p class="pg-copy">© {date.today().year} Copper Services SPA</p>
</footer>
<a href="https://wa.me/{TELEFONO_WA}" class="pg-wa" target="_blank" rel="noopener" aria-label="Escríbanos por WhatsApp">{ICONO_WA}</a>"""


def pagina(s: dict) -> str:
    u = SITIO + url(s)
    imagen = SITIO + img(s["imagen"])
    titulo = f"{s['seo']} | Copper Services"
    descripcion = recortar(s["resumen"])
    wa = f"https://wa.me/{TELEFONO_WA}?text=" + quote(f"Hola, quisiera cotizar: {s['nombre'].lower()}.")
    incluye = "\n".join(f"        <li>{E(t)}</li>" for t in s["incluye"])
    faqs = "\n".join(
        f"""      <details{' open' if i == 0 else ''}>
        <summary>{E(p)}</summary>
        <p>{E(r)}</p>
      </details>"""
        for i, (p, r) in enumerate(s["faqs"])
    )
    otros = "\n".join(
        f"""      <a class="pg-otro" href="{url(o)}">
        <img src="{img(o['imagen'])}" alt="{E(o['titulo'])}" loading="lazy" width="400" height="260">
        <span>{E(o['nombre'])}</span>
      </a>"""
        for o in SERVICIOS
        if o["slug"] != s["slug"]
    )
    grafo = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Service",
                "name": s["titulo"],
                "description": s["resumen"],
                "url": u,
                "image": imagen,
                "provider": {"@id": SITIO + "/#business"},
                "areaServed": [{"@type": "Place", "name": z} for z in ZONA],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITIO + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Servicios", "item": SITIO + "/#servicios"},
                    {"@type": "ListItem", "position": 3, "name": s["nombre"], "item": u},
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": p, "acceptedAnswer": {"@type": "Answer", "text": r}}
                    for p, r in s["faqs"]
                ],
            },
        ],
    }
    return f"""<!DOCTYPE html>
<html lang="es-CL">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- Generado por herramientas/generar_paginas.py — editar ahí, no a mano. -->
<title>{E(titulo)}</title>
<meta name="description" content="{E(descripcion)}">
<link rel="canonical" href="{u}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Copper Services SPA">
<meta property="og:locale" content="es_CL">
<meta property="og:title" content="{E(titulo)}">
<meta property="og:description" content="{E(descripcion)}">
<meta property="og:url" content="{u}">
<meta property="og:image" content="{imagen}">
<meta name="twitter:card" content="summary_large_image">
<meta name="geo.region" content="CL-CO">
<meta name="geo.placename" content="Salamanca">
<link rel="icon" type="image/png" href="/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@300;400;600;700&family=Barlow+Condensed:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/paginas.css">
<link rel="preload" as="image" href="{img(s['imagen'])}">
{json_ld(grafo)}
</head>
<body>
{cabecera()}
<main>
  <section class="pg-hero" style="background-image:url('{img(s['imagen'])}')">
    <div class="pg-wrap">
      <nav aria-label="Ruta" class="pg-migas"><a href="/">Inicio</a> / <a href="/#servicios">Servicios</a> / <span>{E(s['nombre'])}</span></nav>
      <h1>{E(s['titulo'])}</h1>
      <p class="pg-resumen">{E(s['resumen'])}</p>
      <div class="pg-botones">
        <a class="pg-btn" href="{wa}" target="_blank" rel="noopener">{ICONO_WA} Cotizar por WhatsApp</a>
        <a class="pg-btn pg-btn-2" href="{'/productos/' if s.get('catalogo') else COTIZADOR}">Ver catálogo{' de productos' if s.get('catalogo') else ' y cotizar'}</a>
      </div>
    </div>
  </section>

  <section class="pg-sec">
    <div class="pg-wrap pg-dos">
      <div>
        <p class="pg-lbl">Qué incluye</p>
        <h2>Qué hacemos</h2>
        <ul class="pg-lista">
{incluye}
        </ul>
      </div>
      <div class="pg-caja">
        <p class="pg-lbl">Cobertura</p>
        <h2>Dónde trabajamos</h2>
        <p>Base en {E(DIRECCION)}. Atendemos {E(', '.join(ZONA[:-2]))}, el {E(ZONA[-2])} y la {E(ZONA[-1])}.</p>
        <p>Lunes a viernes, 08:00 – 18:00 hrs · <a href="tel:+{TELEFONO_WA}">{TELEFONO}</a></p>
      </div>
    </div>
  </section>

  <section class="pg-sec pg-gris">
    <div class="pg-wrap">
      <p class="pg-lbl">Cómo trabajamos</p>
      <h2>Tres pasos</h2>
      <ol class="pg-pasos">
        <li><strong>Diagnóstico y levantamiento.</strong> Entendemos su necesidad, plazos y condiciones de la faena.</li>
        <li><strong>Propuesta técnica y comercial.</strong> Alcance, plazos y valores claros.</li>
        <li><strong>Ejecución y seguimiento.</strong> Trabajo en terreno con informe y comunicación directa.</li>
      </ol>
    </div>
  </section>

  <section class="pg-sec">
    <div class="pg-wrap">
      <p class="pg-lbl">Preguntas frecuentes</p>
      <h2>Lo que más nos consultan</h2>
      <div class="pg-faq">
{faqs}
      </div>
    </div>
  </section>

  <section class="pg-sec pg-gris">
    <div class="pg-wrap">
      <p class="pg-lbl">Más servicios</p>
      <h2>Otros servicios de Copper</h2>
      <div class="pg-otros">
{otros}
      </div>
    </div>
  </section>
</main>
{pie()}
</body>
</html>
"""


def convertir_imagenes() -> None:
    from PIL import Image

    origen = RAIZ / "IMAGENES"
    destino = origen / "web"
    destino.mkdir(exist_ok=True)
    for archivo, nombre in IMAGENES.items():
        im = Image.open(origen / archivo)
        im = im.convert("RGB")
        im.thumbnail((1280, 1280))
        salida = destino / f"{nombre}.webp"
        im.save(salida, "WEBP", quality=72, method=6)
        print(f"{archivo} → {salida.name} ({(origen / archivo).stat().st_size // 1024} KB → {salida.stat().st_size // 1024} KB)")


def main() -> None:
    if "--imagenes" in sys.argv:
        convertir_imagenes()
    for s in SERVICIOS:
        destino = RAIZ / s["slug"] / "index.html"
        destino.parent.mkdir(exist_ok=True)
        destino.write_text(pagina(s), encoding="utf-8", newline="\n")
    (RAIZ / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITIO}/sitemap.xml\n", encoding="utf-8", newline="\n")
    import generar_catalogo

    if "--catalogo" in sys.argv:
        generar_catalogo.actualizar()
    generar_catalogo.generar()
    total = escribir_sitemap()
    print(f"{len(SERVICIOS)} páginas de servicio, sitemap con {total} URLs y robots.txt listos.")


def escribir_sitemap() -> int:
    from generar_catalogo import rutas

    hoy = date.today().isoformat()
    urls = [("/", "1.0")] + [(url(s), "0.8") for s in SERVICIOS] + [(r, "0.7") for r in rutas()]
    (RAIZ / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(f"  <url><loc>{SITIO}{u}</loc><lastmod>{hoy}</lastmod><priority>{p}</priority></url>" for u, p in urls)
        + "\n</urlset>\n",
        encoding="utf-8",
        newline="\n",
    )
    return len(urls)


if __name__ == "__main__":
    main()
