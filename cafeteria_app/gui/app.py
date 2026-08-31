"""
app.py
=======
Ventana raíz de la aplicación. Crea el controlador de negocio
(AppController) UNA sola vez, y administra la navegación entre las 5
pantallas (Login, Panel principal, Inventario, Ventas, Cierre)
mostrando/ocultando frames superpuestos sobre un mismo contenedor
(patrón estándar de Tkinter para apps multi-pantalla).
"""

import tkinter as tk
from tkinter import ttk

from core.controller import AppController

from .cierre_view import CierreView
from .estilos import COLOR_FONDO
from .inventario_view import InventarioView
from .login_view import LoginView
from .principal_view import PrincipalView
from .ventas_view import VentasView


class CafeteriaApp(tk.Tk):
    """Ventana principal. Administra el controlador de negocio y el
    cambio entre las distintas pantallas (frames) de la aplicación."""

    def __init__(self):
        super().__init__()
        self.title("Cafetería — Sistema de Ventas")
        self.geometry("1050x700")
        self.minsize(950, 620)
        self.configure(bg=COLOR_FONDO)

        self.controller = AppController()
        self._configurar_estilos()

        contenedor = tk.Frame(self, bg=COLOR_FONDO)
        contenedor.pack(fill="both", expand=True)
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        self._frames = {}
        for Clase in (LoginView, PrincipalView, InventarioView, VentasView, CierreView):
            frame = Clase(contenedor, self)
            self._frames[Clase.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.mostrar("LoginView")

    def _configurar_estilos(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("Treeview", font=("Segoe UI", 10), rowheight=26, background="white",
                          fieldbackground="white")
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        estilo.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=(16, 8))

    def mostrar(self, nombre_frame):
        """Cambia la pantalla visible. Si el frame define `al_mostrar`,
        se llama primero para refrescar sus datos desde el controlador."""
        frame = self._frames[nombre_frame]
        if hasattr(frame, "al_mostrar"):
            frame.al_mostrar()
        frame.tkraise()

    def cerrar_sesion(self):
        self.controller.autenticado = False
        self.mostrar("LoginView")


def iniciar_aplicacion():
    app = CafeteriaApp()
    app.mainloop()
