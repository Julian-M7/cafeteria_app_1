"""
seed_inventario.py
====================
Script de utilidad para (re)generar data/json/inventario.json a partir
de la lista de precios inicial de la cafetería (LISTA_PRECIOS_CAFE.xlsx,
incluida como referencia en recursos/).

El archivo original sólo trae "Producto" y "Precio (COP)"; no trae una
columna de categoría. Como el enunciado exige que cada producto tenga
categoria = "Bebida" o "Comida" (sección 2.2), aquí se clasificó cada
uno de los 52 productos manualmente según su naturaleza.

Dos productos no son ni bebida ni comida en sentido estricto
("Cigarro" y "Rollo papel H.", papel higiénico) pero el enunciado sólo
permite esas dos categorías; se dejaron en "Comida" como categoría por
defecto (la que no es bebida). Si esto no es lo que se busca, puedes
reclasificarlos o eliminarlos libremente desde la pantalla de
Inventario una vez la aplicación esté corriendo.

Este script es IDEMPOTENTE respecto al archivo de datos: lo vuelve a
crear desde cero cada vez que se ejecuta. Úsalo sólo si quieres
restaurar el inventario a su estado inicial (por ejemplo, para
volver a calificar el proyecto desde cero):

    python3 seed_inventario.py
"""

from core.inventario import Inventario
from core import persistence as p

# (nombre, categoria, precio_cop) en el mismo orden que la lista original
PRODUCTOS_INICIALES = [
    ("Jugo litro", "Bebida", 4800),
    ("Pony Malta", "Bebida", 2200),
    ("Vive 100", "Bebida", 2200),
    ("Gatorade", "Bebida", 4400),
    ("Naty Malta", "Bebida", 2800),
    ("Agua botella peq.", "Bebida", 1200),
    ("Bretana", "Bebida", 4000),
    ("Agua bot. 60c", "Bebida", 2200),
    ("Agua litro", "Bebida", 2200),
    ("Agua saborizada", "Bebida", 2200),
    ("Cola y Pola", "Bebida", 3200),
    ("Jugo Caja", "Bebida", 2300),
    ("Gaseosa grande", "Bebida", 3300),
    ("Gaseosa peq.", "Bebida", 2300),
    ("Speed", "Bebida", 2500),
    ("Cerveza lata", "Bebida", 3700),
    ("Coronita", "Bebida", 4000),
    ("Cerveza botella", "Bebida", 3300),
    ("Trocipollo", "Comida", 2200),
    ("Tostaco", "Comida", 2200),
    ("Cheetos", "Comida", 2200),
    ("Tocineta", "Comida", 2200),
    ("Yups", "Comida", 2200),
    ("Chicharrón", "Comida", 3200),
    ("Papas", "Comida", 2500),
    ("Gall. Club Social", "Comida", 1100),
    ("Gall. Miel", "Comida", 1300),
    ("Cocosette", "Comida", 3000),
    ("Gall. Oreo", "Comida", 1600),
    ("Gall. Richs", "Comida", 1600),
    ("Ponqué Gala", "Comida", 2600),
    ("Barra chocol.", "Comida", 2600),
    ("Bocadillo", "Comida", 900),
    ("Bombón", "Comida", 1000),
    ("Almendra", "Comida", 3800),
    ("Trident x3", "Comida", 1100),
    ("Trident x5", "Comida", 1600),
    ("Trident x1", "Comida", 300),
    ("Empanada", "Comida", 3000),
    ("Arepa", "Comida", 2200),
    ("Cigarro", "Comida", 1000),          # ver nota arriba: no es comida real
    ("Maní", "Comida", 2200),
    ("Waffer Jet", "Comida", 3000),
    ("Tinto", "Bebida", 1600),
    ("Tinto Grande", "Bebida", 2200),
    ("Aromática", "Bebida", 1600),
    ("Aromática Grande", "Bebida", 2200),
    ("Perico", "Bebida", 2200),
    ("Café", "Bebida", 2900),
    ("Milo", "Bebida", 3100),
    ("Rollo papel H.", "Comida", 2500),   # ver nota arriba: no es comida real
    ("Limonada", "Bebida", 2600),
    ("Menú del día", "Restaurante", 16000),
    ("Menú ejecutivo", "Restaurante", 18000),
    ("Limonada", "Restaurante", 3000),
    ("Cerveza", "Restaurante", 4000),
    ("Adicional de huevo (1)", "Restaurante", 1500),
    ("Adicional de huevo (2)", "Restaurante", 2900),
    ("Sopa adicional", "Restaurante", 8500),
    ("Sopa con porción de arroz", "Restaurante", 10000),
    ("Menú especial", "Restaurante", 22000),
    ("Tinto Golden", "Restaurante", 1500),
    ("Desechables", "Restaurante", 1000),
    ("Medio runtazo", "Restaurante", 16000),
    ("Bandeja junior ejecutivo", "Restaurante", 16000),
    ("Bandeja junior casa", "Restaurante", 14000),
    ("Jarra chicha", "Restaurante", 3500),
    ("Vaso de chicha", "Restaurante", 2500),
    ("Botella chicha 1,5 L", "Restaurante", 10000),
]


def seed():
    inventario = Inventario()
    for nombre, categoria, precio in PRODUCTOS_INICIALES:
        inventario.agregar(nombre, categoria, str(precio))
    print(f"Inventario inicializado con {len(PRODUCTOS_INICIALES)} productos "
          f"en {p.INVENTARIO_PATH}")


if __name__ == "__main__":
    seed()
