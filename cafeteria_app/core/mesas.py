"""
mesas.py
=========
Gestión de las 5 mesas y sus pedidos independientes.

Se persiste en data/json/mesas.json como un objeto con 5 llaves
(mesa1..mesa5). Cada mesa contiene:
    {
        "productos": [
            {"idProducto": int, "nombre": str, "cantidad": int,
             "precioUnitario": Decimal}
        ],
        "pagada": bool,
        "metodoPago": None | "efectivo" | "transferencia",
        "totalPagado": Decimal
    }

Regla de negocio clave (precio congelado):
    Al agregar un producto a una mesa se copia su precio ACTUAL del
    inventario dentro de la línea del pedido ("precioUnitario"). Si el
    precio del producto cambia después en el inventario, los pedidos ya
    creados NO se ven afectados, porque ya no vuelven a leer el precio
    del inventario: usan el que quedó congelado en la línea.
"""

from decimal import Decimal

from . import persistence as p

NUM_MESAS = 16
NOMBRES_MESAS = [f"mesa{i}" for i in range(1, NUM_MESAS + 1)]

DOS_DECIMALES = Decimal("0.01")


def _mesa_vacia():
    return {
        "productos": [],
        "pagada": False,
        "metodoPago": None,
        "totalPagado": Decimal("0.00"),
    }


class Mesas:
    def __init__(self, ruta=None):
        self.ruta = ruta or p.MESAS_PATH
        self._mesas = {}
        self._nombres = list(NOMBRES_MESAS)
        self.cargar()

    # ---------- Persistencia ----------

    def cargar(self):
        valor_defecto = {nombre: self._serializar_mesa(_mesa_vacia()) for nombre in NOMBRES_MESAS}
        datos = p.leer_json(self.ruta, valor_defecto)

        nombres_extra = [
            nombre for nombre in datos
            if nombre.startswith("mesa") and nombre[4:].isdigit()
        ]
        self._nombres = sorted(set(NOMBRES_MESAS + nombres_extra),
                               key=lambda nombre: int(nombre[4:]))
        self._mesas = {}
        for nombre in self._nombres:
            mesa_json = datos.get(nombre) or self._serializar_mesa(_mesa_vacia())
            productos = []
            for item in mesa_json.get("productos", []):
                productos.append({
                    "idProducto": item["idProducto"],
                    "nombre": item["nombre"],
                    "cantidad": int(item["cantidad"]),
                    "precioUnitario": Decimal(str(item["precioUnitario"])),
                })
            self._mesas[nombre] = {
                "productos": productos,
                "pagada": bool(mesa_json.get("pagada", False)),
                "metodoPago": mesa_json.get("metodoPago"),
                "totalPagado": Decimal(str(mesa_json.get("totalPagado", "0.00"))),
            }

    def guardar(self):
        salida = {nombre: self._serializar_mesa(mesa) for nombre, mesa in self._mesas.items()}
        p.escribir_json(self.ruta, salida)

    @staticmethod
    def _serializar_mesa(mesa):
        return {
            "productos": [
                {
                    "idProducto": it["idProducto"],
                    "nombre": it["nombre"],
                    "cantidad": it["cantidad"],
                    "precioUnitario": str(it["precioUnitario"]),
                }
                for it in mesa["productos"]
            ],
            "pagada": mesa["pagada"],
            "metodoPago": mesa["metodoPago"],
            "totalPagado": str(mesa["totalPagado"]),
        }

    # ---------- Consultas ----------

    def nombres(self):
        return list(self._nombres)

    def agregar_mesa(self):
        siguiente = max(int(nombre[4:]) for nombre in self._nombres) + 1
        nombre = f"mesa{siguiente}"
        self._nombres.append(nombre)
        self._mesas[nombre] = _mesa_vacia()
        self.guardar()
        return nombre

    def _obtener_mesa(self, nombre_mesa):
        if nombre_mesa not in self._mesas:
            raise ValueError(f"Mesa inválida: {nombre_mesa}")
        return self._mesas[nombre_mesa]

    def obtener_pedido(self, nombre_mesa):
        return self._obtener_mesa(nombre_mesa)

    def lineas_con_subtotal(self, nombre_mesa):
        mesa = self._obtener_mesa(nombre_mesa)
        lineas = []
        for item in mesa["productos"]:
            subtotal = (item["precioUnitario"] * item["cantidad"]).quantize(DOS_DECIMALES)
            lineas.append({**item, "subtotal": subtotal})
        return lineas

    def calcular_total(self, nombre_mesa):
        total = Decimal("0.00")
        for linea in self.lineas_con_subtotal(nombre_mesa):
            total += linea["subtotal"]
        return total.quantize(DOS_DECIMALES)

    # ---------- Mutaciones ----------

    def agregar_producto(self, nombre_mesa, producto_inventario, cantidad=1):
        mesa = self._obtener_mesa(nombre_mesa)
        cantidad = int(cantidad)
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")

        precio_actual = Decimal(str(producto_inventario["precio"])).quantize(DOS_DECIMALES)

        # Si el mismo producto ya está en la mesa CON el mismo precio
        # congelado, se suma la cantidad en vez de crear una línea nueva.
        for item in mesa["productos"]:
            if item["idProducto"] == producto_inventario["id"] and item["precioUnitario"] == precio_actual:
                item["cantidad"] += cantidad
                self.guardar()
                return dict(mesa)

        mesa["productos"].append({
            "idProducto": producto_inventario["id"],
            "nombre": producto_inventario["nombre"],
            "cantidad": cantidad,
            "precioUnitario": precio_actual,  # precio CONGELADO al momento de agregar
        })
        self.guardar()
        return dict(mesa)

    def modificar_cantidad(self, nombre_mesa, indice_producto, nueva_cantidad):
        mesa = self._obtener_mesa(nombre_mesa)
        self._validar_indice(mesa, indice_producto)
        nueva_cantidad = int(nueva_cantidad)
        if nueva_cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")
        mesa["productos"][indice_producto]["cantidad"] = nueva_cantidad
        self.guardar()
        return dict(mesa)

    def eliminar_producto(self, nombre_mesa, indice_producto):
        mesa = self._obtener_mesa(nombre_mesa)
        self._validar_indice(mesa, indice_producto)
        mesa["productos"].pop(indice_producto)
        self.guardar()
        return dict(mesa)

    def reducir_productos(self, nombre_mesa, cantidades):
        """Reduce unidades de líneas después de un cobro parcial."""
        mesa = self._obtener_mesa(nombre_mesa)
        for indice, cantidad in sorted(cantidades, reverse=True):
            self._validar_indice(mesa, indice)
            cantidad = int(cantidad)
            disponible = mesa["productos"][indice]["cantidad"]
            if cantidad <= 0 or cantidad > disponible:
                raise ValueError("La cantidad a pagar no es válida para el producto seleccionado.")
            mesa["productos"][indice]["cantidad"] -= cantidad
            if mesa["productos"][indice]["cantidad"] == 0:
                mesa["productos"].pop(indice)
        self.guardar()
        return dict(mesa)

    def marcar_pagada(self, nombre_mesa, metodo_pago, total_pagado):
        mesa = self._obtener_mesa(nombre_mesa)
        mesa["pagada"] = True
        mesa["metodoPago"] = metodo_pago
        mesa["totalPagado"] = Decimal(str(total_pagado)).quantize(DOS_DECIMALES)
        self.guardar()

    def liberar_mesa(self, nombre_mesa):
        """Deja la mesa vacía y disponible para nuevos clientes."""
        self._obtener_mesa(nombre_mesa)  # valida que exista
        self._mesas[nombre_mesa] = _mesa_vacia()
        self.guardar()

    def liberar_todas(self):
        for nombre in self._nombres:
            self._mesas[nombre] = _mesa_vacia()
        self.guardar()

    @staticmethod
    def _validar_indice(mesa, indice):
        if not isinstance(indice, int) or indice < 0 or indice >= len(mesa["productos"]):
            raise ValueError("Producto no encontrado en el pedido de la mesa.")
