"""
test_core.py
=============
Pruebas automatizadas de toda la lógica de negocio (paquete core/),
completamente desacopladas de la interfaz gráfica.

Cubre:
    A) Parseo y formateo de montos (core/money.py) - sección 5 del
       enunciado ("Validaciones detalladas para cobro").
    B) Los 8 "casos de prueba clave" listados en la sección 8 del
       enunciado, de principio a fin (login -> inventario -> mesa ->
       cobro -> cierre -> reinicio -> persistencia).
    C) Reglas de negocio críticas de la sección 4 (precio congelado,
       cierre sólo con mesas pagadas, reinicio no toca inventario,
       etc.)

Ejecutar desde la raíz del proyecto con:
    python3 -m unittest tests.test_core -v
"""

import shutil
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from core import money
from core.controller import AppController, CobroError


class PruebasParseoDeMontos(unittest.TestCase):
    """Sección 5 del enunciado: validaciones detalladas para cobro."""

    def test_entero_simple(self):
        """'10000' -> válido, debe aceptarse."""
        valor, error = money.parse_monto("10000")
        self.assertIsNone(error)
        self.assertEqual(valor, Decimal("10000.00"))

    def test_punto_como_miles(self):
        """'10.000' -> válido como miles."""
        valor, error = money.parse_monto("10.000")
        self.assertIsNone(error)
        self.assertEqual(valor, Decimal("10000.00"))

    def test_punto_miles_coma_decimales(self):
        """'10.000,50' -> válido con decimales."""
        valor, error = money.parse_monto("10.000,50")
        self.assertIsNone(error)
        self.assertEqual(valor, Decimal("10000.50"))

    def test_coma_como_alternativa_de_miles(self):
        """'10,000' -> válido como alternativa (separador de miles)."""
        valor, error = money.parse_monto("10,000")
        self.assertIsNone(error)
        self.assertEqual(valor, Decimal("10000.00"))

    def test_simbolo_de_moneda(self):
        """'$10.000,50' -> válido con símbolo."""
        valor, error = money.parse_monto("$10.000,50")
        self.assertIsNone(error)
        self.assertEqual(valor, Decimal("10000.50"))

    def test_letras_invalido(self):
        """'abc123' -> inválido."""
        valor, error = money.parse_monto("abc123")
        self.assertIsNone(valor)
        self.assertIsNotNone(error)

    def test_campo_vacio_invalido(self):
        """campo vacío -> inválido."""
        valor, error = money.parse_monto("")
        self.assertIsNone(valor)
        self.assertEqual(error, "Campo vacío.")

        valor, error = money.parse_monto("   ")
        self.assertIsNone(valor)
        self.assertEqual(error, "Campo vacío.")

        valor, error = money.parse_monto(None)
        self.assertIsNone(valor)
        self.assertEqual(error, "Campo vacío.")

    def test_formato_us_miles_y_decimales(self):
        """'10,000.50' (coma miles + punto decimal, estilo US) -> válido."""
        valor, error = money.parse_monto("10,000.50")
        self.assertIsNone(error)
        self.assertEqual(valor, Decimal("10000.50"))

    def test_multiples_grupos_de_miles(self):
        """'1.234.567,89' -> agrupación de miles repetida + decimales."""
        valor, error = money.parse_monto("1.234.567,89")
        self.assertIsNone(error)
        self.assertEqual(valor, Decimal("1234567.89"))

    def test_decimal_simple_con_coma(self):
        """'10,50' (un solo decimal con coma) -> 10.50."""
        valor, error = money.parse_monto("10,50")
        self.assertIsNone(error)
        self.assertEqual(valor, Decimal("10.50"))

    def test_decimal_simple_con_punto(self):
        """'10.5' (un solo decimal con punto) -> 10.50."""
        valor, error = money.parse_monto("10.5")
        self.assertIsNone(error)
        self.assertEqual(valor, Decimal("10.50"))

    def test_mas_de_dos_decimales_invalido(self):
        """Más de 2 decimales reales (no agrupación de miles) -> inválido."""
        valor, error = money.parse_monto("10.1234")
        self.assertIsNone(valor)
        self.assertIn("2 decimales", error)

    def test_monto_negativo_invalido(self):
        valor, error = money.parse_monto("-10000")
        self.assertIsNone(valor)
        self.assertIn("positivo", error)

    def test_monto_cero_invalido(self):
        valor, error = money.parse_monto("0")
        self.assertIsNone(valor)
        self.assertIn("mayor que cero", error)

    def test_formato_no_aceptado_caracteres_mixtos(self):
        valor, error = money.parse_monto("10.00.00,,50")
        self.assertIsNone(valor)
        self.assertIsNotNone(error)

    def test_formatear_monto_local(self):
        self.assertEqual(money.formatear_monto(Decimal("10000.5")), "$10.000,50")
        self.assertEqual(money.formatear_monto(Decimal("1234567")), "$1.234.567,00")
        self.assertEqual(money.formatear_monto(Decimal("900")), "$900,00")


class BaseControladorAislado(unittest.TestCase):
    """Clase base que crea un AppController apuntando a archivos JSON
    temporales, para que las pruebas nunca toquen datos reales."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="cafeteria_test_"))
        self.controller = AppController(
            ruta_inventario=str(self.tmp_dir / "inventario.json"),
            ruta_mesas=str(self.tmp_dir / "mesas.json"),
            ruta_cierre=str(self.tmp_dir / "cierre.json"),
        )
        # Producto de prueba estándar para varios tests
        self.cafe = self.controller.agregar_producto("Café", "Bebida", "2900")
        self.empanada = self.controller.agregar_producto("Empanada", "Comida", "3000")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def nueva_instancia_controller(self):
        """Crea una SEGUNDA instancia de AppController apuntando a los
        MISMOS archivos, simulando reabrir la aplicación, para
        verificar que todo quedó realmente persistido en disco."""
        return AppController(
            ruta_inventario=str(self.tmp_dir / "inventario.json"),
            ruta_mesas=str(self.tmp_dir / "mesas.json"),
            ruta_cierre=str(self.tmp_dir / "cierre.json"),
        )


class PruebasLogin(BaseControladorAislado):
    def test_login_correcto(self):
        """Login con hattu / 12345."""
        self.assertTrue(self.controller.iniciar_sesion("hattu", "12345"))
        self.assertTrue(self.controller.autenticado)

    def test_login_incorrecto(self):
        self.assertFalse(self.controller.iniciar_sesion("hattu", "clave_mala"))
        self.assertFalse(self.controller.autenticado)
        self.assertFalse(self.controller.iniciar_sesion("otro_usuario", "12345"))

    def test_10_mesas_y_categoria_restaurante(self):
        """Debe existir 10 mesas y la categoría restaurante en el inventario."""
        self.assertEqual(len(self.controller.nombres_mesas()), 16)
        self.assertIn("mesa10", self.controller.nombres_mesas())

        producto = self.controller.agregar_producto("Menú del día", "Restaurante", "16000")
        self.assertEqual(producto["categoria"], "Restaurante")
        self.assertEqual(producto["precio"], Decimal("16000.00"))
        otra = self.nueva_instancia_controller()
        self.assertEqual(otra.inventario.obtener(producto["id"])["nombre"], "Menú del día")

    def test_buscar_producto_por_nombre(self):
        """La búsqueda debe localizar productos por coincidencia parcial."""
        self.controller.agregar_producto("Menú ejecutivo", "Restaurante", "18000")
        resultados = self.controller.buscar_productos("ejecutivo")
        self.assertTrue(any(item["nombre"].lower() == "menú ejecutivo" for item in resultados))

    def test_generar_reporte_pdf(self):
        """Debe poder generar un PDF del cierre con contenido útil."""
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)
        self.controller.cobrar_mesa("mesa1", "efectivo", "5000")

        ruta_pdf = str(self.tmp_dir / "reporte.pdf")
        texto = self.controller.generar_reporte_cierre(ruta_pdf, formato="pdf")
        self.assertTrue(Path(ruta_pdf).exists())
        self.assertIn("Cierre de caja", texto)

    def test_productos_restaurante_nuevos_y_pago_parcial(self):
        productos = [
            ("Tinto Golden", "1500"),
            ("Desechables", "1000"),
            ("Medio runtazo", "16000"),
            ("Bandeja junior ejecutivo", "16000"),
            ("Bandeja junior casa", "14000"),
            ("Jarra de chicha", "3500"),
            ("Vaso de chicha", "2500"),
            ("Botella de chicha 1,5 L", "10000"),
        ]
        for nombre, precio in productos:
            self.controller.agregar_producto(nombre, "Restaurante", precio)

        tinto = self.controller.buscar_productos("tinto golden")[0]
        desechables = self.controller.buscar_productos("desechables")[0]
        self.controller.agregar_a_mesa("mesa16", tinto["id"], 2)
        self.controller.agregar_a_mesa("mesa16", desechables["id"], 1)

        resultado = self.controller.cobrar_seleccion_mesa(
            "mesa16", [(0, 1)], "transferencia"
        )
        self.assertEqual(resultado["total"], Decimal("1500.00"))
        self.assertEqual(len(self.controller.lineas_mesa("mesa16")), 2)
        self.assertEqual(self.controller.lineas_mesa("mesa16")[0]["cantidad"], 1)
        self.assertEqual(self.controller.totales_cierre()["totalGeneral"], Decimal("1500.00"))

    def test_mesa_nueva_se_persiste(self):
        self.assertEqual(len(self.controller.nombres_mesas()), 16)
        nombre = self.controller.agregar_mesa()
        self.assertEqual(nombre, "mesa17")
        otra = self.nueva_instancia_controller()
        self.assertIn("mesa17", otra.nombres_mesas())


class CasosDePruebaClaveDelEnunciado(BaseControladorAislado):
    """Los 8 casos de prueba clave listados explícitamente en la
    sección 8 del enunciado, verificados de punta a punta."""

    def test_1_pago_valido_efectivo_10000(self):
        """Pago válido en efectivo con 10000."""
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)  # total = 2900
        resultado = self.controller.cobrar_mesa("mesa1", "efectivo", "10000")
        self.assertEqual(resultado["total"], Decimal("2900.00"))
        self.assertEqual(resultado["recibido"], Decimal("10000.00"))
        self.assertEqual(resultado["cambio"], Decimal("7100.00"))

    def test_2_pago_valido_efectivo_10_punto_000(self):
        """Pago válido en efectivo con 10.000."""
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)  # total = 2900
        resultado = self.controller.cobrar_mesa("mesa1", "efectivo", "10.000")
        self.assertEqual(resultado["recibido"], Decimal("10000.00"))
        self.assertEqual(resultado["cambio"], Decimal("7100.00"))

    def test_3_pago_valido_con_decimales(self):
        """Pago válido con decimales 10.000,50."""
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)  # total = 2900
        resultado = self.controller.cobrar_mesa("mesa1", "efectivo", "10.000,50")
        self.assertEqual(resultado["recibido"], Decimal("10000.50"))
        self.assertEqual(resultado["cambio"], Decimal("7100.50"))

    def test_4_pago_insuficiente_en_efectivo(self):
        """Pago insuficiente en efectivo."""
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 2)  # total = 5800
        with self.assertRaises(CobroError) as ctx:
            self.controller.cobrar_mesa("mesa1", "efectivo", "5000")
        self.assertIn("Monto insuficiente", str(ctx.exception))
        self.assertIn("Falta", str(ctx.exception))
        # La mesa NO debió quedar cobrada ni liberada tras el error
        lineas = self.controller.lineas_mesa("mesa1")
        self.assertEqual(len(lineas), 1)

    def test_5_transferencia_monto_autocompletado(self):
        """Pago por transferencia con monto autocompletado."""
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 3)  # total = 8700
        resultado = self.controller.cobrar_mesa("mesa1", "transferencia")
        self.assertEqual(resultado["total"], Decimal("8700.00"))
        self.assertEqual(resultado["recibido"], Decimal("8700.00"))
        self.assertEqual(resultado["cambio"], Decimal("0.00"))

    def test_6_reiniciar_cierre_libera_mesas_no_toca_inventario(self):
        """Reiniciar cierre deja mesas libres y no cambia inventario."""
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)
        self.controller.cobrar_mesa("mesa1", "efectivo", "5000")
        self.controller.agregar_a_mesa("mesa2", self.empanada["id"], 2)

        productos_antes = self.controller.listar_productos()

        self.controller.reiniciar_cierre()

        # Todas las mesas quedan libres (sin productos)
        for nombre_mesa in self.controller.nombres_mesas():
            self.assertEqual(self.controller.lineas_mesa(nombre_mesa), [])

        # El cierre queda en cero
        totales = self.controller.totales_cierre()
        self.assertEqual(totales["totalGeneral"], Decimal("0.00"))

        # El inventario NO cambió
        productos_despues = self.controller.listar_productos()
        self.assertEqual(productos_antes, productos_despues)

    def test_7_cierre_totales_exactos(self):
        """Cierre muestra totales exactos en efectivo, transferencia y general."""
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 2)       # 5800 efectivo
        self.controller.cobrar_mesa("mesa1", "efectivo", "6000")

        self.controller.agregar_a_mesa("mesa2", self.empanada["id"], 3)  # 9000 transferencia
        self.controller.cobrar_mesa("mesa2", "transferencia")

        self.controller.agregar_a_mesa("mesa3", self.cafe["id"], 1)      # 2900 efectivo
        self.controller.cobrar_mesa("mesa3", "efectivo", "3000")

        totales = self.controller.totales_cierre()
        self.assertEqual(totales["totalEfectivo"], Decimal("8700.00"))       # 5800 + 2900
        self.assertEqual(totales["totalTransferencia"], Decimal("9000.00"))
        self.assertEqual(totales["totalGeneral"], Decimal("17700.00"))

    def test_8_json_guarda_historial_completo(self):
        """JSON guarda el historial completo de ventas."""
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 2)
        self.controller.cobrar_mesa("mesa1", "efectivo", "10000")

        # Se simula "reabrir la aplicación" con una instancia nueva que
        # lee los mismos archivos JSON desde cero.
        otra = self.nueva_instancia_controller()
        ventas = otra.cierre.ventas()

        self.assertEqual(len(ventas), 1)
        venta = ventas[0]
        self.assertEqual(venta["nombreProducto"], "Café")
        self.assertEqual(venta["cantidad"], 2)
        self.assertEqual(venta["precioUnitario"], Decimal("2900.00"))
        self.assertEqual(venta["subtotal"], Decimal("5800.00"))
        self.assertEqual(venta["metodoPago"], "efectivo")
        self.assertEqual(venta["mesa"], "mesa1")


class PruebasReglasDeNegocio(BaseControladorAislado):
    """Sección 4 del enunciado: reglas de negocio críticas."""

    def test_precio_congelado_no_afectado_por_cambio_de_inventario(self):
        """Un producto modificado en inventario después no afecta
        órdenes activas o cerradas."""
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)  # precio congelado: 2900

        # Sube el precio del café en el inventario
        self.controller.modificar_producto(self.cafe["id"], precio_texto="5000")

        lineas = self.controller.lineas_mesa("mesa1")
        self.assertEqual(lineas[0]["precioUnitario"], Decimal("2900.00"))
        self.assertEqual(self.controller.total_mesa("mesa1"), Decimal("2900.00"))

        # El inventario sí refleja el nuevo precio para ventas futuras
        producto_actualizado = self.controller.inventario.obtener(self.cafe["id"])
        self.assertEqual(producto_actualizado["precio"], Decimal("5000.00"))

    def test_producto_eliminado_de_inventario_no_afecta_pedido_existente(self):
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)
        self.controller.eliminar_producto(self.cafe["id"])

        lineas = self.controller.lineas_mesa("mesa1")
        self.assertEqual(len(lineas), 1)
        self.assertEqual(lineas[0]["nombre"], "Café")
        self.assertEqual(lineas[0]["precioUnitario"], Decimal("2900.00"))

    def test_cierre_solo_incluye_mesas_pagadas(self):
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)
        self.controller.cobrar_mesa("mesa1", "efectivo", "5000")

        self.controller.agregar_a_mesa("mesa2", self.empanada["id"], 5)  # NO se cobra

        resumen = self.controller.resumen_cierre()
        nombres_en_cierre = {item["nombreProducto"] for item in resumen}
        self.assertIn("Café", nombres_en_cierre)
        self.assertNotIn("Empanada", nombres_en_cierre)

        # La mesa2 sigue teniendo su pedido intacto (no se tocó)
        self.assertEqual(len(self.controller.lineas_mesa("mesa2")), 1)

    def test_mesa_queda_libre_inmediatamente_tras_cobro(self):
        self.controller.agregar_a_mesa("mesa4", self.cafe["id"], 1)
        self.controller.cobrar_mesa("mesa4", "transferencia")
        self.assertEqual(self.controller.lineas_mesa("mesa4"), [])
        self.assertEqual(self.controller.total_mesa("mesa4"), Decimal("0.00"))

    def test_no_se_puede_cobrar_mesa_vacia(self):
        with self.assertRaises(CobroError):
            self.controller.cobrar_mesa("mesa5", "efectivo", "10000")

    def test_resumen_agrupa_por_producto_y_precio(self):
        """Si hay variaciones de precio por el mismo producto, se
        desglosa por precio en el cierre."""
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)  # 2900
        self.controller.cobrar_mesa("mesa1", "efectivo", "5000")

        self.controller.modificar_producto(self.cafe["id"], precio_texto="3200")
        self.controller.agregar_a_mesa("mesa2", self.cafe["id"], 1)  # 3200 (precio nuevo)
        self.controller.cobrar_mesa("mesa2", "efectivo", "5000")

        resumen = self.controller.resumen_cierre()
        lineas_cafe = [item for item in resumen if item["nombreProducto"] == "Café"]
        self.assertEqual(len(lineas_cafe), 2)
        precios = {item["precioUnitario"] for item in lineas_cafe}
        self.assertEqual(precios, {Decimal("2900.00"), Decimal("3200.00")})


class PruebasInventario(BaseControladorAislado):
    def test_filtro_por_categoria(self):
        """Filtrar por categoría: todas, solo bebidas, solo comidas."""
        bebidas = self.controller.listar_productos("Bebida")
        comidas = self.controller.listar_productos("Comida")
        todas = self.controller.listar_productos("Todas")

        self.assertTrue(all(p["categoria"] == "Bebida" for p in bebidas))
        self.assertTrue(all(p["categoria"] == "Comida" for p in comidas))
        self.assertEqual(len(todas), len(bebidas) + len(comidas))

    def test_categoria_invalida_rechazada(self):
        with self.assertRaises(ValueError):
            self.controller.agregar_producto("Postre", "Postre", "5000")

    def test_precio_invalido_rechazado_al_agregar(self):
        with self.assertRaises(ValueError):
            self.controller.agregar_producto("Té", "Bebida", "abc")

    def test_eliminar_producto_inexistente(self):
        with self.assertRaises(ValueError):
            self.controller.eliminar_producto(9999)

    def test_ids_unicos_entre_productos_existentes(self):
        """El id de cada producto es único entre TODOS los productos que
        existen actualmente en el inventario (requisito explícito del
        enunciado: 'id (único)'). Nota de diseño: como inventario.json
        debe guardarse como un simple arreglo -sin contador aparte-, el
        siguiente id se calcula como max(ids existentes) + 1; esto es
        válido y no rompe la unicidad, aunque significa que si se
        elimina el producto con el id más alto, ese id podría
        reutilizarse en el futuro. Esto no afecta pedidos ni el cierre
        porque ambos guardan nombre y precio congelados, no dependen de
        volver a resolver el id contra el inventario."""
        nuevo1 = self.controller.agregar_producto("Jugo", "Bebida", "3000")
        nuevo2 = self.controller.agregar_producto("Soda", "Bebida", "2500")
        self.assertNotEqual(nuevo1["id"], nuevo2["id"])

        self.controller.eliminar_producto(nuevo1["id"])
        nuevo3 = self.controller.agregar_producto("Té", "Bebida", "2000")

        ids_existentes = [p["id"] for p in self.controller.listar_productos()]
        self.assertEqual(len(ids_existentes), len(set(ids_existentes)))
        self.assertIn(nuevo3["id"], ids_existentes)


class PruebasMesas(BaseControladorAislado):
    def test_agregar_mismo_producto_mismo_precio_suma_cantidad(self):
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 2)
        lineas = self.controller.lineas_mesa("mesa1")
        self.assertEqual(len(lineas), 1)
        self.assertEqual(lineas[0]["cantidad"], 3)

    def test_modificar_cantidad_de_producto_en_mesa(self):
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)
        self.controller.modificar_cantidad_mesa("mesa1", 0, 5)
        lineas = self.controller.lineas_mesa("mesa1")
        self.assertEqual(lineas[0]["cantidad"], 5)
        self.assertEqual(lineas[0]["subtotal"], Decimal("14500.00"))

    def test_eliminar_producto_de_mesa(self):
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)
        self.controller.agregar_a_mesa("mesa1", self.empanada["id"], 1)
        self.controller.eliminar_de_mesa("mesa1", 0)
        lineas = self.controller.lineas_mesa("mesa1")
        self.assertEqual(len(lineas), 1)
        self.assertEqual(lineas[0]["nombre"], "Empanada")

    def test_mesas_independientes_entre_si(self):
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)
        self.controller.agregar_a_mesa("mesa2", self.empanada["id"], 4)
        self.assertEqual(self.controller.total_mesa("mesa1"), Decimal("2900.00"))
        self.assertEqual(self.controller.total_mesa("mesa2"), Decimal("12000.00"))

    def test_cantidad_cero_o_negativa_rechazada(self):
        self.controller.agregar_a_mesa("mesa1", self.cafe["id"], 1)
        with self.assertRaises(ValueError):
            self.controller.modificar_cantidad_mesa("mesa1", 0, 0)
        with self.assertRaises(ValueError):
            self.controller.modificar_cantidad_mesa("mesa1", 0, -3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
