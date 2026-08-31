"""
inventario_view.py
=====================
Pantalla de gestión de inventario (módulo 2.2): listar, agregar,
modificar, eliminar y filtrar productos por categoría.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from core.money import formatear_monto

from .estilos import (COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ERROR, COLOR_FONDO,
                       COLOR_TEXTO_SUAVE, crear_barra_superior)


class InventarioView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_FONDO)
        self.app = app

        crear_barra_superior(self, app, "📦  Inventario")

        contenido = tk.Frame(self, bg=COLOR_FONDO)
        contenido.pack(fill="both", expand=True, padx=24, pady=16)

        superior = tk.Frame(contenido, bg=COLOR_FONDO)
        superior.pack(fill="x", pady=(0, 10))

        tk.Label(superior, text="Categoría:", font=("Segoe UI", 10), bg=COLOR_FONDO).pack(
            side="left")
        self.filtro = ttk.Combobox(superior, values=["Todas", "Bebida", "Comida", "Restaurante"],
                                    state="readonly", width=18, font=("Segoe UI", 10))
        self.filtro.current(0)
        self.filtro.pack(side="left", padx=(6, 20))
        self.filtro.bind("<<ComboboxSelected>>", lambda e: self._refrescar())

        tk.Label(superior, text="Buscar:", font=("Segoe UI", 10), bg=COLOR_FONDO).pack(side="left")
        self.entry_busqueda = ttk.Entry(superior, width=22, font=("Segoe UI", 10))
        self.entry_busqueda.pack(side="left", padx=(6, 20))
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self._refrescar())

        tk.Button(
            superior, text="+ Agregar producto", font=("Segoe UI", 9, "bold"), bg=COLOR_ACENTO,
            fg="white", bd=0, cursor="hand2", padx=10, pady=5,
            activebackground=COLOR_ACENTO_HOVER, activeforeground="white",
            command=self._abrir_agregar,
        ).pack(side="right")

        columnas = ("id", "nombre", "categoria", "precio")
        self.tabla = ttk.Treeview(contenido, columns=columnas, show="headings", height=16)
        for col, texto, ancho in (("id", "ID", 60), ("nombre", "Nombre", 280),
                                   ("categoria", "Categoría", 130), ("precio", "Precio", 140)):
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="w" if col == "nombre" else "center")
        self.tabla.pack(fill="both", expand=True)
        self.tabla.bind("<Double-1>", lambda e: self._abrir_modificar())

        pie = tk.Frame(contenido, bg=COLOR_FONDO)
        pie.pack(fill="x", pady=(10, 0))
        tk.Button(pie, text="Modificar", font=("Segoe UI", 9), bg="white", bd=1,
                  relief="solid", cursor="hand2", padx=14, pady=5,
                  command=self._abrir_modificar).pack(side="left")
        tk.Button(pie, text="Eliminar", font=("Segoe UI", 9), bg="white", bd=1, relief="solid",
                  cursor="hand2", padx=14, pady=5, fg=COLOR_ERROR,
                  command=self._eliminar).pack(side="left", padx=8)
        self.label_contador = tk.Label(pie, text="", font=("Segoe UI", 9), bg=COLOR_FONDO,
                                        fg=COLOR_TEXTO_SUAVE)
        self.label_contador.pack(side="right")

    def al_mostrar(self):
        self._refrescar()

    def _refrescar(self):
        categoria = self.filtro.get()
        texto_busqueda = self.entry_busqueda.get()
        seleccion_previa = self.tabla.selection()

        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        productos = self.app.controller.buscar_productos(texto_busqueda, categoria)
        for prod in productos:
            self.tabla.insert("", "end", iid=str(prod["id"]),
                               values=(prod["id"], prod["nombre"], prod["categoria"],
                                       formatear_monto(prod["precio"])))

        if seleccion_previa and self.tabla.exists(seleccion_previa[0]):
            self.tabla.selection_set(seleccion_previa[0])

        self.label_contador.config(text=f"{len(productos)} producto(s)")

    def _seleccion_id(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Selecciona un producto",
                                 "Primero selecciona un producto de la lista.")
            return None
        return int(seleccion[0])

    def _abrir_agregar(self):
        DialogoProducto(self, self.app, modo="agregar")

    def _abrir_modificar(self):
        id_producto = self._seleccion_id()
        if id_producto is None:
            return
        producto = self.app.controller.inventario.obtener(id_producto)
        DialogoProducto(self, self.app, modo="modificar", producto=producto)

    def _eliminar(self):
        id_producto = self._seleccion_id()
        if id_producto is None:
            return
        producto = self.app.controller.inventario.obtener(id_producto)
        if not messagebox.askyesno("Confirmar eliminación",
                                    f"¿Eliminar '{producto['nombre']}' del inventario?\n\n"
                                    "Esto no afecta pedidos ya existentes en las mesas."):
            return
        try:
            self.app.controller.eliminar_producto(id_producto)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        self._refrescar()


class DialogoProducto(tk.Toplevel):
    """Ventana modal para agregar o modificar un producto del inventario."""

    def __init__(self, vista_padre, app, modo, producto=None):
        super().__init__(vista_padre)
        self.vista_padre = vista_padre
        self.app = app
        self.modo = modo
        self.producto = producto

        titulo = "Agregar producto" if modo == "agregar" else "Modificar producto"
        self.title(titulo)
        self.configure(bg="white")
        self.geometry("360x350")
        self.resizable(False, False)
        self.transient(vista_padre.winfo_toplevel())
        self.grab_set()

        tk.Label(self, text=titulo, font=("Segoe UI", 13, "bold"), bg="white",
                 fg=COLOR_ACENTO).pack(pady=(18, 14))

        tk.Label(self, text="Nombre", font=("Segoe UI", 9), bg="white").pack(anchor="w", padx=30)
        self.entry_nombre = ttk.Entry(self, font=("Segoe UI", 10))
        self.entry_nombre.pack(fill="x", padx=30, pady=(2, 10))

        tk.Label(self, text="Categoría", font=("Segoe UI", 9), bg="white").pack(anchor="w",
                                                                                 padx=30)
        self.combo_categoria = ttk.Combobox(self, values=["Bebida", "Comida", "Restaurante"], state="readonly",
                                             font=("Segoe UI", 10))
        self.combo_categoria.pack(fill="x", padx=30, pady=(2, 10))

        tk.Label(self, text="Precio (COP)", font=("Segoe UI", 9), bg="white").pack(anchor="w",
                                                                                    padx=30)
        self.entry_precio = ttk.Entry(self, font=("Segoe UI", 10))
        self.entry_precio.pack(fill="x", padx=30, pady=(2, 4))
        tk.Label(self, text="Ej: 10000, 10.000 ó 10.000,50", font=("Segoe UI", 8), bg="white",
                 fg=COLOR_TEXTO_SUAVE).pack(anchor="w", padx=30)

        self.label_error = tk.Label(self, text="", font=("Segoe UI", 9), bg="white",
                                     fg=COLOR_ERROR, wraplength=300, justify="left")
        self.label_error.pack(pady=(8, 4), padx=30, anchor="w")

        if producto:
            self.entry_nombre.insert(0, producto["nombre"])
            self.combo_categoria.set(producto["categoria"])
            self.entry_precio.insert(0, str(producto["precio"]))
        else:
            self.combo_categoria.current(0)

        self.entry_nombre.focus_set()

        botones = tk.Frame(self, bg="white")
        botones.pack(fill="x", padx=30, pady=(10, 20), side="bottom")
        tk.Button(botones, text="Cancelar", font=("Segoe UI", 9), bg="white", bd=1,
                  relief="solid", cursor="hand2", command=self.destroy).pack(
            side="left", expand=True, fill="x", padx=(0, 6), ipady=5)
        tk.Button(botones, text="Guardar", font=("Segoe UI", 9, "bold"), bg=COLOR_ACENTO,
                  fg="white", bd=0, cursor="hand2", command=self._guardar).pack(
            side="left", expand=True, fill="x", padx=(6, 0), ipady=5)

    def _guardar(self):
        nombre = self.entry_nombre.get().strip()
        categoria = self.combo_categoria.get()
        precio_texto = self.entry_precio.get().strip()

        if not nombre:
            self.label_error.config(text="El nombre no puede estar vacío.")
            return
        if categoria not in ("Bebida", "Comida", "Restaurante"):
            self.label_error.config(text="Selecciona una categoría.")
            return

        try:
            if self.modo == "agregar":
                self.app.controller.agregar_producto(nombre, categoria, precio_texto)
            else:
                self.app.controller.modificar_producto(self.producto["id"], nombre, categoria,
                                                         precio_texto)
        except ValueError as e:
            self.label_error.config(text=str(e))
            return

        self.vista_padre._refrescar()
        self.destroy()
