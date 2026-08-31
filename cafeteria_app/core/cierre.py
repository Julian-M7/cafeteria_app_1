"""
cierre.py
==========
Acumula el historial de ventas de las mesas ya COBRADAS y calcula los
totales de caja por método de pago.

Se persiste en data/json/cierre.json como:
    {
        "ventas": [
            {
                "nombreProducto": str,
                "cantidad": int,
                "precioUnitario": Decimal,
                "subtotal": Decimal,
                "mesa": str,
                "metodoPago": "efectivo" | "transferencia",
                "fecha": str (ISO 8601)
            },
            ...
        ],
        "totalEfectivo": Decimal,
        "totalTransferencia": Decimal,
        "totalGeneral": Decimal,
        "fechaCierre": str | None
    }

`ventas` guarda el DESGLOSE histórico completo (una entrada por cada
línea cobrada, con su precio unitario y subtotal reales), no sólo los
totales acumulados. Esto corrige la falencia del Cierre.java original
descrita en el enunciado (no guardaba precios unitarios ni subtotales).
"""

from datetime import datetime
from decimal import Decimal

from . import money
from . import persistence as p

DOS_DECIMALES = Decimal("0.01")


def _cierre_vacio():
    return {
        "ventas": [],
        "totalEfectivo": Decimal("0.00"),
        "totalTransferencia": Decimal("0.00"),
        "totalGeneral": Decimal("0.00"),
        "fechaCierre": None,
    }


class Cierre:
    def __init__(self, ruta=None):
        self.ruta = ruta or p.CIERRE_PATH
        self._datos = _cierre_vacio()
        self.cargar()

    # ---------- Persistencia ----------

    def cargar(self):
        datos = p.leer_json(self.ruta, self._serializar(_cierre_vacio()))

        ventas = []
        for v in datos.get("ventas", []):
            ventas.append({
                "nombreProducto": v["nombreProducto"],
                "cantidad": int(v["cantidad"]),
                "precioUnitario": Decimal(str(v["precioUnitario"])),
                "subtotal": Decimal(str(v["subtotal"])),
                "mesa": v.get("mesa"),
                "metodoPago": v.get("metodoPago"),
                "fecha": v.get("fecha"),
            })

        self._datos = {
            "ventas": ventas,
            "totalEfectivo": Decimal(str(datos.get("totalEfectivo", "0.00"))),
            "totalTransferencia": Decimal(str(datos.get("totalTransferencia", "0.00"))),
            "totalGeneral": Decimal(str(datos.get("totalGeneral", "0.00"))),
            "fechaCierre": datos.get("fechaCierre"),
        }

    def guardar(self):
        p.escribir_json(self.ruta, self._serializar(self._datos))

    @staticmethod
    def _serializar(datos):
        return {
            "ventas": [
                {
                    "nombreProducto": v["nombreProducto"],
                    "cantidad": v["cantidad"],
                    "precioUnitario": str(v["precioUnitario"]),
                    "subtotal": str(v["subtotal"]),
                    "mesa": v.get("mesa"),
                    "metodoPago": v.get("metodoPago"),
                    "fecha": v.get("fecha"),
                }
                for v in datos["ventas"]
            ],
            "totalEfectivo": str(datos["totalEfectivo"]),
            "totalTransferencia": str(datos["totalTransferencia"]),
            "totalGeneral": str(datos["totalGeneral"]),
            "fechaCierre": datos["fechaCierre"],
        }

    # ---------- Mutaciones ----------

    def registrar_venta(self, lineas, metodo_pago, nombre_mesa):
        """
        Registra en el historial de cierre las líneas de una mesa recién
        cobrada. `lineas` son las líneas de la mesa YA calculadas (con
        precioUnitario congelado y subtotal), tal como las produce
        Mesas.lineas_con_subtotal(). Sólo se llama para mesas
        efectivamente cobradas (el cierre nunca incluye mesas sin pagar).
        """
        ahora = datetime.now().isoformat(timespec="seconds")
        total_venta = Decimal("0.00")

        for linea in lineas:
            self._datos["ventas"].append({
                "nombreProducto": linea["nombre"],
                "cantidad": linea["cantidad"],
                "precioUnitario": linea["precioUnitario"],
                "subtotal": linea["subtotal"],
                "mesa": nombre_mesa,
                "metodoPago": metodo_pago,
                "fecha": ahora,
            })
            total_venta += linea["subtotal"]

        if metodo_pago == "efectivo":
            self._datos["totalEfectivo"] += total_venta
        elif metodo_pago == "transferencia":
            self._datos["totalTransferencia"] += total_venta
        self._datos["totalGeneral"] += total_venta

        self.guardar()

    def reiniciar(self):
        """Elimina todo el historial de cierre y reinicia los totales a
        cero. NO afecta el inventario (eso lo maneja otro módulo)."""
        self._datos = _cierre_vacio()
        self.guardar()

    # ---------- Consultas ----------

    def resumen_agrupado(self):
        """
        Agrupa las ventas por (producto, precio unitario). Si un mismo
        producto se vendió a precios distintos (porque el precio del
        inventario cambió entre una venta y otra), aparece como líneas
        separadas -una por cada precio-, tal como permite el enunciado.
        """
        agrupado = {}
        for v in self._datos["ventas"]:
            clave = (v["nombreProducto"], v["precioUnitario"])
            if clave not in agrupado:
                agrupado[clave] = {
                    "nombreProducto": v["nombreProducto"],
                    "precioUnitario": v["precioUnitario"],
                    "cantidadTotal": 0,
                    "subtotalTotal": Decimal("0.00"),
                }
            agrupado[clave]["cantidadTotal"] += v["cantidad"]
            agrupado[clave]["subtotalTotal"] += v["subtotal"]

        return sorted(agrupado.values(), key=lambda x: (x["nombreProducto"], x["precioUnitario"]))

    def totales(self):
        return {
            "totalEfectivo": self._datos["totalEfectivo"],
            "totalTransferencia": self._datos["totalTransferencia"],
            "totalGeneral": self._datos["totalGeneral"],
        }

    def ventas(self):
        return list(self._datos["ventas"])

    def generar_reporte_texto(self):
        lineas_reporte = []
        lineas_reporte.append("=" * 72)
        lineas_reporte.append("Cierre de caja")
        lineas_reporte.append("REPORTE DE CIERRE DE CAJA - CAFETERÍA")
        lineas_reporte.append(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lineas_reporte.append("=" * 72)
        lineas_reporte.append("")

        resumen = self.resumen_agrupado()
        if not resumen:
            lineas_reporte.append("No hay ventas registradas en este cierre.")
        else:
            encabezado = f"{'Producto':<28}{'Cant.':>6}{'P. Unitario':>14}{'Subtotal':>14}"
            lineas_reporte.append(encabezado)
            lineas_reporte.append("-" * len(encabezado))
            for item in resumen:
                lineas_reporte.append(
                    f"{item['nombreProducto']:<28}"
                    f"{item['cantidadTotal']:>6}"
                    f"{money.formatear_monto(item['precioUnitario']):>14}"
                    f"{money.formatear_monto(item['subtotalTotal']):>14}"
                )

        lineas_reporte.append("")
        totales = self.totales()
        lineas_reporte.append(f"Total en efectivo:      {money.formatear_monto(totales['totalEfectivo'])}")
        lineas_reporte.append(f"Total en transferencia: {money.formatear_monto(totales['totalTransferencia'])}")
        lineas_reporte.append(f"TOTAL GENERAL:          {money.formatear_monto(totales['totalGeneral'])}")
        lineas_reporte.append("")
        lineas_reporte.append(f"Número de líneas vendidas: {len(self._datos['ventas'])}")
        lineas_reporte.append("=" * 72)

        return "\n".join(lineas_reporte)

    def generar_reporte_pdf(self, ruta_salida=None):
        texto = self.generar_reporte_texto()
        ruta_final = ruta_salida or "reporte_cierre.pdf"
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
            from reportlab.lib import colors
        except ImportError:
            if ruta_salida:
                with open(ruta_final, "w", encoding="utf-8") as f:
                    f.write(texto)
                return texto
            raise RuntimeError("Para exportar PDF necesitas instalar reportlab: pip install reportlab")

        doc = SimpleDocTemplate(ruta_final, pagesize=letter, rightMargin=20 * mm, leftMargin=20 * mm,
                                topMargin=18 * mm, bottomMargin=18 * mm)
        estilo = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Cierre de caja", estilo['Title']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", estilo['BodyText']))
        story.append(Spacer(1, 10))

        resumen = self.resumen_agrupado()
        filas = [["Producto", "Cant.", "P. Unitario", "Subtotal"]]
        for item in resumen:
            filas.append([
                item["nombreProducto"],
                str(item["cantidadTotal"]),
                money.formatear_monto(item["precioUnitario"]),
                money.formatear_monto(item["subtotalTotal"]),
            ])

        if len(filas) == 1:
            story.append(Paragraph("No hay ventas registradas en este cierre.", estilo['BodyText']))
        else:
            tabla = Table(filas)
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a2c1f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(tabla)

        story.append(Spacer(1, 14))
        totales = self.totales()
        story.append(Paragraph(f"Total en efectivo: {money.formatear_monto(totales['totalEfectivo'])}", estilo['BodyText']))
        story.append(Paragraph(f"Total en transferencia: {money.formatear_monto(totales['totalTransferencia'])}", estilo['BodyText']))
        story.append(Paragraph(f"TOTAL GENERAL: {money.formatear_monto(totales['totalGeneral'])}", estilo['BodyText']))
        doc.build(story)
        return texto
