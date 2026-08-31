"""
cierre_view.py
================
Pantalla de cierre de caja (módulo 2.5): resumen de ventas agrupadas,
totales por método de pago, generación de reporte y reinicio de cierre.
"""

import datetime
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.money import formatear_monto

from .estilos import (COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_BORDE, COLOR_ERROR, COLOR_FONDO,
                       COLOR_TEXTO, crear_barra_superior)


class CierreView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_FONDO)
        self.app = app

        crear_barra_superior(self, app, "📊  Cierre de caja")

        contenido = tk.Frame(self, bg=COLOR_FONDO)
        contenido.pack(fill="both", expand=True, padx=24, pady=16)

        tk.Label(contenido, text="Ventas de mesas cobradas (agrupadas por producto y precio)",
                 font=("Segoe UI", 9), bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(anchor="w",
                                                                             pady=(0, 6))

        columnas = ("nombre", "cantidad", "precio", "subtotal")
        self.tabla = ttk.Treeview(contenido, columns=columnas, show="headings", height=13)
        for col, texto, ancho in (("nombre", "Producto", 220), ("cantidad", "Cant. vendida", 120),
                                   ("precio", "P. Unitario", 130), ("subtotal", "Subtotal", 130)):
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="w" if col == "nombre" else "center")
        self.tabla.pack(fill="both", expand=True)

        panel_totales = tk.Frame(contenido, bg="white", highlightbackground=COLOR_BORDE,
                                  highlightthickness=1)
        panel_totales.pack(fill="x", pady=(14, 14))

        self.label_efectivo = self._fila_total(panel_totales, "Total en efectivo")
        self.label_transferencia = self._fila_total(panel_totales, "Total en transferencia")
        self.label_general = self._fila_total(panel_totales, "TOTAL GENERAL", grande=True)

        botones = tk.Frame(contenido, bg=COLOR_FONDO)
        botones.pack(fill="x")
        tk.Button(
            botones, text="Generar reporte", font=("Segoe UI", 9, "bold"), bg=COLOR_ACENTO,
            fg="white", bd=0, cursor="hand2", padx=14, pady=7,
            activebackground=COLOR_ACENTO_HOVER, activeforeground="white",
            command=self._generar_reporte,
        ).pack(side="left")
        tk.Button(
            botones, text="Reiniciar cierre", font=("Segoe UI", 9, "bold"), bg="white",
            fg=COLOR_ERROR, bd=1, relief="solid", cursor="hand2", padx=14, pady=7,
            command=self._reiniciar,
        ).pack(side="left", padx=10)

    def _fila_total(self, parent, texto, grande=False):
        fila = tk.Frame(parent, bg="white")
        fila.pack(fill="x", padx=16, pady=6)
        fuente = ("Segoe UI", 13, "bold") if grande else ("Segoe UI", 10)
        tk.Label(fila, text=texto, font=fuente, bg="white",
                 fg=COLOR_TEXTO if grande else COLOR_ACENTO).pack(side="left")
        valor = tk.Label(fila, text="$0,00", font=fuente, bg="white", fg=COLOR_TEXTO)
        valor.pack(side="right")
        return valor

    def al_mostrar(self):
        self._refrescar()

    def _refrescar(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        resumen = self.app.controller.resumen_cierre()
        for item in resumen:
            self.tabla.insert("", "end", values=(
                item["nombreProducto"], item["cantidadTotal"],
                formatear_monto(item["precioUnitario"]), formatear_monto(item["subtotalTotal"])))

        totales = self.app.controller.totales_cierre()
        self.label_efectivo.config(text=formatear_monto(totales["totalEfectivo"]))
        self.label_transferencia.config(text=formatear_monto(totales["totalTransferencia"]))
        self.label_general.config(text=formatear_monto(totales["totalGeneral"]))

    def _generar_reporte(self):
        resumen = self.app.controller.resumen_cierre()
        if not resumen:
            messagebox.showinfo("Sin ventas", "No hay ventas registradas para generar un reporte.")
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        carpeta_reportes = os.path.join(base_dir, "data", "reportes")
        os.makedirs(carpeta_reportes, exist_ok=True)

        marca_tiempo = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_sugerido = f"reporte_cierre_{marca_tiempo}.pdf"

        ruta = filedialog.asksaveasfilename(
            title="Guardar reporte de cierre",
            initialdir=carpeta_reportes,
            initialfile=nombre_sugerido,
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf"), ("Archivo de texto", "*.txt")],
        )
        if not ruta:
            return

        formato = "pdf" if ruta.lower().endswith(".pdf") else "txt"
        self.app.controller.generar_reporte_cierre(ruta, formato=formato)
        messagebox.showinfo("Reporte generado", f"El reporte se guardó en:\n{ruta}")

    def _reiniciar(self):
        if not messagebox.askyesno(
                "Reiniciar cierre",
                "Esto eliminará todas las ventas cobradas y dejará las 5 mesas libres.\n"
                "El inventario NO se modificará.\n\n¿Deseas continuar?"):
            return
        self.app.controller.reiniciar_cierre()
        self._refrescar()
        messagebox.showinfo("Cierre reiniciado", "El cierre se reinició correctamente.")
