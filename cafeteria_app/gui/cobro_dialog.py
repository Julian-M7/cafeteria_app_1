"""
cobro_dialog.py
==================
Ventana modal de cobro (módulo 2.4): selección de método de pago
(efectivo o transferencia), validación del monto recibido y cálculo
del cambio.
"""

import tkinter as tk
from tkinter import ttk

from core.money import formatear_monto

from .estilos import COLOR_ACENTO, COLOR_ERROR, COLOR_EXITO, COLOR_EXITO_HOVER, COLOR_TEXTO_SUAVE


class DialogoCobro(tk.Toplevel):
    def __init__(self, panel_mesa, app, nombre_mesa, total, lineas=None, al_confirmar=None):
        super().__init__(panel_mesa)
        self.panel_mesa = panel_mesa
        self.app = app
        self.nombre_mesa = nombre_mesa
        self.total = total
        self.lineas = lineas or []
        self.al_confirmar = al_confirmar
        self._cobrado = False

        titulo = f"Cobrar {nombre_mesa.replace('mesa', 'Mesa ')}"
        self.title(titulo)
        self.configure(bg="white")
        self.geometry("560x620")
        self.resizable(False, False)
        self.transient(panel_mesa.winfo_toplevel())
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

        tk.Label(self, text=titulo, font=("Segoe UI", 13, "bold"), bg="white",
                 fg=COLOR_ACENTO).pack(pady=(18, 4))
        tk.Label(self, text="Total a pagar", font=("Segoe UI", 9), bg="white",
                 fg=COLOR_TEXTO_SUAVE).pack()
        self.label_total = tk.Label(self, text=formatear_monto(total),
                        font=("Segoe UI", 24, "bold"), bg="white", fg="#2c2015")
        self.label_total.pack(pady=(0, 16))

        tk.Label(self, text="Selecciona los productos a pagar", font=("Segoe UI", 9, "bold"),
                 bg="white", fg=COLOR_ACENTO).pack(anchor="w", padx=30)
        self.tabla_productos = ttk.Treeview(
            self, columns=("producto", "cantidad", "subtotal"), show="headings",
            selectmode="extended", height=5,
        )
        for columna, titulo, ancho in (("producto", "Producto", 260), ("cantidad", "Cant.", 70),
                                        ("subtotal", "Subtotal", 110)):
            self.tabla_productos.heading(columna, text=titulo)
            self.tabla_productos.column(columna, width=ancho,
                                        anchor="w" if columna == "producto" else "center")
        self.tabla_productos.pack(fill="x", padx=30, pady=(4, 8))
        for indice, linea in enumerate(self.lineas):
            self.tabla_productos.insert("", "end", iid=str(indice), values=(
                linea["nombre"], linea["cantidad"], formatear_monto(linea["subtotal"])))
        if self.lineas:
            self.tabla_productos.selection_set("0")

        fila_cantidad = tk.Frame(self, bg="white")
        fila_cantidad.pack(fill="x", padx=30, pady=(0, 10))
        tk.Label(fila_cantidad, text="Unidades de la línea seleccionada:",
                 font=("Segoe UI", 9), bg="white").pack(side="left")
        self.spin_cantidad = tk.Spinbox(fila_cantidad, from_=1, to=99, width=5,
                                        font=("Segoe UI", 10))
        self.spin_cantidad.pack(side="left", padx=8)
        self.spin_cantidad.bind("<KeyRelease>", lambda _event: self._actualizar_total_seleccion())
        self.tabla_productos.bind("<<TreeviewSelect>>", self._actualizar_cantidad)
        if self.lineas:
            self.tabla_productos.selection_set(*[str(indice) for indice in range(len(self.lineas))])

        tk.Label(self, text="Método de pago", font=("Segoe UI", 9), bg="white").pack(anchor="w",
                                                                                       padx=30)
        self.metodo = tk.StringVar(value="efectivo")
        fila_metodo = tk.Frame(self, bg="white")
        fila_metodo.pack(fill="x", padx=30, pady=(2, 14))
        self.radio_efectivo = tk.Radiobutton(
            fila_metodo, text="Efectivo", variable=self.metodo, value="efectivo", bg="white",
            font=("Segoe UI", 10), command=self._actualizar_modo)
        self.radio_efectivo.pack(side="left", padx=(0, 20))
        self.radio_transferencia = tk.Radiobutton(
            fila_metodo, text="Transferencia", variable=self.metodo, value="transferencia",
            bg="white", font=("Segoe UI", 10), command=self._actualizar_modo)
        self.radio_transferencia.pack(side="left")

        tk.Label(self, text="Monto recibido", font=("Segoe UI", 9), bg="white").pack(anchor="w",
                                                                                       padx=30)
        self.entry_monto = ttk.Entry(self, font=("Segoe UI", 13))
        self.entry_monto.pack(fill="x", padx=30, pady=(2, 4))
        self.entry_monto.bind("<Return>", lambda e: self._confirmar())
        self.label_ayuda = tk.Label(self, text="Ej: 10000, 10.000 ó 10.000,50",
                                     font=("Segoe UI", 8), bg="white", fg=COLOR_TEXTO_SUAVE)
        self.label_ayuda.pack(anchor="w", padx=30)

        self.label_resultado = tk.Label(self, text="", font=("Segoe UI", 11, "bold"), bg="white",
                                         fg=COLOR_EXITO, wraplength=320, justify="left")
        self.label_resultado.pack(pady=(12, 0))
        self.label_error = tk.Label(self, text="", font=("Segoe UI", 9), bg="white",
                                     fg=COLOR_ERROR, wraplength=320, justify="left")
        self.label_error.pack(pady=(4, 0), padx=30)

        botones = tk.Frame(self, bg="white")
        botones.pack(fill="x", padx=30, pady=(16, 20), side="bottom")
        self.boton_cancelar = tk.Button(botones, text="Cancelar", font=("Segoe UI", 9),
                                         bg="white", bd=1, relief="solid", cursor="hand2",
                                         command=self._cerrar)
        self.boton_cancelar.pack(side="left", expand=True, fill="x", padx=(0, 6), ipady=6)
        self.boton_confirmar = tk.Button(
            botones, text="Confirmar pago", font=("Segoe UI", 9, "bold"), bg=COLOR_EXITO,
            fg="white", bd=0, cursor="hand2", activebackground=COLOR_EXITO_HOVER,
            activeforeground="white", command=self._confirmar)
        self.boton_confirmar.pack(side="left", expand=True, fill="x", padx=(6, 0), ipady=6)

        self._actualizar_modo()
        self.entry_monto.focus_set()

    def _actualizar_modo(self):
        self.label_error.config(text="")
        if self.metodo.get() == "transferencia":
            self.entry_monto.config(state="normal")
            self.entry_monto.delete(0, tk.END)
            self.entry_monto.insert(0, str(self.total))
            self.entry_monto.config(state="disabled")
            self.label_ayuda.config(text="El monto se autocompleta con el total y no se puede "
                                          "editar. No hay cambio.")
        else:
            self.entry_monto.config(state="normal")
            self.entry_monto.delete(0, tk.END)
            self.label_ayuda.config(text="Ej: 10000, 10.000 ó 10.000,50")
            self.entry_monto.focus_set()

    def _actualizar_cantidad(self, _evento=None):
        seleccion = self.tabla_productos.selection()
        if len(seleccion) == 1:
            cantidad = self.lineas[int(seleccion[0])]["cantidad"]
            self.spin_cantidad.delete(0, tk.END)
            self.spin_cantidad.insert(0, str(cantidad))
        self._actualizar_total_seleccion()

    def _actualizar_total_seleccion(self):
        seleccion = self.tabla_productos.selection()
        if not seleccion:
            return
        total = 0
        for iid in seleccion:
            linea = self.lineas[int(iid)]
            cantidad = linea["cantidad"]
            if len(seleccion) == 1:
                try:
                    cantidad = int(self.spin_cantidad.get())
                except ValueError:
                    cantidad = 0
            total += linea["precioUnitario"] * cantidad
        self.label_total.config(text=formatear_monto(total))

    def _selecciones(self):
        seleccion = self.tabla_productos.selection()
        if not seleccion:
            raise ValueError("Selecciona al menos un producto para cobrar.")
        if len(seleccion) > 1:
            return [(int(iid), self.lineas[int(iid)]["cantidad"]) for iid in seleccion]
        indice = int(seleccion[0])
        try:
            cantidad = int(self.spin_cantidad.get())
        except ValueError as error:
            raise ValueError("La cantidad seleccionada no es válida.") from error
        return [(indice, cantidad)]

    def _confirmar(self):
        if self._cobrado:
            return

        metodo = self.metodo.get()
        monto_texto = str(self.total) if metodo == "transferencia" else self.entry_monto.get()

        try:
            resultado = self.app.controller.cobrar_seleccion_mesa(
                self.nombre_mesa, self._selecciones(), metodo, monto_texto)
        except Exception as e:
            self.label_error.config(text=str(e))
            self.label_resultado.config(text="")
            return

        self._cobrado = True
        self.label_error.config(text="")
        if metodo == "efectivo":
            self.label_resultado.config(
                text=f"✓ Pago confirmado.\nCambio a entregar: "
                     f"{formatear_monto(resultado['cambio'])}")
        else:
            self.label_resultado.config(text="✓ Pago por transferencia confirmado.")

        self.entry_monto.config(state="disabled")
        self.radio_efectivo.config(state="disabled")
        self.radio_transferencia.config(state="disabled")
        self.boton_confirmar.config(state="disabled", bg="#a9c9aa")
        self.boton_cancelar.config(text="Cerrar")

        if self.al_confirmar:
            self.al_confirmar()

    def _cerrar(self):
        self.destroy()
