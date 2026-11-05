"""mapa.py: dibuja el mapa de barrios con NetworkX y matplotlib."""
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Patch

from db import obtener_sedes
from rutas import cargar_grafo_nx

# Posición (x, y) de cada barrio en el dibujo, copiada del mapa de clase.
# Sin esto NetworkX los colocaría al azar y el dibujo cambiaría cada vez.
# Las y están al revés (en una imagen crecen hacia abajo), por eso se les cambia el signo.
_PIXELES = {
    "Tetuán": (736, 318), "Moncloa": (563, 385), "Chamberí": (720, 425),
    "Centro": (712, 532), "Latina": (572, 557), "Vallecas": (894, 631),
    "Carabanchel": (580, 672), "Usera": (728, 672),
}
POSICIONES = {barrio: (x, -y) for barrio, (x, y) in _PIXELES.items()}

COLOR_NORMAL = "#6AAFBF"      # barrio sin restaurante
COLOR_SEDE = "#E8A0B4"        # barrio con restaurante (sede)
COLOR_RUTA = "#F5B041"        # barrio por el que pasa la ruta resaltada
COLOR_TRAMO = "#C9B8D0"       # tramo normal
COLOR_TRAMO_RUTA = "#D62728"  # tramo de la ruta resaltada


def dibujar_mapa(ruta=None, archivo=None):
    """Dibuja los barrios (nodos) y los tramos (aristas, con sus minutos).
    ruta: lista de barrios que se resalta. archivo: nombre .png donde guardar el dibujo."""
    G = cargar_grafo_nx()                         # el mapa como grafo de NetworkX
    ruta = ruta or []
    barrios_sede = {barrio for _, barrio in obtener_sedes()}

    # Los tramos de la ruta, en las dos direcciones (el grafo no es dirigido)
    tramos_ruta = set(zip(ruta, ruta[1:])) | set(zip(ruta[1:], ruta))

    # Un color por nodo: la ruta manda sobre las sedes y estas sobre el resto
    colores_nodos = []
    for barrio in G.nodes:
        if barrio in ruta:
            colores_nodos.append(COLOR_RUTA)
        elif barrio in barrios_sede:
            colores_nodos.append(COLOR_SEDE)
        else:
            colores_nodos.append(COLOR_NORMAL)

    # Color y grosor de cada tramo: rojo y grueso si está en la ruta
    colores_tramos = [COLOR_TRAMO_RUTA if (u, v) in tramos_ruta else COLOR_TRAMO for u, v in G.edges]
    grosores = [5 if (u, v) in tramos_ruta else 2.5 for u, v in G.edges]

    # Los minutos que se escriben encima de cada tramo
    minutos = {(u, v): datos["weight"] for u, v, datos in G.edges(data=True)}

    plt.figure(figsize=(8, 7))
    nx.draw_networkx_edges(G, POSICIONES, edge_color=colores_tramos, width=grosores)
    nx.draw_networkx_nodes(G, POSICIONES, node_color=colores_nodos, node_size=2800)
    nx.draw_networkx_labels(G, POSICIONES, font_size=8, font_weight="bold")
    nx.draw_networkx_edge_labels(G, POSICIONES, edge_labels=minutos, font_size=9)

    leyenda = [Patch(color=COLOR_SEDE, label="Barrio con restaurante"),
               Patch(color=COLOR_NORMAL, label="Otro barrio")]
    if ruta:
        leyenda.insert(0, Patch(color=COLOR_RUTA, label="Ruta: " + " → ".join(ruta)))
    # La leyenda va DEBAJO del dibujo para no tapar ningún barrio
    plt.legend(handles=leyenda, loc="upper center", bbox_to_anchor=(0.5, 0.0), fontsize=8)
    plt.title("Mapa de RiderExpress (minutos en moto)")
    plt.axis("off")
    plt.tight_layout()

    if archivo:
        plt.savefig(archivo, dpi=150, bbox_inches="tight")   # guardar ANTES de show(), que cierra la figura
    plt.show()                                    # abre la ventana; el programa sigue al cerrarla