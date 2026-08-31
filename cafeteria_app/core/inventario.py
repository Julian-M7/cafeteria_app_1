"""
inventario.py
===============
Gestión del inventario de productos de la cafetería.

Cada producto se representa internamente como:
    {
        "id": int,
        "nombre": str,
        "categoria": "Bebida" | "Comida",
        "precio": Decimal
    }

Se persiste en data/json/inventario.json como un arreglo de objetos
(con "precio" serializado como string para no perder precisión).

Regla de negocio importante: modificar o eliminar un producto del
inventario NUNCA afecta pedidos ya existentes en las mesas, porque el
módulo `mesas` congela nombre y precio unitario en el momento en que el
producto se agrega a una mesa (ver mesas.py). Este módulo sólo gestiona
el catálogo "vivo" de productos disponibles para nuevas ventas.
"""

from decimal import Decimal

from . import persistence as p

CATEGORIAS_VALIDAS = ("Bebida", "Comida", "Restaurante")


class Inventario:
    def __init__(self, ruta=None):
        self.ruta = ruta or p.INVENTARIO_PATH
        self._productos = {}
        self.cargar()

    # ---------- Persistencia ----------

    def cargar(self):
        datos = p.leer_json(self.ruta, [])
        self._productos = {}
        for item in datos:
            id_producto = int(item["id"])
            self._productos[id_producto] = {
                "id": id_producto,
                "nombre": item["nombre"],
                "categoria": item["categoria"],
                "precio": Decimal(str(item["precio"])),
            }

    def guardar(self):
        datos = [self._serializar(prod) for prod in self.listar()]
        p.escribir_json(self.ruta, datos)

    @staticmethod
    def _serializar(prod):
        return {
            "id": prod["id"],
            "nombre": prod["nombre"],
            "categoria": prod["categoria"],
            "precio": str(prod["precio"]),
        }

    # ---------- Consultas ----------

    def listar(self, categoria=None):
        """Lista los productos, opcionalmente filtrados por categoría.
        `categoria` puede ser None, "Todas", "Bebida", "Comida" o "Restaurante"."""
        productos = list(self._productos.values())
        if categoria and categoria != "Todas":
            productos = [pr for pr in productos if pr["categoria"] == categoria]
        return sorted(productos, key=lambda x: x["id"])

    def buscar(self, texto, categoria=None):
        """Busca coincidencias por nombre, sin distinguir mayúsculas/minúsculas."""
        texto = (texto or "").strip().lower()
        if not texto:
            return self.listar(categoria)
        productos = self.listar(categoria)
        return [prod for prod in productos if texto in prod["nombre"].lower()]

    def obtener(self, id_producto):
        return self._productos.get(int(id_producto))

    def _siguiente_id(self):
        if not self._productos:
            return 1
        return max(self._productos.keys()) + 1

    # ---------- Mutaciones ----------

    def agregar(self, nombre, categoria, precio):
        nombre = self._validar_nombre(nombre)
        categoria = self._validar_categoria(categoria)
        precio_dec = self._validar_precio(precio)

        nuevo_id = self._siguiente_id()
        self._productos[nuevo_id] = {
            "id": nuevo_id,
            "nombre": nombre,
            "categoria": categoria,
            "precio": precio_dec,
        }
        self.guardar()
        return dict(self._productos[nuevo_id])

    def modificar(self, id_producto, nombre=None, categoria=None, precio=None):
        prod = self.obtener(id_producto)
        if prod is None:
            raise ValueError(f"No existe un producto con id {id_producto}.")

        if nombre is not None:
            prod["nombre"] = self._validar_nombre(nombre)
        if categoria is not None:
            prod["categoria"] = self._validar_categoria(categoria)
        if precio is not None:
            prod["precio"] = self._validar_precio(precio)

        self.guardar()
        return dict(prod)

    def eliminar(self, id_producto):
        id_producto = int(id_producto)
        if id_producto not in self._productos:
            raise ValueError(f"No existe un producto con id {id_producto}.")
        del self._productos[id_producto]
        self.guardar()

    # ---------- Validaciones ----------

    @staticmethod
    def _validar_nombre(nombre):
        nombre = (nombre or "").strip()
        if not nombre:
            raise ValueError("El nombre del producto no puede estar vacío.")
        return nombre

    @staticmethod
    def _validar_categoria(categoria):
        if categoria not in CATEGORIAS_VALIDAS:
            raise ValueError("La categoría debe ser 'Bebida', 'Comida' o 'Restaurante'.")
        return categoria

    @staticmethod
    def _validar_precio(precio):
        valor = precio if isinstance(precio, Decimal) else Decimal(str(precio))
        if valor <= 0:
            raise ValueError("El precio debe ser mayor que cero.")
        return valor.quantize(Decimal("0.01"))
