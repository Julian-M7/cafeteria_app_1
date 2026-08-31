"""
principal_view.py
===================
Panel principal con navegación a Inventario, Ventas y Cierre, tal como
lo pide el enunciado ("Después del login, ir al panel principal con
navegación a Inventario, Ventas y Cierre").
"""

import tkinter as tk

from .estilos import (COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_BARRA, COLOR_BORDE,
                       COLOR_FONDO, COLOR_TEXTO, COLOR_TEXTO_SUAVE)


class PrincipalView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_FONDO)
        self.app = app

        barra = tk.Frame(self, bg=COLOR_BARRA, height=56)
        barra.pack(fill="x", side="top")
        barra.pack_propagate(False)
        tk.Label(barra, text="☕  Cafetería — Panel principal", font=("Segoe UI", 13, "bold"),
                 bg=COLOR_BARRA, fg="white").pack(side="left", padx=20)
        tk.Button(
            barra, text="Cerrar sesión", font=("Segoe UI", 9), bg=COLOR_BARRA, fg="white",
            activebackground=COLOR_ACENTO_HOVER, activeforeground="white", bd=0,
            cursor="hand2", command=self.app.cerrar_sesion,
        ).pack(side="right", padx=20)

        cuerpo = tk.Frame(self, bg=COLOR_FONDO)
        cuerpo.place(relx=0.5, rely=0.52, anchor="center")

        tk.Label(cuerpo, text="¿Qué deseas hacer?", font=("Segoe UI", 15, "bold"),
                 bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=(0, 24))

        fila = tk.Frame(cuerpo, bg=COLOR_FONDO)
        fila.pack()

        self._tarjeta(fila, "📦", "Inventario", "Gestiona productos y precios",
                      lambda: self.app.mostrar("InventarioView")).grid(row=0, column=0, padx=14)
        self._tarjeta(fila, "🧾", "Ventas", "Atiende las 5 mesas",
                      lambda: self.app.mostrar("VentasView")).grid(row=0, column=1, padx=14)
        self._tarjeta(fila, "📊", "Cierre", "Consulta ventas y totales",
                      lambda: self.app.mostrar("CierreView")).grid(row=0, column=2, padx=14)

    def _tarjeta(self, parent, icono, titulo, descripcion, comando):
        marco = tk.Frame(parent, bg="white", width=220, height=170,
                          highlightbackground=COLOR_BORDE, highlightthickness=1,
                          cursor="hand2")
        marco.pack_propagate(False)
        tk.Label(marco, text=icono, font=("Segoe UI", 30), bg="white").pack(pady=(24, 6))
        tk.Label(marco, text=titulo, font=("Segoe UI", 13, "bold"), bg="white",
                 fg=COLOR_ACENTO).pack()
        tk.Label(marco, text=descripcion, font=("Segoe UI", 9), bg="white",
                 fg=COLOR_TEXTO_SUAVE, wraplength=170, justify="center").pack(pady=(4, 0))

        def entrar(_event=None):
            comando()

        marco.bind("<Button-1>", entrar)
        for widget in marco.winfo_children():
            widget.bind("<Button-1>", entrar)
        return marco

    def al_mostrar(self):
        pass
