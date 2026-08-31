"""
ventas_view.py
================
Pantalla de ventas (módulo 2.3): selección de mesa (1 a 5), añadir
productos desde el inventario, modificar/eliminar líneas del pedido y
enviar la mesa a cobro.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from core.money import formatear_monto

from .cobro_dialog import DialogoCobro
from .estilos import (COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ERROR, COLOR_EXITO,
                       COLOR_EXITO_HOVER, COLOR_FONDO, COLOR_TEXTO, crear_barra_superior)


class VentasView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_FONDO)
        self.app = app

        crear_barra_superior(self, app, "🧾  Ventas")

        barra_acciones = tk.Frame(self, bg=COLOR_FONDO)
        barra_acciones.pack(fill="x", padx=16, pady=(10, 0))
        tk.Button(
            barra_acciones, text="+ Añadir mesa", font=("Segoe UI", 9, "bold"),
            bg=COLOR_ACENTO, fg="white", bd=0, cursor="hand2", padx=10, pady=5,
            activebackground=COLOR_ACENTO_HOVER, activeforeground="white",
            command=self._agregar_mesa,
        ).pack(side="right")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=14)
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self._refrescar_actual())

        self.paneles = {}
        self._crear_pestanas()

    def _crear_pestanas(self):
        self.paneles = {}
        for nombre_mesa in self.app.controller.nombres_mesas():
            panel = PanelMesa(self.notebook, self.app, nombre_mesa)
            self.notebook.add(panel, text=nombre_mesa.replace("mesa", "Mesa "))
            self.paneles[nombre_mesa] = panel

    def _agregar_mesa(self):
        nombre = self.app.controller.agregar_mesa()
        for panel in self.paneles.values():
            panel.destroy()
        for pestaña in self.notebook.tabs():
            self.notebook.forget(pestaña)
        self._crear_pestanas()
        self.notebook.select(self.paneles[nombre])

    def al_mostrar(self):
        self._refrescar_actual()

    def _refrescar_actual(self):
        seleccion = self.notebook.select()
        if not seleccion:
            return
        indice = self.notebook.index(seleccion)
        nombre_mesa = self.app.controller.nombres_mesas()[indice]
        self.paneles[nombre_mesa].refrescar()


class PanelMesa(tk.Frame):
    def __init__(self, parent, app, nombre_mesa):
        super().__init__(parent, bg="white")
        self.app = app
        self.nombre_mesa = nombre_mesa

        contenedor = tk.Frame(self, bg="white")
        contenedor.pack(fill="both", expand=True, padx=14, pady=14)
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_columnconfigure(1, weight=1)
        contenedor.grid_rowconfigure(0, weight=1)

        # ---------------- Panel izquierdo: inventario disponible ----------------
        izquierdo = tk.Frame(contenedor, bg="white")
        izquierdo.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        fila_filtro = tk.Frame(izquierdo, bg="white")
        fila_filtro.pack(fill="x", pady=(0, 6))
        tk.Label(fila_filtro, text="Productos disponibles", font=("Segoe UI", 10, "bold"),
                 bg="white", fg=COLOR_ACENTO).pack(side="left")
        self.filtro = ttk.Combobox(fila_filtro, values=["Todas", "Bebida", "Comida", "Restaurante"],
                                    state="readonly", width=12, font=("Segoe UI", 9))
        self.filtro.current(0)
        self.filtro.pack(side="right")
        self.filtro.bind("<<ComboboxSelected>>", lambda e: self._refrescar_inventario())

        self.entry_busqueda = ttk.Entry(fila_filtro, width=18, font=("Segoe UI", 9))
        self.entry_busqueda.pack(side="left", padx=(0, 8))
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self._refrescar_inventario())

        self.tabla_inventario = ttk.Treeview(izquierdo, columns=("nombre", "precio"),
                                              show="headings", height=14)
        self.tabla_inventario.heading("nombre", text="Producto")
        self.tabla_inventario.heading("precio", text="Precio")
        self.tabla_inventario.column("nombre", width=190)
        self.tabla_inventario.column("precio", width=90, anchor="center")
        self.tabla_inventario.pack(fill="both", expand=True)
        self.tabla_inventario.bind("<Double-1>", lambda e: self._agregar_producto())

        fila_agregar = tk.Frame(izquierdo, bg="white")
        fila_agregar.pack(fill="x", pady=(8, 0))
        tk.Label(fila_agregar, text="Cantidad:", font=("Segoe UI", 9), bg="white").pack(
            side="left")
        self.spin_cantidad = tk.Spinbox(fila_agregar, from_=1, to=99, width=4,
                                         font=("Segoe UI", 9))
        self.spin_cantidad.pack(side="left", padx=6)
        tk.Button(
            fila_agregar, text="Añadir a la mesa →", font=("Segoe UI", 9, "bold"),
            bg=COLOR_ACENTO, fg="white", bd=0, cursor="hand2", padx=10, pady=4,
            activebackground=COLOR_ACENTO_HOVER, activeforeground="white",
            command=self._agregar_producto,
        ).pack(side="right")

        # ---------------- Panel derecho: pedido de la mesa ----------------
        derecho = tk.Frame(contenedor, bg="white")
        derecho.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Label(derecho, text=f"Pedido — {nombre_mesa.replace('mesa', 'Mesa ')}",
                 font=("Segoe UI", 10, "bold"), bg="white", fg=COLOR_ACENTO).pack(
            anchor="w", pady=(0, 6))

        columnas = ("nombre", "cantidad", "precio", "subtotal")
        self.tabla_pedido = ttk.Treeview(derecho, columns=columnas, show="headings", height=12)
        for col, texto, ancho in (("nombre", "Producto", 150), ("cantidad", "Cant.", 50),
                                   ("precio", "P. Unit.", 90), ("subtotal", "Subtotal", 90)):
            self.tabla_pedido.heading(col, text=texto)
            self.tabla_pedido.column(col, width=ancho,
                                      anchor="center" if col != "nombre" else "w")
        self.tabla_pedido.pack(fill="both", expand=True)

        fila_botones = tk.Frame(derecho, bg="white")
        fila_botones.pack(fill="x", pady=(8, 0))
        tk.Button(fila_botones, text="+1", font=("Segoe UI", 9), bg="white", bd=1,
                  relief="solid", cursor="hand2", width=3,
                  command=lambda: self._ajustar_cantidad(1)).pack(side="left")
        tk.Button(fila_botones, text="-1", font=("Segoe UI", 9), bg="white", bd=1,
                  relief="solid", cursor="hand2", width=3,
                  command=lambda: self._ajustar_cantidad(-1)).pack(side="left", padx=6)
        tk.Button(fila_botones, text="Eliminar línea", font=("Segoe UI", 9), bg="white", bd=1,
                  relief="solid", cursor="hand2", fg=COLOR_ERROR,
                  command=self._eliminar_linea).pack(side="left", padx=6)

        pie = tk.Frame(derecho, bg="white")
        pie.pack(fill="x", pady=(14, 0))
        self.label_total = tk.Label(pie, text="Total: $0", font=("Segoe UI", 14, "bold"),
                                     bg="white", fg=COLOR_TEXTO)
        self.label_total.pack(side="left")
        tk.Button(
            pie, text="Cobrar mesa", font=("Segoe UI", 10, "bold"), bg=COLOR_EXITO, fg="white",
            bd=0, cursor="hand2", padx=16, pady=8, activebackground=COLOR_EXITO_HOVER,
            activeforeground="white", command=self._cobrar,
        ).pack(side="right")

        self._refrescar_inventario()
        self._refrescar_pedido()

    def refrescar(self):
        self._refrescar_inventario()
        self._refrescar_pedido()

    def _refrescar_inventario(self):
        categoria = self.filtro.get()
        texto_busqueda = self.entry_busqueda.get()
        seleccion_previa = self.tabla_inventario.selection()

        for fila in self.tabla_inventario.get_children():
            self.tabla_inventario.delete(fila)
        for prod in self.app.controller.buscar_productos(texto_busqueda, categoria):
            self.tabla_inventario.insert("", "end", iid=str(prod["id"]),
                                          values=(prod["nombre"], formatear_monto(prod["precio"])))

        if seleccion_previa and self.tabla_inventario.exists(seleccion_previa[0]):
            self.tabla_inventario.selection_set(seleccion_previa[0])

    def _refrescar_pedido(self):
        for fila in self.tabla_pedido.get_children():
            self.tabla_pedido.delete(fila)
        lineas = self.app.controller.lineas_mesa(self.nombre_mesa)
        for indice, linea in enumerate(lineas):
            self.tabla_pedido.insert("", "end", iid=str(indice),
                                      values=(linea["nombre"], linea["cantidad"],
                                              formatear_monto(linea["precioUnitario"]),
                                              formatear_monto(linea["subtotal"])))
        total = self.app.controller.total_mesa(self.nombre_mesa)
        self.label_total.config(text=f"Total: {formatear_monto(total)}")

    def _producto_seleccionado(self):
        seleccion = self.tabla_inventario.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona un producto",
                                 "Elige un producto de la lista de la izquierda.")
            return None
        return int(seleccion[0])

    def _agregar_producto(self):
        id_producto = self._producto_seleccionado()
        if id_producto is None:
            return
        try:
            cantidad = int(self.spin_cantidad.get())
        except ValueError:
            cantidad = 1

        try:
            self.app.controller.agregar_a_mesa(self.nombre_mesa, id_producto, cantidad)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        self._refrescar_pedido()

    def _linea_seleccionada(self):
        seleccion = self.tabla_pedido.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona un producto",
                                 "Elige una línea del pedido de la mesa.")
            return None
        return int(seleccion[0])

    def _ajustar_cantidad(self, delta):
        indice = self._linea_seleccionada()
        if indice is None:
            return
        lineas = self.app.controller.lineas_mesa(self.nombre_mesa)
        nueva_cantidad = lineas[indice]["cantidad"] + delta
        try:
            if nueva_cantidad <= 0:
                self.app.controller.eliminar_de_mesa(self.nombre_mesa, indice)
            else:
                self.app.controller.modificar_cantidad_mesa(self.nombre_mesa, indice,
                                                              nueva_cantidad)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        self._refrescar_pedido()

    def _eliminar_linea(self):
        indice = self._linea_seleccionada()
        if indice is None:
            return
        try:
            self.app.controller.eliminar_de_mesa(self.nombre_mesa, indice)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        self._refrescar_pedido()

    def _cobrar(self):
        try:
            info = self.app.controller.preparar_cobro(self.nombre_mesa)
        except Exception as e:
            messagebox.showinfo("Mesa vacía", str(e))
            return
        DialogoCobro(self, self.app, self.nombre_mesa, info["total"], info["lineas"],
                     al_confirmar=self._despues_de_cobrar)

    def _despues_de_cobrar(self):
        self._refrescar_pedido()
        self._refrescar_inventario()
