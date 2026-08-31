"""
controller.py
===============
Controlador / fachada central de la aplicación. Coordina Inventario,
Mesas y Cierre, y es el ÚNICO punto que la interfaz gráfica debe usar
para ejecutar operaciones de negocio (la GUI nunca debería llamar a
Inventario/Mesas/Cierre directamente, salvo para lecturas simples).

Esto mantiene la lógica de negocio completamente independiente de
Tkinter: se podría reemplazar toda la carpeta gui/ por una interfaz de
consola o web sin tocar una sola línea de core/.
"""

from decimal import Decimal

from . import money
from .cierre import Cierre
from .inventario import Inventario
from .mesas import Mesas

USUARIO_VALIDO = "hattu"
CONTRASENA_VALIDA = "12345"

DOS_DECIMALES = Decimal("0.01")


class CobroError(Exception):
    """Error de validación durante el proceso de cobro (monto inválido,
    insuficiente, campo vacío, mesa sin productos, etc.)."""
    pass


class AppController:
    def __init__(self, ruta_inventario=None, ruta_mesas=None, ruta_cierre=None):
        self.inventario = Inventario(ruta_inventario)
        self.mesas = Mesas(ruta_mesas)
        self.cierre = Cierre(ruta_cierre)
        self.autenticado = False

    # ================= Login =================

    def iniciar_sesion(self, usuario, contrasena):
        ok = usuario == USUARIO_VALIDO and contrasena == CONTRASENA_VALIDA
        self.autenticado = ok
        return ok

    # ================= Inventario =================

    def listar_productos(self, categoria=None):
        return self.inventario.listar(categoria)

    def buscar_productos(self, texto, categoria=None):
        return self.inventario.buscar(texto, categoria)

    def agregar_producto(self, nombre, categoria, precio_texto):
        precio, error = money.parse_monto(precio_texto)
        if error:
            raise ValueError(error)
        return self.inventario.agregar(nombre, categoria, precio)

    def modificar_producto(self, id_producto, nombre=None, categoria=None, precio_texto=None):
        precio = None
        if precio_texto is not None:
            precio, error = money.parse_monto(precio_texto)
            if error:
                raise ValueError(error)
        return self.inventario.modificar(id_producto, nombre, categoria, precio)

    def eliminar_producto(self, id_producto):
        self.inventario.eliminar(id_producto)

    # ================= Ventas / Mesas =================

    def nombres_mesas(self):
        return self.mesas.nombres()

    def agregar_mesa(self):
        return self.mesas.agregar_mesa()

    def lineas_mesa(self, nombre_mesa):
        return self.mesas.lineas_con_subtotal(nombre_mesa)

    def total_mesa(self, nombre_mesa):
        return self.mesas.calcular_total(nombre_mesa)

    def agregar_a_mesa(self, nombre_mesa, id_producto, cantidad=1):
        producto = self.inventario.obtener(id_producto)
        if producto is None:
            raise ValueError("Producto no encontrado en el inventario.")
        return self.mesas.agregar_producto(nombre_mesa, producto, cantidad)

    def modificar_cantidad_mesa(self, nombre_mesa, indice, cantidad):
        return self.mesas.modificar_cantidad(nombre_mesa, indice, cantidad)

    def eliminar_de_mesa(self, nombre_mesa, indice):
        return self.mesas.eliminar_producto(nombre_mesa, indice)

    # ================= Cobro =================

    def preparar_cobro(self, nombre_mesa):
        """Datos necesarios para mostrar el panel de cobro. Lanza
        CobroError si la mesa no tiene productos que cobrar."""
        lineas = self.mesas.lineas_con_subtotal(nombre_mesa)
        if not lineas:
            raise CobroError("La mesa no tiene productos para cobrar.")
        return {"lineas": lineas, "total": self.mesas.calcular_total(nombre_mesa)}

    def cobrar_mesa(self, nombre_mesa, metodo_pago, monto_texto=None):
        """
        Cobra una mesa: valida el monto (efectivo) o autocompleta con el
        total (transferencia), registra la venta en el cierre y libera
        la mesa para nuevos clientes. Es la única forma de que una venta
        entre al módulo de cierre, por lo que el cierre SIEMPRE refleja
        únicamente mesas efectivamente cobradas.
        """
        lineas = self.mesas.lineas_con_subtotal(nombre_mesa)
        if not lineas:
            raise CobroError("La mesa no tiene productos para cobrar.")

        return self.cobrar_seleccion_mesa(
            nombre_mesa,
            [(indice, linea["cantidad"]) for indice, linea in enumerate(lineas)],
            metodo_pago,
            monto_texto,
        )

    def cobrar_seleccion_mesa(self, nombre_mesa, selecciones, metodo_pago, monto_texto=None):
        """Cobra unidades seleccionadas y conserva en la mesa lo pendiente."""
        lineas = self.mesas.lineas_con_subtotal(nombre_mesa)
        if not lineas or not selecciones:
            raise CobroError("Selecciona al menos un producto para cobrar.")

        lineas_cobradas = []
        cantidades_validas = []
        for indice, cantidad in selecciones:
            if not isinstance(indice, int) or indice < 0 or indice >= len(lineas):
                raise CobroError("Producto seleccionado inválido.")
            cantidad = int(cantidad)
            if cantidad <= 0 or cantidad > lineas[indice]["cantidad"]:
                raise CobroError("La cantidad seleccionada no es válida.")
            linea = dict(lineas[indice])
            linea["cantidad"] = cantidad
            linea["subtotal"] = (linea["precioUnitario"] * cantidad).quantize(DOS_DECIMALES)
            lineas_cobradas.append(linea)
            cantidades_validas.append((indice, cantidad))

        total = sum((linea["subtotal"] for linea in lineas_cobradas), Decimal("0.00"))
        total = total.quantize(DOS_DECIMALES)

        if metodo_pago == "efectivo":
            recibido, error = money.parse_monto(monto_texto)
            if error:
                raise CobroError(error)
            if recibido < total:
                faltante = (total - recibido).quantize(DOS_DECIMALES)
                raise CobroError(f"Monto insuficiente. Falta: {money.formatear_monto(faltante)}")
            cambio = (recibido - total).quantize(DOS_DECIMALES)
        elif metodo_pago == "transferencia":
            # El monto se autocompleta con el total; no se permite editar
            # manualmente y no hay cambio a entregar.
            recibido = total
            cambio = Decimal("0.00")
        else:
            raise CobroError("Método de pago inválido. Use 'efectivo' o 'transferencia'.")

        self.cierre.registrar_venta(lineas_cobradas, metodo_pago, nombre_mesa)
        self.mesas.reducir_productos(nombre_mesa, cantidades_validas)
        if not self.mesas.lineas_con_subtotal(nombre_mesa):
            self.mesas.liberar_mesa(nombre_mesa)

        return {
            "total": total,
            "recibido": recibido,
            "cambio": cambio,
            "metodoPago": metodo_pago,
        }

    # ================= Cierre =================

    def resumen_cierre(self):
        return self.cierre.resumen_agrupado()

    def totales_cierre(self):
        return self.cierre.totales()

    def generar_reporte_cierre(self, ruta_salida=None, formato="txt"):
        if formato.lower() == "pdf":
            texto = self.cierre.generar_reporte_pdf(ruta_salida)
            return texto

        texto = self.cierre.generar_reporte_texto()
        if ruta_salida:
            with open(ruta_salida, "w", encoding="utf-8") as f:
                f.write(texto)
        return texto

    def reiniciar_cierre(self):
        """Botón 'Reiniciar cierre': borra ventas y totales de cierre,
        libera las 5 mesas, y NO toca el inventario."""
        self.cierre.reiniciar()
        self.mesas.liberar_todas()
